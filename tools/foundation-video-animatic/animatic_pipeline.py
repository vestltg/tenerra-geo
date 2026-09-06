#!/usr/bin/env python3
"""
Reusable primitives for building an ANYA/Tenerra placeholder animatic:
Pillow frame rendering + espeak-ng narration + ffmpeg assembly.

This module does the mechanical, repetitive part (TTS synthesis, exact
beat-duration timing, watermarking, disclosure bars, ffmpeg concatenation)
so a new video only requires writing the BEATS list and per-beat visual
functions — not re-deriving the pipeline. See SKILL.md for the workflow
this fits into and why an animatic looks the way it does.

Typical use: copy this file next to a new `generate_video.py`, define
BEATS (see the bottom of this file for the shape), write one frame
function per beat using the helpers below, then call `build(beats, out_path)`.
"""
import os
import re
import subprocess
import wave
import contextlib
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30

FONT_DIR = "/usr/share/fonts/truetype"
SERIF = os.path.join(FONT_DIR, "liberation/LiberationSerif-Regular.ttf")
SERIF_BOLD = os.path.join(FONT_DIR, "liberation/LiberationSerif-Bold.ttf")
SERIF_ITALIC = os.path.join(FONT_DIR, "liberation/LiberationSerif-Italic.ttf")
SANS = os.path.join(FONT_DIR, "dejavu/DejaVuSans.ttf")
SANS_BOLD = os.path.join(FONT_DIR, "dejavu/DejaVuSans-Bold.ttf")

# Fallback palette if the site's own colors can't be read (see load_palette).
DEFAULT_PALETTE = {
    "ink": (13, 13, 13),
    "cream": (245, 243, 238),
    "cream_dim": (237, 233, 225),
    "accent": (130, 86, 247),
    "muted": (152, 152, 152),
    "warn": (200, 70, 60),
}


def load_palette(html_path, fallback=None):
    """Pull the site's real hex colors out of its HTML/CSS instead of
    guessing a brand palette from scratch. Returns the fallback dict if the
    file is missing or nothing is found — always check the result looks
    sane before rendering a full video with it."""
    fallback = fallback or DEFAULT_PALETTE
    if not html_path or not os.path.exists(html_path):
        return dict(fallback)
    with open(html_path, "r", errors="ignore") as f:
        text = f.read()
    hexes = re.findall(r"#[0-9a-fA-F]{6}\b", text)
    if not hexes:
        return dict(fallback)
    from collections import Counter
    counts = Counter(hexes)
    ordered = [h for h, _ in counts.most_common()]

    def to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def brightness(rgb):
        return sum(rgb) / 3

    rgbs = sorted(set(to_rgb(h) for h in ordered), key=brightness, reverse=True)
    lightest = rgbs[0]
    darkest = min(rgbs, key=brightness)
    mids = [c for c in rgbs if c not in (darkest, lightest)]
    accent = max(mids, key=lambda c: max(c) - min(c)) if mids else lightest

    # cream_dim needs to be genuinely distinct from cream (for gradients),
    # but still a light/neutral tone, not just "the next color found" —
    # otherwise a gradient built from it can shift hue instead of just
    # value. Prefer a real near-white second tone from the site; if none
    # exists, synthesize one by darkening cream slightly rather than
    # reusing cream itself, which would make any gradient built from it a
    # no-op flat fill.
    cream_dim = None
    for c in rgbs[1:]:
        if brightness(lightest) - brightness(c) <= 40 and brightness(c) > 150:
            cream_dim = c
            break
    if cream_dim is None:
        cream_dim = tuple(max(v - 18, 0) for v in lightest)

    return {
        "ink": darkest,
        "cream": lightest,
        "cream_dim": cream_dim,
        "accent": accent,
        "muted": (152, 152, 152),
        "warn": (200, 70, 60),
    }


def font(path, size):
    return ImageFont.truetype(path, size)


