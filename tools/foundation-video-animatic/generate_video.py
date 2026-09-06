#!/usr/bin/env python3
"""
ANYA Foundation Video — animatic generator.

Renders a placeholder/animatic cut of the Foundation Video script: mockup
visuals (Pillow) + synthetic TTS narration (espeak-ng) + assembly (ffmpeg).

THIS IS NOT THE FINAL ASSET. It exists to check pacing/timing against the
script. Two things make that explicit rather than incidental:
  - The narration is espeak-ng, deliberately left robotic. The storyboard
    is explicit that this video needs Michael's real recorded voice, not
    synthetic speech — using a voice good enough to be mistaken for final
    would misrepresent that requirement.
  - There is no real footage. Beats 2-4 are text/shape mockups standing in
    for the locked brand open and the Sample Mom capture/retrieval scenes.
Every frame is watermarked to say so.

Usage: python3 generate_video.py
Requires: ffmpeg, espeak-ng, Pillow (pip install Pillow)
"""
import os
import subprocess
import wave
import contextlib
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
FRAMES = os.path.join(BUILD, "frames")
AUDIO = os.path.join(BUILD, "audio")
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(AUDIO, exist_ok=True)

# Brand palette pulled from the live tenerra-geo site (index.html)
INK = (13, 13, 13)          # #0D0D0D
CREAM = (245, 243, 238)     # #F5F3EE
CREAM_DIM = (237, 233, 225) # #EDE9E1
ACCENT = (130, 86, 247)     # #8256F7
MUTED = (152, 152, 152)     # #989898
WARN = (200, 70, 60)

FONT_DIR = "/usr/share/fonts/truetype"
SERIF = os.path.join(FONT_DIR, "liberation/LiberationSerif-Regular.ttf")
SERIF_BOLD = os.path.join(FONT_DIR, "liberation/LiberationSerif-Bold.ttf")
SERIF_ITALIC = os.path.join(FONT_DIR, "liberation/LiberationSerif-Italic.ttf")
SANS = os.path.join(FONT_DIR, "dejavu/DejaVuSans.ttf")
SANS_BOLD = os.path.join(FONT_DIR, "dejavu/DejaVuSans-Bold.ttf")
LOGO_PATH = "/home/user/tenerra-geo/assets/images/tenerra-logo.png"


def font(path, size):
    return ImageFont.truetype(path, size)


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


