# Audio pipeline: music bed, sound effects, levels

How audio is made in this workspace. The method lives in two skills, `.claude/skills/music-bed/` and
`.claude/skills/sfx-kit/`; this file is the house settings on top of them. Everything is synthesized by code:
no samples, no licences, nothing for Content ID to match.

## Levels (every video)
| Track | Level |
|---|---|
| Narration | as recorded or voiced; the final loudnorm evens the mix |
| Music bed in a Short | `<audio id="mus" … data-volume="0.22">` in the composition |
| Music bed in a long-form | mixed after the chapters are joined: `amix` with `volume=0.22` |
| Sound effects | effects track about −33 LUFS integrated, peaks ≤ 0.25, mixed at unity |
| Final | `loudnorm=I=-16:TP=-1.5:LRA=11` → about −16 LUFS, true peak ≤ −1.5 dBTP |

## Music bed
Give the bed six story acts (tension, turn, build, peak, settle, question) and it arranges itself around them:

```bash
uv run --python 3.12 --with numpy --with soundfile python \
  .claude/skills/music-bed/scripts/bed_from_timeline.py \
  timeline.json comp/audio/music.wav --acts 1,4,8,9,11,13 --key minor --mood tense --bpm 104 --seed 1983
```

- `--acts`: six line indices (0-based) for **tension**, **turn**, **build**, **peak**, **settle** and **question**.
- **Key and mood by topic:** history, business, crisis → `--key minor --mood tense`; tech, AI, news explainers →
  `--key minor --mood light`; food, travel, warm human stories → `--key major --mood light`.
- **Footage with its own speech:** add `--duck-timeline` so the bed drops out under it.

See `.claude/skills/music-bed/SKILL.md` for the full options.

## Sound effects
`sfx-kit` reads the composition's own GSAP timeline, so every sound lands on a real animation:
extract the events → synthesize one WAV → mix it under the render. See `.claude/skills/sfx-kit/SKILL.md`.

House rules:
- **Vary and thin the pops.** A photo gets a paper flick, a card a paper slide, a chip a soft click, an SVG a bubble;
  some pops stay silent. A sound on every move reads as cheap.
- A line being drawn gets a pen sound; a running number gets ticks; a crack or tear gets `data-sfx="tear"` on its path.
- No low booms on stamps.
- Test new effects on an unpublished video first, and report levels (LUFS, peak), not "it sounds good".
- Skip windows where real footage carries its own speech.

## Practical notes
- Renders need free space on the system disk (a render failed at 1 GB free; 3 GB+ is safe).
- `extract_events.mjs` launches its own headless Chrome (HyperFrames' bundled one), so no extra install is needed.