def gradient_background(color_top, color_bottom, w=W, h=H):
    """A vertical gradient card, not a flat fill. A single flat color —
    especially something near-white like a cream brand tone — reads as a
    blank/broken screen once it's held for 10-20 seconds, even though the
    same color works fine as a text background in print or on a web page
    you can scroll past. Default to this for any full-bleed light or dark
    card; reserve a flat fill for small elements (cards, bars), not full
    frames."""
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        rgb = tuple(int(color_top[i] + (color_bottom[i] - color_top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=rgb)
    return img


def accent_rule(draw, cx, cy, width=120, thickness=4, color=None, palette=None):
    """A short accent-colored rule — a small, deliberate mark that reads as
    a design choice rather than an empty frame. Use sparingly (one per
    card) near a quote, headline, or URL; it should not compete with the
    text it sits next to."""
    color = color or (palette or DEFAULT_PALETTE)["accent"]
    draw.rectangle([cx - width / 2, cy - thickness / 2, cx + width / 2, cy + thickness / 2], fill=color)


def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def watermark(draw, text="PLACEHOLDER ANIMATIC — SYNTHETIC VOICE, MOCKUP VISUALS, NOT FOR PUBLICATION"):
    """Burn a visible flag onto every frame. This is not decoration — an
    animatic that looks clean enough to pass for final defeats the point
    of it being an internal timing tool. Keep this on every frame, always."""
    f = font(SANS, 20)
    w = draw.textlength(text, font=f)
    draw.text((W - w - 24, 20), text, font=f, fill=(255, 120, 110))


def disclosure_bar(draw, text):
    """Lower-third bar for beats showing a demo/sample account, matching
    the standing disclosure treatment used across ANYA cluster videos."""
    bar_h = 64
    draw.rectangle([0, H - bar_h, W, H], fill=(0, 0, 0))
    f = font(SANS, 26)
    w = draw.textlength(text, font=f)
    draw.text(((W - w) / 2, H - bar_h + (bar_h - 30) / 2), text, font=f, fill=(255, 255, 255))


def pending_tag(draw, text, cx, cy, color=(200, 70, 60), size=28, bold=True):
    """Render an unresolved script item (missing exchange, unconfirmed URL,
    etc.) visibly on the frame. Never invent plausible-sounding content to
    fill a gap the script itself flags as open — surfacing the gap is the
    correct behavior, not a defect to paper over."""
    f = font(SANS_BOLD if bold else SANS, size)
    w = draw.textlength(text, font=f)
    draw.text((cx - w / 2, cy), text, font=f, fill=color)


def wav_duration(path):
    with contextlib.closing(wave.open(path, "r")) as f:
        return f.getnframes() / float(f.getframerate())


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def synth_beat_audio(vo_text, duration, out_path, raw_path):
    """Render one beat's narration with espeak-ng, padded/trimmed to the
    beat's exact duration. `vo_text=None` produces silence (for silent
    beats like a cold-open quote card)."""
    if not vo_text:
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-t", str(duration), out_path])
        return
    run(["espeak-ng", "-v", "en-us", "-s", "150", "-p", "35", "-a", "170",
         "-w", raw_path, vo_text])
    speech_dur = wav_duration(raw_path)
    if speech_dur > duration:
        print(f"WARNING: narration ({speech_dur:.1f}s) exceeds beat duration "
              f"({duration}s) — it will be cut off. Shorten the VO line or "
              f"extend the beat.")
    pad = max(duration - speech_dur, 0)
    lead = 0.4
    run(["ffmpeg", "-y", "-i", raw_path,
         "-af", f"adelay={int(lead*1000)}|{int(lead*1000)},apad=pad_dur={pad}",
         "-t", str(duration), "-ar", "44100", "-ac", "1", out_path])


def build(beats, out_path, build_dir=None):
    """Assemble a list of beats into one MP4.

    Each beat is a dict: {"n": int, "start": seconds, "end": seconds,
    "frame": callable() -> PIL.Image, "vo": str or None}.

    Beat timestamps should come straight from the storyboard/cue sheet —
    don't round or adjust them; the whole point of an animatic is to check
    the real pacing.
    """
    build_dir = build_dir or os.path.join(os.path.dirname(os.path.abspath(out_path)), "build")
    frames_dir = os.path.join(build_dir, "frames")
    audio_dir = os.path.join(build_dir, "audio")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    concat_list = os.path.join(build_dir, "concat.txt")
    audio_parts = []
    with open(concat_list, "w") as f:
        for beat in beats:
            dur = beat["end"] - beat["start"]
            frame_path = os.path.join(frames_dir, f"beat{beat['n']}.png")
            beat["frame"]().save(frame_path)
            seg_path = os.path.join(frames_dir, f"beat{beat['n']}_seg.mp4")
            run(["ffmpeg", "-y", "-loop", "1", "-i", frame_path, "-t", str(dur),
                 "-r", str(FPS), "-pix_fmt", "yuv420p", "-vf", f"scale={W}:{H}",
                 seg_path])
            f.write(f"file '{seg_path}'\n")

            audio_out = os.path.join(audio_dir, f"beat{beat['n']}.wav")
            audio_raw = os.path.join(audio_dir, f"beat{beat['n']}_raw.wav")
            synth_beat_audio(beat.get("vo"), dur, audio_out, audio_raw)
            audio_parts.append(audio_out)

    video_concat = os.path.join(build_dir, "video_concat.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c", "copy", video_concat])

    narration = os.path.join(build_dir, "narration.wav")
    audio_concat_list = os.path.join(build_dir, "audio_concat.txt")
    with open(audio_concat_list, "w") as f:
        for p in audio_parts:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", audio_concat_list,
         "-ar", "44100", "-ac", "1", narration])

    run(["ffmpeg", "-y", "-i", video_concat, "-i", narration,
         "-c:v", "libx264", "-c:a", "aac", "-shortest", out_path])
    print(f"Wrote {out_path}")
    return out_path


def verify(out_path, sample_times_sec):
    """Extract one JPEG per given timestamp so you can actually look at
    each beat before delivering. ffprobe confirms duration/codecs; the
    extracted frames are what catch a wrong color, missing watermark, or
    illegible text — read them with the Read tool before sending the video
    anywhere. Don't rely on soffice/LibreOffice for this kind of check;
    it's frequently broken or unavailable in these environments."""
    out_dir = os.path.join(os.path.dirname(os.path.abspath(out_path)), "verify_frames")
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for t in sample_times_sec:
        p = os.path.join(out_dir, f"frame_{t}s.jpg")
        run(["ffmpeg", "-y", "-ss", str(t), "-i", out_path, "-frames:v", "1", p])
        paths.append(p)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-show_entries", "stream=codec_type,codec_name,width,height",
         "-of", "default=noprint_wrappers=0", out_path],
        stdout=subprocess.PIPE, text=True,
    )
    print(probe.stdout)
    return paths