def draw_centered_lines(draw, lines, fnt, cy, fill, line_gap=1.3, anchor_cx=None):
    anchor_cx = anchor_cx or (W // 2)
    heights = [fnt.getbbox(l)[3] - fnt.getbbox(l)[1] for l in lines]
    line_h = fnt.size * line_gap
    total_h = line_h * len(lines)
    y = cy - total_h / 2
    for line in lines:
        w = draw.textlength(line, font=fnt)
        draw.text((anchor_cx - w / 2, y), line, font=fnt, fill=fill)
        y += line_h


def watermark(draw, text="PLACEHOLDER ANIMATIC — SYNTHETIC VOICE, MOCKUP VISUALS, NOT FOR PUBLICATION"):
    f = font(SANS, 20)
    w = draw.textlength(text, font=f)
    draw.text((W - w - 24, 20), text, font=f, fill=(255, 120, 110))


def disclosure_bar(img, draw, text="Demonstration using ANYA's Sample Family. Not a real user account."):
    bar_h = 64
    draw.rectangle([0, H - bar_h, W, H], fill=(0, 0, 0))
    f = font(SANS, 26)
    w = draw.textlength(text, font=f)
    draw.text(((W - w) / 2, H - bar_h + (bar_h - 30) / 2), text, font=f, fill=(255, 255, 255))


def beat1_frame():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    attrib_f = font(SERIF_ITALIC, 34)
    quote_f = font(SERIF, 52)
    lines = [
        "“It's so easy!”",
        "",
        "“Now I'm not the only one holding it.",
        "Anya is too.”",
    ]
    y = H / 2 - 40
    for line in lines:
        if line == "":
            y += 30
            continue
        w = d.textlength(line, font=quote_f)
        d.text(((W - w) / 2, y), line, font=quote_f, fill=INK)
        y += 70
    attrib = "— Kim B., parent of two adult children with autism  ·  July 2026"
    w = d.textlength(attrib, font=attrib_f)
    d.text(((W - w) / 2, y + 40), attrib, font=attrib_f, fill=(90, 90, 90))
    watermark(d)
    return img


def beat2_frame():
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        target = 260
        logo = logo.resize((target, target))
        img.paste(logo, ((W - target) // 2, (H - target) // 2 - 40), logo)
    except Exception:
        f = font(SANS_BOLD, 90)
        text = "ANYA"
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, H / 2 - 60), text, font=f, fill=CREAM)
    note_f = font(SANS, 24)
    note = "[ locked “Boxes → Vest” static open — placeholder card, real component not substituted ]"
    w = d.textlength(note, font=note_f)
    d.text(((W - w) / 2, H / 2 + 160), note, font=note_f, fill=MUTED)
    watermark(d)
    return img


def beat3_frame():
    img = Image.new("RGB", (W, H), (24, 24, 26))
    d = ImageDraw.Draw(img)
    # mock chat card
    card = [W / 2 - 560, H / 2 - 230, W / 2 + 560, H / 2 + 150]
    d.rounded_rectangle(card, radius=28, fill=(38, 38, 42), outline=ACCENT, width=3)
    body_f = font(SANS, 30)
    body_lines = wrap(d, "“She eats better if breakfast starts with something warm — oatmeal, not cereal.”", body_f, 980)
    yy = card[1] + 60
    for line in body_lines:
        d.text((card[0] + 60, yy), line, font=body_f, fill=CREAM)
        yy += 44
    typing_f = font(SANS, 24)
    d.text((card[0] + 60, card[3] - 60), "typing … kept.", font=typing_f, fill=ACCENT)
    cap_f = font(SANS_BOLD, 30)
    cap = "Morning routine"
    w = d.textlength(cap, font=cap_f)
    d.text(((W - w) / 2, H / 2 - 340), cap, font=cap_f, fill=CREAM)
    disclosure_bar(img, d)
    watermark(d)
    return img


def beat4_frame():
    img = Image.new("RGB", (W, H), (24, 24, 26))
    d = ImageDraw.Draw(img)
    time_f = font(SANS_BOLD, 30)
    time_text = "—  weeks later  —"
    w = d.textlength(time_text, font=time_f)
    d.text(((W - w) / 2, H / 2 - 400), time_text, font=time_f, fill=MUTED)
    card = [W / 2 - 560, H / 2 - 230, W / 2 + 560, H / 2 + 150]
    d.rounded_rectangle(card, radius=28, fill=(38, 38, 42), outline=ACCENT, width=3)
    body_f = font(SANS, 30)
    body_lines = wrap(d, "“What did she say worked for breakfast again?”", body_f, 980)
    yy = card[1] + 60
    for line in body_lines:
        d.text((card[0] + 60, yy), line, font=body_f, fill=CREAM)
        yy += 44
    pending_f = font(SANS, 24)
    d.text((card[0] + 60, card[3] - 60), "[ PENDING — real ANYA / Sample Parent exchange not yet sourced ]", font=pending_f, fill=WARN)
    cap_f = font(SANS_BOLD, 28)
    cap = "[ caption pending real exchange ]"
    w = d.textlength(cap, font=cap_f)
    d.text(((W - w) / 2, H / 2 - 340), cap, font=cap_f, fill=WARN)
    disclosure_bar(img, d)
    watermark(d)
    return img


def beat5_frame():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    url_f = font(SANS, 64)
    url = "anya.tenerra.ai"
    w = d.textlength(url, font=url_f)
    d.text(((W - w) / 2, H / 2 - 40), url, font=url_f, fill=INK)
    note_f = font(SANS, 26)
    note = "[ FINAL URL NOT YET CONFIRMED ]"
    w = d.textlength(note, font=note_f)
    d.text(((W - w) / 2, H / 2 + 50), note, font=note_f, fill=(160, 90, 80))
    watermark(d)
    return img


BEATS = [
    {"n": 1, "label": "Cold Open", "start": 0, "end": 12, "frame": beat1_frame,
     "vo": None},
    {"n": 2, "label": "Transition", "start": 12, "end": 22, "frame": beat2_frame,
     "vo": "Every parent I've worked with in thirty years has carried the same thing. Everything they know about their child, held nowhere but memory."},
    {"n": 3, "label": "Capture", "start": 22, "end": 40, "frame": beat3_frame,
     "vo": "Anya just listens. No forms. No fields that don't fit your child. She tells Anya what she knows, and it's kept."},
    {"n": 4, "label": "Retrieval", "start": 40, "end": 60, "frame": beat4_frame,
     "vo": "Weeks later, when she needed it again, it was still there. Not because she remembered to write it down twice. Because Anya already had it."},
    {"n": 5, "label": "Close", "start": 60, "end": 80, "frame": beat5_frame,
     "vo": "This is Anya. Built for what you already know."},
]


def wav_duration(path):
    with contextlib.closing(wave.open(path, "r")) as f:
        return f.getnframes() / float(f.getframerate())


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def synth_beat_audio(beat):
    dur = beat["end"] - beat["start"]
    out = os.path.join(AUDIO, f"beat{beat['n']}.wav")
    if not beat["vo"]:
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
             "-t", str(dur), out])
        return out
    raw = os.path.join(AUDIO, f"beat{beat['n']}_raw.wav")
    run(["espeak-ng", "-v", "en-us", "-s", "150", "-p", "35", "-a", "170",
         "-w", raw, beat["vo"]])
    speech_dur = wav_duration(raw)
    if speech_dur > dur:
        print(f"WARNING: beat {beat['n']} speech ({speech_dur:.1f}s) exceeds "
              f"beat duration ({dur}s) — will overrun into next beat's audio slot.")
    pad = max(dur - speech_dur, 0)
    lead = 0.4
    run(["ffmpeg", "-y", "-i", raw,
         "-af", f"adelay={int(lead*1000)}|{int(lead*1000)},apad=pad_dur={pad}",
         "-t", str(dur), "-ar", "44100", "-ac", "1", out])
    return out


