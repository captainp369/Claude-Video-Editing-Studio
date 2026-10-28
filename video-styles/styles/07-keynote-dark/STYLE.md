---
style: Keynote minimal (Premium Dark)
number: 07
tier: free
verdict: Strong
tech: css
best_for: the default for product/tech videos; titles, claims, launches
avoid_for: playful/hand-made moods
---

# 07 · Keynote minimal · Premium Dark
> Black canvas, lit chrome type, one coral light. The studio's default look.

## Philosophy
Restraint reads as confidence. The frame is black glass: type is "lit" with a chrome gradient, one coral object (the orb) is the only colour and the only light source, and the camera never stops creeping forward. Everything that appears does so with a soft blur-in, as if focusing. Compatible with `MOTION_PHILOSOPHY.md` (Premium Dark).

## Use it when / skip it when
Use for: titles, launches, hero claims, anything that must feel premium.
Skip for: casual or handmade moods.

## Palette
| Role | Hex | Use |
|---|---|---|
| Black | `#000000` | background |
| Chrome type | `#FFFFFF → #D9D9D9 → #8A8A8A → #F2F2F2` (gradient clipped to text) | titles |
| Muted | `#9A9A9A` | sub line |
| Coral | `#D97757` | the only accent: orb, halo, key words, labels |
| Glass | `rgba(255,255,255,.06)` + 1.5 px `rgba(255,255,255,.18)` border | cards |

## Type
Kanit 800 for the chrome title (150 px), Kanit 600 sub (60 px), Kanit 700 card text (70 px); Inter 700, `letter-spacing .22em`, 24 px for small caps labels.

## Layout
Title top, orb centred in the upper-middle, glass card in the lower third; registration crosses (+) in the four corners; a perspective grid floor receding at the bottom.

## Motion
| Beat | Move | Ease |
|---|---|---|
| Title | scale 1.18 → 1 + blur 16 → 0 | power3.out (0.9 s) |
| Sub | rise 24 px + fade | power2.out |
| Light sweep | skewed gradient bar crosses the title | power2.inOut |
| Orb | scale 0 + rotate −90° → 0 | back.out(1.7) |
| Halo | scale .5 → 1 + fade | sine.out |
| Card | rise 120 px, scale .96 → 1 | expo.out |
| Emphasis | card border + coral glow pulse | sine.inOut |
Ambient: camera scale 1 → 1.06, grid scrolls, orb star rotates 90° over 4 s.

## Signature technique
Chrome text: `background: linear-gradient(180deg,#fff 0%,#d9d9d9 45%,#8a8a8a 60%,#f2f2f2 100%); -webkit-background-clip: text; color: transparent;`
Grid floor: `perspective(900px) rotateX(64deg)` with a mask fade `linear-gradient(#000 0%, transparent 70%)`, animated with `backgroundPositionY`.

## Don'ts
- More than ONE accent colour (coral only).
- Bright backgrounds, hard shadows, or illustration.
- A frozen frame: the camera push-in must run the whole clip.

## Pitfalls & tips
- Chrome text needs `-webkit-background-clip: text` AND `color: transparent`; animating `filter: blur()` on it renders fine (the example does).
- Keep the `.sweep` inside the camera layer so it zooms with the title.

## 16:9 note
Title left, orb right; card as a lower-third. The grid becomes the bottom 30% of the frame.

## Prompt for Claude
Paste this with your script (replace the bracketed parts):
```
Build a HyperFrames composition in the "Keynote minimal (Premium Dark)" style.
Read _shared/HYPERFRAMES_RULES.md and styles/07-keynote-dark/STYLE.md completely, and use
styles/07-keynote-dark/example.html as the structural reference (same layering, same techniques).
Keep the palette, fonts and motion rules exactly. Obey every "Don't".
Black background, chrome gradient type, coral is the ONLY accent. The camera must creep forward all clip.
Content / script: [PASTE SCRIPT OR BEATS HERE]
Format: [1080x1920 vertical | 1920x1080 horizontal], [N] seconds.
Deliver one HTML file with a paused GSAP timeline in window.__timelines and a duration anchor.
```

## Files
`example.html` — the 6 s vertical reference composition (the micro-story "AI writes a note to its future self").
Render: `npx hyperframes@0.6.6 render . -c styles/07-keynote-dark/example.html -o out.mp4 -w 2` from the pack root.
