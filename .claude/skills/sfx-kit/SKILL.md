---
name: sfx-kit
description: >
  Add UI sound effects to a HyperFrames / GSAP motion-graphics video: pops when cards and photos appear, a stamp knock,
  a pen scratch while a line draws, ticks while a number runs, a paper tear, key clicks while text types on, a marker
  hiss on highlights. The sounds are synthesized in Python (no samples, no licences, no Content ID risk) and placed
  automatically from the composition's own timeline, so every sound lands on a real animation. Use this whenever a
  finished motion-graphics video feels silent between the words, when someone asks for "sound effects", "SFX",
  "whooshes", "pops" or "foley" on an animated explainer, Short or Reel, and before you reach for a stock SFX pack.
---

# Sound effects from the timeline

## The one idea

A motion-graphics video already knows when everything happens: it is in the GSAP timeline. So the effects track is
not hand-placed. `extract_events.mjs` walks the timeline and lists every slam, pop, line draw, number run, typing
reveal and highlight; `sfxkit.py` picks a voice for each one by **what moved** and synthesizes a single WAV that lines
up to the frame. Re-voice or re-time the video, run it again, and the effects follow.

The craft is not in the synthesis (that is solved). It is in **restraint**: a sound on every move reads as cheap.
The kit drops low-priority sounds that land too close to another one, keeps only every other pop in a run, and gives
different kinds of objects different sounds.

## Workflow

### 1 · Render the video as usual
The effects are mixed in after the render, so nothing in the composition changes. You need the composition HTML and
the rendered MP4.

### 2 · Extract the events

```bash
node scripts/extract_events.mjs path/to/composition.html events.json
```

It launches a headless Chrome (HyperFrames' bundled `chrome-headless-shell`, or `$CHROME_PATH`, or
`--browser-url http://127.0.0.1:9335` to reuse one), loads the page, and classifies each tween:

| Animation | Event | Default voice |
|---|---|---|
| scale-in from ≥ 1.4 (a slam) | `stamp` | **stamp**: light rubber-stamp knock |
| scale-in from ≤ 0.9 with `back`/`elastic` ease | `pop` | by the element's class: `.photo` → **photo** (paper flick), `.card` → **card** (paper slide), `.chip`/`.tag`/`.pill` → **chip** (soft click), SVG → **bubble** (three pitches) |
| `strokeDashoffset` (line draw) | `draw` | **pen** (scratch with a writing wobble) |
| `clip-path: inset(0 100% …)` → `inset(0 0% …)` (typing reveal) | `type` | **keys** (soft key clicks) |
| a number tween with `onUpdate` (≤ 6 s) | `count` | **ticks** that slow down with the ease |
| `backgroundSize` sweep (marker highlight) | `marker` | **marker** hiss |
| a big slide-in (≥ 300 px) or a blur zoom-in | `swoosh` | **swoosh** (fast pass of air) |
| `scaleX`/`scaleY` from 0 without a spring (bars, rules) | `wipe` | **card** (paper slide) |
| fade-up of an HTML element | `rise` | **air** (very soft) |

Start values are read from `tl.from()` vars and from `fromTo()` start objects alike. Ignored: tweens of 3 s or more,
yoyo/repeat loops, and anything on a camera, grid or background element (`.cam`, `#bg`, `.grain`…), so slow camera
drifts never make a sound. A composition drawn on a canvas as a function of time (no tweens per object) yields no
events: write the events file by hand (see `examples/`).

Ask for a specific voice on any element with `data-sfx="tear"` (a paper rip, e.g. on a crack line), or for silence
with `data-sfx="none"`. Only the animated element's own attribute counts.

### 3 · Synthesize

```bash
uv run --python 3.12 --with numpy --with soundfile python scripts/sfxkit.py events.json sfx.wav --report
```

Options: `--gain 0.8` overall level, `--no air,marker` drop voices, `--skip 12.5:35.0` no effects in a window
(e.g. under real footage that carries its own sound). `--report` prints every placed sound with its time: read it
against the video before you mix.

### 4 · Mix

```bash
ffmpeg -i video.mp4 -i sfx.wav -filter_complex \
 "[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0[s];[0:a][s]amix=inputs=2:normalize=0:duration=first[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k with_sfx.mp4
ffmpeg -i with_sfx.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v copy -c:a aac -b:a 192k final.mp4
```

Mix the effects **before** any insert that is not part of the composition (an intro card, a sponsor slate), so their
times still match the composition's clock.

### 5 · Say what you can and cannot know
You cannot hear the result. Report counts and levels (`--report`, the LUFS of the effects track, the final LUFS), make
it a separate file next to the plain version, and let the person listen and decide.

## Density and level rules

| Rule | Value | Why |
|---|---|---|
| Quiet needed before a low-priority sound (bubble, chip, air) | 1.2 s | stops the "every move pings" effect |
| … before a medium one (card, marker) | 0.8 s | |
| … before a high one (photo, pen, keys) | 0.25 s | |
| Stamps, tears, counters | always play | they carry meaning |
| A run of pops (gaps < 2.5 s) | every other one is silent | variety by omission |
| Effects track loudness (sparse) | about −33 LUFS integrated, peaks ≤ 0.25 | sits under narration at −16 LUFS final |

## Anti-patterns
- **One sound for every pop.** The first version of this kit put the same bubble on 43 pops in a 2.5-minute Short. It
  was the first thing the viewer noticed.
- **A low boom on stamps.** Anything with sub-bass reads as a branded sting. Keep a channel's intro sting unique.
- **Effects under real footage with dialogue.** Use `--skip` for those windows.
- **Unseeded randomness.** `sfxkit.py` seeds its generator; a re-run must give the same file.
- **Saying it sounds good.** Measure it, then ask.

## Files
- `scripts/extract_events.mjs`: timeline → events JSON (Node 18+, `puppeteer-core`; it finds HyperFrames' copy).
- `scripts/sfxkit.py`: events JSON → effects WAV. Voices: bubble, chip, card, photo, stamp, pen, tear, keys, tick, marker, swoosh, air.
- `examples/events.example.json`: a hand-written events file. Any editor can produce one (time + type), so the voices
  also work without HyperFrames.