def build():
    concat_list = os.path.join(BUILD, "concat.txt")
    audio_parts = []
    with open(concat_list, "w") as f:
        for beat in BEATS:
            dur = beat["end"] - beat["start"]
            frame_path = os.path.join(FRAMES, f"beat{beat['n']}.png")
            beat["frame"]().save(frame_path)
            seg_path = os.path.join(FRAMES, f"beat{beat['n']}_seg.mp4")
            run(["ffmpeg", "-y", "-loop", "1", "-i", frame_path, "-t", str(dur),
                 "-r", str(FPS), "-pix_fmt", "yuv420p", "-vf", f"scale={W}:{H}",
                 seg_path])
            f.write(f"file '{seg_path}'\n")
            audio_parts.append(synth_beat_audio(beat))

    video_concat = os.path.join(BUILD, "video_concat.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c", "copy", video_concat])

    narration = os.path.join(BUILD, "narration.wav")
    audio_concat_list = os.path.join(BUILD, "audio_concat.txt")
    with open(audio_concat_list, "w") as f:
        for p in audio_parts:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", audio_concat_list,
         "-ar", "44100", "-ac", "1", narration])

    out = os.path.join(HERE, "ANYA_Foundation_Video_ANIMATIC.mp4")
    run(["ffmpeg", "-y", "-i", video_concat, "-i", narration,
         "-c:v", "libx264", "-c:a", "aac", "-shortest", out])
    print(f"Wrote {out}")
    return out


if __name__ == "__main__":
    build()
