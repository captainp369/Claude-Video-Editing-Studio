---
name: music-bed
description: >
  Compose an original background music bed for a narrated video — synthesized
  locally in Python (no library, no licensing, no downloads) and arranged to the
  edit's own act structure so the music opens up exactly where the story does.
  Use this whenever a video needs music, score, a soundtrack, an underscore, or
  "something under the narration"; whenever a cut feels silent, flat, or like
  it's missing energy; whenever someone asks what music to put behind a pitch,
  intro, explainer, or Shorts/Reels edit; and whenever you are about to suggest
  finding a stock track — build one instead, it takes about a minute and it can
  be timed to the beats of this specific edit in a way stock never is.
---

# Music beds for narrated video

## The one idea

A stock track is a loop that happens to be playing while your video plays. A bed
built with this skill is **arranged to the edit**: it is sparse while the problem
is being stated, it warms when the product appears, it opens up on the emotional
peak, and it resolves on the call to action. That correspondence is the entire
reason to build one rather than download one, and it costs almost nothing because
you already know the act timings — you cut them.

So the work is not "write music." The work is: get the act map, choose a palette
that matches the video's temperature, and draw gain envelopes whose corners land
on act boundaries.

The DSP is already solved in `scripts/bedkit.py`. Do not re-derive envelopes and
harmonic stacks; spend your judgement on tempo, instrument choice, and where the
music changes shape.

## Workflow

### 1 · Get the real act map

Never guess the timings. Measure them from the narration you actually rendered:

```bash
for f in a*.wav; do
  printf "%s %s\n" "$f" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")"
done
```

Then lay out act start times exactly as the composition uses them (lead-in plus
inter-act gaps). Write the act map down — you will reuse it twice, once for the
envelopes and once for the verification step.

### 2 · Choose the palette

Match the temperature of the video, not your own taste. `references/palettes.md`
has tempo ranges, voice combinations, and chord progressions for the common
cases: brisk product pitch, calm/reflective, tense or investigative, warm
storytelling. Read it when the choice isn't obvious.

Two quick anchors:
- **Brisk pitch / feature demo** — 92–100 BPM, `pluck` ostinato + `pulse` + `shaker`.
- **Calm, personal, reflective** — 72–80 BPM, `felt` + `drone` + `brush`, no tick.

### 3 · The shortcut: `bed_from_timeline.py`

Most narrated videos have the same six-act shape, so you rarely need to write an arrangement by hand.
If the edit writes a timeline (`{"starts": [...line start times...], "end": seconds}`), one command builds the bed:

```bash
uv run --python 3.12 --with numpy --with soundfile python scripts/bed_from_timeline.py timeline.json music.wav \
  --acts 1,4,8,9,11,13 --key minor --mood tense --bpm 104 --seed 1983
```

`--acts` names six narration lines (0-based) where the music changes shape: **tension** (the problem; sparse, with a
low drone if `--mood tense`) · **turn** (the answer arrives; pulse and ostinato come in) · **build** · **peak**
(fullest) · **settle** · **question** (pad only, for the closing question or call to action). `--seconds` takes six
times instead. `--key minor` (D minor) suits history, business, investigation; `--key major` (C major) suits warm,
light topics. `--duck a:b` (repeatable) or `--duck-timeline` silences the bed under real footage that has its own
sound. Same arguments, same seed → a byte-identical file.

Write a custom arrangement (below) only when the six-act shape does not fit.

### 4 · Write a custom arrangement

Import `bedkit`, declare the chord cycle in note names, and drive it from
`Bed.bars()` / `Bed.beats()`. `scripts/example_arrangement.py` is a complete,
runnable arrangement you can copy and edit — start from it rather than a blank
file.

The envelopes are where the skill lives:

```python
warmth = b.env([(0, 0.30), (9, 0.42),      # problem — thin, a little cold
                (14, 0.85),                 # the turn — warmth arrives
                (56, 1.15), (72, 1.05),     # the peak — open it up
                (82, 0.55), (89, 0.0)])     # resolve and clear out
```

