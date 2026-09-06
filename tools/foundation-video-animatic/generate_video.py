#!/usr/bin/env python3
"""
ANYA Foundation Video — animatic generator.

Renders a placeholder/animatic cut of the Foundation Video script: mockup
visuals (Pillow) + synthetic TTS narration (espeak-ng) + assembly (ffmpeg).
The mechanical parts (timing, TTS, ffmpeg assembly, watermarking,
disclosure bars) live in animatic_pipeline.py; this file only defines the
five beats' visuals and VO lines.

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
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animatic_pipeline as ap

W, H = ap.W, ap.H
HERE = os.path.dirname(os.path.abspath(__file__))
SITE_HTML = "/home/user/tenerra-geo/index.html"
BRAND_FONT = os.path.join(HERE, "fonts", "CormorantGaramond-Regular.ttf")
PALETTE = ap.load_palette(SITE_HTML)
INK, CREAM, ACCENT, MUTED, WARN = (
    PALETTE["ink"], PALETTE["cream"], PALETTE["accent"], PALETTE["muted"], PALETTE["warn"],
)
HEADER_WORDMARK = ap.load_header_wordmark(SITE_HTML)
if not HEADER_WORDMARK:
    raise RuntimeError(
        "Could not find the site header's wordmark in index.html — the "
        "opening card needs the real logo+company-name lockup, not a guess."
    )


def beat1_frame():
    img = ap.gradient_background(CREAM, PALETTE["cream_dim"])
    d = ImageDraw.Draw(img)
    ap.accent_rule(d, W / 2, H / 2 - 190, palette=PALETTE)
    quote_f = ap.font(ap.SERIF, 52)
    attrib_f = ap.font(ap.SERIF_ITALIC, 34)
    lines = ["“It's so easy!”", "", "“Now I'm not the only one holding it.", "Anya is too.”"]
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
    ap.watermark(d)
    return img


def beat2_frame():
    # Opening card: the real site-header wordmark (logo + "Tenerra"), not
    # the bare icon and not the header's separate "tenerra.ai" URL label.
    img = ap.gradient_background(INK, tuple(max(c - 10, 0) for c in INK))
    d = ImageDraw.Draw(img)
    ap.render_wordmark(
        img, d,
        logo_path=HEADER_WORDMARK["logo_path"],
        text=HEADER_WORDMARK["wordmark_text"],
        cx=W / 2, cy=H / 2 - 40,
        text_size=84, ink=CREAM, font_path=BRAND_FONT,
    )
    note_f = ap.font(ap.SANS, 24)
    note = "[ locked “Boxes → Vest” static open — placeholder card, real component not substituted ]"
    w = d.textlength(note, font=note_f)
    d.text(((W - w) / 2, H / 2 + 160), note, font=note_f, fill=MUTED)
    ap.watermark(d)
    return img


def beat3_frame():
    img = Image.new("RGB", (W, H), (24, 24, 26))
    d = ImageDraw.Draw(img)
    card = [W / 2 - 560, H / 2 - 230, W / 2 + 560, H / 2 + 150]
    d.rounded_rectangle(card, radius=28, fill=(38, 38, 42), outline=ACCENT, width=3)
    body_f = ap.font(ap.SANS, 30)
    body_lines = ap.wrap(d, "“She eats better if breakfast starts with something warm — oatmeal, not cereal.”", body_f, 980)
    yy = card[1] + 60
    for line in body_lines:
        d.text((card[0] + 60, yy), line, font=body_f, fill=CREAM)
        yy += 44
    typing_f = ap.font(ap.SANS, 24)
    d.text((card[0] + 60, card[3] - 60), "typing … kept.", font=typing_f, fill=ACCENT)
    cap_f = ap.font(ap.SANS_BOLD, 30)
    cap = "Morning routine"
    w = d.textlength(cap, font=cap_f)
    d.text(((W - w) / 2, H / 2 - 340), cap, font=cap_f, fill=CREAM)
    ap.disclosure_bar(d, "Demonstration using ANYA's Sample Family. Not a real user account.")
    ap.watermark(d)
    return img


def beat4_frame():
    img = Image.new("RGB", (W, H), (24, 24, 26))
    d = ImageDraw.Draw(img)
    time_f = ap.font(ap.SANS_BOLD, 30)
    time_text = "—  weeks later  —"
    w = d.textlength(time_text, font=time_f)
    d.text(((W - w) / 2, H / 2 - 400), time_text, font=time_f, fill=MUTED)
    card = [W / 2 - 560, H / 2 - 230, W / 2 + 560, H / 2 + 150]
    d.rounded_rectangle(card, radius=28, fill=(38, 38, 42), outline=ACCENT, width=3)
    body_f = ap.font(ap.SANS, 30)
    body_lines = ap.wrap(d, "“What did she say worked for breakfast again?”", body_f, 980)
    yy = card[1] + 60
    for line in body_lines:
        d.text((card[0] + 60, yy), line, font=body_f, fill=CREAM)
        yy += 44
    # pending_tag() centers on cx, but this note needs to sit left-aligned
    # inside the card, so draw it directly rather than through the helper.
    d.text((card[0] + 60, card[3] - 60), "[ PENDING — real ANYA / Sample Parent exchange not yet sourced ]",
            font=ap.font(ap.SANS, 24), fill=WARN)
    ap.pending_tag(d, "[ caption pending real exchange ]", W / 2, H / 2 - 340, color=WARN, size=28)
    ap.disclosure_bar(d, "Demonstration using ANYA's Sample Family. Not a real user account.")
    ap.watermark(d)
    return img


def beat5_frame():
    img = ap.gradient_background(CREAM, PALETTE["cream_dim"])
    d = ImageDraw.Draw(img)
    ap.accent_rule(d, W / 2, H / 2 - 110, palette=PALETTE)
    url_f = ap.font(ap.SANS, 64)
    url = "anya.tenerra.ai"
    w = d.textlength(url, font=url_f)
    d.text(((W - w) / 2, H / 2 - 40), url, font=url_f, fill=INK)
    ap.pending_tag(d, "[ FINAL URL NOT YET CONFIRMED ]", W / 2, H / 2 + 60, color=(160, 90, 80), size=26)
    ap.watermark(d)
    return img


BEATS = [
    {"n": 1, "start": 0, "end": 12, "frame": beat1_frame, "vo": None},
    {"n": 2, "start": 12, "end": 22, "frame": beat2_frame,
     "vo": "Every parent I've worked with in thirty years has carried the same thing. Everything they know about their child, held nowhere but memory."},
    {"n": 3, "start": 22, "end": 40, "frame": beat3_frame,
     "vo": "Anya just listens. No forms. No fields that don't fit your child. She tells Anya what she knows, and it's kept."},
    {"n": 4, "start": 40, "end": 60, "frame": beat4_frame,
     "vo": "Weeks later, when she needed it again, it was still there. Not because she remembered to write it down twice. Because Anya already had it."},
    {"n": 5, "start": 60, "end": 80, "frame": beat5_frame,
     "vo": "This is Anya. Built for what you already know."},
]

if __name__ == "__main__":
    out = os.path.join(HERE, "ANYA_Foundation_Video_ANIMATIC.mp4")
    ap.build(BEATS, out)
    ap.verify(out, [b["start"] + 1 for b in BEATS])
