---
style: Terminal
number: 04
tier: free
verdict: Strong
tech: css
best_for: AI/dev content, "watch it run" demos, command and log storytelling
avoid_for: non-technical audiences, warm/emotional beats
---

# 04 · Terminal
> Phosphor-green text typed onto a dark screen with scanlines. Reads instantly as "this is the machine's point of view".

## Philosophy
A terminal is *evidence*: if it is on the screen, it happened. So the content is real-looking commands, counts, and one highlighted result. Output arrives line by line, exactly like a process running; the viewer reads at the machine's pace. The CRT overlay (scanlines + vignette) sells it without any 3D.

## Use it when / skip it when
Use for: Claude Code / CLI demos, token counts, config reveals, "here's what it printed".
Skip for: general audiences who don't know the idiom.

## Palette
| Role | Hex | Use |
|---|---|---|
| Screen | `#0C0F0A` (window `#070906`) | background |
| Phosphor | `#39FF6A` | prompt, title, key result (with glow) |
| Text | `#E9F5DB` | normal output |
| Dim | `#6E8F74` | secondary lines |
| Warn | `#FFB000` | in-progress/alert |
| Window border | `#1F5130` | frame |

## Type
IBM Plex Sans Thai (title 128 px / 700, sub 64 px / 600, result 84 px / 700) for anything Thai; IBM Plex Mono for commands and logs (42 px, line-height 1.8). Glow = `text-shadow: 0 0 12px rgba(57,255,106,.55), 0 0 2px rgba(57,255,106,.9)`.

## Layout
Title + sub at the top (with blinking block cursor), a bordered window (`#win`) in the middle with a 64 px title bar, lines inside. The key result gets an 8 px left bar and the glow.

## Motion
| Beat | Move | Ease |
|---|---|---|
| Title / sub | typed (clip-path reveal) | `steps(10)` / `steps(14)` |
| Window | `scaleY` 0→1 from top | power3.out |
| Command line | typed | `steps(9)` |
| Output lines | appear instantly (`steps(1)`) | — |
| Progress bar | `scaleX` in 12 steps | `steps(12)` |
| Result | typed line by line, then 3 quick background flashes | steps / none |
Ambient: cursor blinks (0.24 s), whole screen scales 1.0 → 1.03.

## Signature technique
**Typing = stepped clip-path reveal**, not per-character spans:
```js
const type = (el, at, dur, n) => tl.to(el, { clipPath: "inset(0 0% 0 0)", duration: dur, ease: `steps(${n})` }, at);
```
Scanlines: `repeating-linear-gradient(0deg, rgba(0,0,0,.28) 0 2px, transparent 2px 5px)` overlay + radial vignette overlay, both above the content.

## Don'ts
- No rounded UI, no serif, no gradients (other than the CRT overlay).
- No more than one accent besides green (amber for warnings only).
- Don't type everything: output lines should *appear*, only commands and the result are typed.

## Pitfalls & tips
- Per-letter typing broke Thai vowels/tone marks → clip-path steps.
- Text was too small at first: commands ≥ 42 px; the result ≥ 80 px.
- Make sure the font stack lists a Thai font after the mono, or Thai in logs falls back to a system font.

## 16:9 note
Window fills ~70% of the frame, centred; title above it left-aligned. Use two columns (command / output) only if lines stay ≥ 36 px.

## Prompt for Claude
Paste this with your script (replace the bracketed parts):
```
Build a HyperFrames composition in the "Terminal" style.
Read _shared/HYPERFRAMES_RULES.md and styles/04-terminal/STYLE.md completely, and use
styles/04-terminal/example.html as the structural reference (same layering, same techniques).
Keep the palette, fonts and motion rules exactly. Obey every "Don't".
Type commands with a stepped clip-path reveal; output lines appear instantly; keep the CRT overlay on top.
Content / script: [PASTE SCRIPT OR BEATS HERE]
Format: [1080x1920 vertical | 1920x1080 horizontal], [N] seconds.
Deliver one HTML file with a paused GSAP timeline in window.__timelines and a duration anchor.
```

## Files
`example.html` — the 6 s vertical reference composition (the micro-story "AI writes a note to its future self").
Render: `npx hyperframes@0.6.6 render . -c styles/04-terminal/example.html -o out.mp4 -w 2` from the pack root.