Every corner is an act boundary. If you find yourself picking round numbers like
30 and 60, you have stopped scoring the edit and started decorating it.

### 5 · Render

```bash
uv run --python 3.12 --with numpy --with soundfile python arrangement.py
```

Keep it deterministic. Use `Bed`'s seeded `rng` for noise voices and harmonic
functions (`sin`, `cos`) for any variation — never unseeded randomness. A
re-render must produce a byte-identical file, or a later re-render silently
changes the mix under a video you already approved.

### 6 · Verify what you cannot hear

This is the step that makes the whole thing trustworthy, so do not skip it:

```bash
python scripts/inspect_bed.py music.wav --map "0:problem,14:turn,56:bloom,81:resolve"
```

It prints loudness, peak and duration, flags clipping and level problems, and
writes a waveform-over-spectrogram picture. **Open the picture** and check the
arrangement you intended is visible: sparse regions should look sparse, the
bloom should show added high-frequency energy, the resolve should taper. If the
picture looks uniform, your envelopes aren't doing anything and the bed is a
loop no matter what the code says.

### 7 · Mix and declare the gap

In HyperFrames the bed is another audio track. Under continuous narration (a voice-over that rarely pauses)
`data-volume` 0.22 sits it under the words; with sparse narration or long pauses, 0.30–0.34. Then normalise the finished mix:

```bash
ffmpeg -i render.mp4 -c:v copy -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -b:a 192k final.mp4 -y
```

Targets that work: bed renders near **−24 LUFS**, final mix **−16 LUFS**, which
leaves roughly 8–10 LU between music and voice.

Then the honest part. You generated audio you have never heard. Say so plainly
when you deliver — one or two sentences, no hedging elsewhere — and offer to
change or remove it:

> The music is synthesized and I can't hear it, so I can only tell you it
> measures right and the arrangement matches the act map. If it grates, say
> so — swapping or dropping it is one command.

Users forgive a bed they don't like. They do not forgive being told something
sounds good by someone who couldn't hear it.

## Level targets

| Thing | Target | Why |
|---|---|---|
| `Bed.master(peak=…)` | `0.30` | lands near −24 LUFS with headroom to spare |
| bed integrated | −24 LUFS | quiet enough to disappear under speech |
| `data-volume` | 0.22 (continuous VO) – 0.34 (sparse VO) | in-composition trim |
| final mix | −16 LUFS | YouTube/IG normalise near here; louder gets turned down |
| true peak | ≤ −1.5 dBTP | survives lossy encoding without clipping |

## Anti-patterns

- **A loop instead of an arrangement.** If the music would work equally well over
  a different video, you haven't used the one advantage you had.
- **Melody that competes with the narration.** A bed is texture and harmonic
  motion. The moment it becomes a tune, the viewer listens to it instead of the
  words. Keep the ostinato inside an octave and let the envelope carry interest.
- **A bright tick at high gain.** `shaker` reads as a clock at gain above ~0.15;
  under slow narration use `brush` instead. Check the spectrogram — if the tick
  shows as full-height bars, it's too loud.
- **Unseeded randomness.** Breaks determinism; a re-render becomes a remix.
- **No resolve.** Ending on an unresolved chord under a CTA leaves the viewer
  faintly unsettled at the exact moment you want them to act. Ring out on the
  tonic.
- **Claiming it sounds good.** You don't know that. Report what you measured.

## Files

- `scripts/bedkit.py` — the synth library: `note()`, voices (`pluck`, `felt`,
  `drone`, `pulse`, `shaker`, `brush`), and `Bed` (placement, bars/beats,
  envelopes, mastering). Read the docstrings before writing an arrangement.
- `scripts/bed_from_timeline.py` — the six-act bed from a timeline JSON; covers most narrated videos.
- `scripts/example_arrangement.py` — a complete 90-second bed. Copy and edit for custom shapes.
- `scripts/inspect_bed.py` — verification and the act-map check.
- `references/palettes.md` — tempo, voicing and progression choices by video
  temperature. Read when the palette isn't obvious from the brief.
