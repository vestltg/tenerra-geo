# Foundation Video — Animatic Generator

Code that renders a timing/pacing check of the ANYA Foundation Video script:
mockup visuals + synthetic narration, assembled into an MP4 matching the
beat timestamps in `ANYA_Foundation_Video_Storyboard_1.docx` / the VO cue
sheet exactly (0:00–0:12, 0:12–0:22, 0:22–0:40, 0:40–0:60, 0:60–0:80).

## This is not the final video

There is no real footage or real narration to build from yet, so this
generates a **placeholder animatic**, not a shippable asset:

- **Narration is `espeak-ng`**, left deliberately robotic. The storyboard
  is explicit that this asset needs Michael's real recorded voice, not
  synthetic speech — a cleaner TTS voice would risk being mistaken for
  final. Every frame carries a burned-in watermark saying so.
- **Visuals are mockups.** Beat 2 stands in for the locked "Boxes → Vest"
  static open using the real logo asset from `assets/images/tenerra-logo.png`
  on a placeholder card. Beats 3–4 are generic chat-bubble mockups standing
  in for the real Sample Mom capture/retrieval screens.
- **Open items from the script are rendered on-screen, not silently
  resolved**: Beat 4's caption/exchange is marked `PENDING` (not sourced
  yet) and Beat 5's URL is marked `NOT YET CONFIRMED`, matching the
  outstanding blockers tracked in `ANYA_Foundation_Video_Script_v2.docx`.

Use it to sanity-check pacing and beat lengths against the ~80s target —
not to preview final tone, voice, or footage.

## Requirements

- `ffmpeg` (`apt-get install ffmpeg`)
- `espeak-ng` (`apt-get install espeak-ng`)
- Python 3 with Pillow (`pip install Pillow`)
- DejaVu / Liberation TTF fonts (present by default on Debian/Ubuntu)

## Run

```bash
python3 generate_video.py
```

Writes `ANYA_Foundation_Video_ANIMATIC.mp4` (1920x1080, 80s) next to the
script. Intermediate frames/audio are written to `build/` and can be
deleted between runs.

## Updating the script

Edit the `BEATS` list at the bottom of `generate_video.py` — each beat has
a `frame` function (Pillow drawing) and a `vo` string (or `None` for
silence). Beat timing comes from `start`/`end` in seconds.
