---
style: Blueprint
number: 05
tier: free
verdict: Strong
tech: svg
best_for: showing how something is built: architectures, systems, specs, "anatomy of X"
avoid_for: emotional/story beats, humour
---

# 05 · Blueprint
> White linework on engineering blue, dimension arrows, leader labels, and one yellow note.

## Philosophy
A blueprint says "this was designed". Lines are drawn, not filled; every part is annotated with a dimension or a label; the single yellow note is the *human decision* on an otherwise mechanical sheet. The camera pans slowly across the drawing like an inspection.

## Use it when / skip it when
Use for: architectures, how-it-works diagrams, hardware/AI "anatomy", spec reveals.
Skip for: anything that should feel warm or playful.

## Palette
| Role | Hex | Use |
|---|---|---|
| Paper | `#0E3B6E` | background |
| Lines / type | `#E8F1FF` | outlines, titles |
| Faint | `#7FB3FF` | grid, dashed centre lines |
| Label | `#BFD8FF` | mono labels |
| Note | `#FFCF5C` | the ONE highlighted note |
Grid: 120 px major / 24 px minor lines at 22% / 10% opacity.

## Type
Bai Jamjuree 700 (title 128 px, sub 64 px, note 66 px); IBM Plex Mono 600 for labels (26 px, `letter-spacing .08em`), e.g. `W 780 · REV.A`, `MEMORY 200K`.

## Layout
Title top-left, title dimension line below it, the subject drawn in elevation in the middle, dimension lines and leader lines (L-shaped) pointing to labels at the right, a yellow-bordered note at the bottom, a `DWG 05` stamp.

## Motion
| Beat | Move | Ease |
|---|---|---|
| Title | slide from −80 px + fade | power3.out |
| Dimension line | draw-on, then ticks | power2.inOut |
| Subject parts | sequential draw-on, 0.17 s apart | power1.inOut |
| Centre line | fade in (dashed, not drawn) | none |
| Leaders + labels | draw-on then labels slide 20 px | power2.out |
| Note | `clip-path` wipe L→R | power3.inOut |
| Stamp | scale 2.2 + rotate −12° → 1 (thud) | back.out(2) |
Ambient: `.cam` pans (−30, −40) px across the whole clip.

## Signature technique
Square line caps and uniform 4 px strokes; dashed lines for axes use fixed `stroke-dasharray: 10 8` (never animated). Draw-on only for solid lines:
```js
p.classList.contains("f") ? "10 8" : `${L} ${L+40}`
```
The camera layer is oversized (`inset: -60px`) so the pan never reveals edges.

## Don'ts
- No solid fills except the single yellow note.
- No more than two line weights (4 px solid, 2.5 px dashed).
- No rounded line caps, no shadows.

## Pitfalls & tips
- Dashed lines must be excluded from the draw-on offset or they vanish.
- Rotated mono labels need `transform-origin: left top` to align with the dimension line.

## 16:9 note
Subject left-centre, labels and leaders to the right, note across the bottom. Keep the major grid at 120 px so scale feels the same.

## Prompt for Claude
Paste this with your script (replace the bracketed parts):
```
Build a HyperFrames composition in the "Blueprint" style.
Read _shared/HYPERFRAMES_RULES.md and styles/05-blueprint/STYLE.md completely, and use
styles/05-blueprint/example.html as the structural reference (same layering, same techniques).
Keep the palette, fonts and motion rules exactly. Obey every "Don't".
Outline only, no fills except one yellow note. Draw solid lines on, keep dashed lines static.
Content / script: [PASTE SCRIPT OR BEATS HERE]
Format: [1080x1920 vertical | 1920x1080 horizontal], [N] seconds.
Deliver one HTML file with a paused GSAP timeline in window.__timelines and a duration anchor.
```

## Files
`example.html` — the 6 s vertical reference composition (the micro-story "AI writes a note to its future self").
Render: `npx hyperframes@0.6.6 render . -c styles/05-blueprint/example.html -o out.mp4 -w 2` from the pack root.
