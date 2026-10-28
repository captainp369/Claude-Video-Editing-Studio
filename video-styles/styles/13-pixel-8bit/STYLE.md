---
style: Pixel art 8-bit
number: 13
tier: free
verdict: Weakest (for Thai text); great for English/numbers and game beats
tech: canvas
best_for: games, "level up/attempt count" beats, nostalgia, countdowns, score-style stats
avoid_for: long Thai sentences at small sizes; premium looks
---

# 13 · Pixel art 8-bit
> The whole frame is a 180×320 canvas scaled 6×, advanced at 8 fps, with a 16-colour palette and an RPG dialog box.

## Philosophy
Real pixels, not pixel *filters*. The frame is literally drawn at 180×320 and upscaled with `image-rendering: pixelated`, so every edge is genuinely hard; motion is stepped at 8 fps and positions are integers. Game grammar tells the story: HUD, ground tiles, a sprite that jumps, an RPG dialog box that types, a ▼ continue marker.

## Use it when / skip it when
Use for: anything game-related, counters/score, retro jokes, a "level" metaphor.
Skip for: long, small Thai text; this was the weakest style for Thai legibility.

## Palette (Sweetie-16)
| Role | Hex |
|---|---|
| Background | `#1A1C2C` |
| Plum | `#5D275D` |
| Red | `#B13E53` |
| Orange | `#EF7D57` |
| Yellow | `#FFCD75` |
| Light green / teal / dark teal | `#A7F070` / `#38B764` / `#257179` |
| Navy / blue / sky / cyan | `#29366F` / `#3B5DC9` / `#41A6F6` / `#73EFF7` |
| White / greys / slate | `#F4F4F4` / `#94B0C2` `#566C86` / `#333C57` |
Use only these.

## Type
Latin: Press Start 2P. **Thai: draw the string on an offscreen canvas at small size in Kanit, threshold the alpha (`> 110`) so edges become hard pixels, then `drawImage` it.** Title 26 px, sub 13–16 px (in canvas pixels, i.e. ×6 on screen).

## Layout
Stars, a title that drops in, a sprite on a ground strip, a bottom RPG dialog box (white 2-px border, navy fill) that types two lines, a blinking ▼.

## Motion
| Beat | Move |
|---|---|
| Time | `t = floor(t*8)/8` (8 fps stepped) |
| Title | integer drop from −20 to 28 px |
| Sprite | jump arc `round(sin(k·π)·30)`, then 2-frame idle bob |
| Dialog | box height grows in 0.25 s, text revealed by cropping its bitmap width |
| Emphasis | 8-point pixel star burst expanding by integers |

## Signature technique
```js
function pixText(txt, size, color, weight=700, family="Kanit"){
  // draw on 178px-wide canvas, threshold alpha so edges are hard, return {c, w}
}
```
Everything is a `fillRect(x,y,w,h)` or `drawImage` at integer coordinates. Sprites are string arrays (`"....rr...."`) mapped to palette letters.

## Don'ts
- No smooth tweens, no gradients, no anti-aliased edges, no sub-pixel positions.
- Don't use more than the 16-colour palette.
- Don't put small Thai text on screen: the pixel grid makes it unreadable.

## Pitfalls & tips
- Thai at ≤ 12 px (canvas) is illegible and overflows: use ≥ 16 px for Thai or switch to English/numbers for the hard parts.
- Cache text bitmaps only after the font is loaded (`document.fonts.check`) or you freeze a fallback-font bitmap.
- Measure width from the thresholded pixels (`w`) so centring is exact.
- 16:9: use a 320×180 canvas scaled 6× (1920×1080).

## 16:9 note
Canvas 320×180 → 1920×1080. Side-scroller layout: ground at the bottom third, HUD along the top, dialog box across the bottom.

## Prompt for Claude
Paste this with your script (replace the bracketed parts):
```
Build a HyperFrames composition in the "Pixel art 8-bit" style.
Read _shared/HYPERFRAMES_RULES.md and styles/13-pixel-8bit/STYLE.md completely, and use
styles/13-pixel-8bit/example.html as the structural reference (same layering, same techniques).
Keep the palette, fonts and motion rules exactly. Obey every "Don't".
Render everything on a small canvas scaled with image-rendering: pixelated, stepped at 8 fps, integer coordinates, Sweetie-16 palette only. Keep Thai text large or use English/numbers.
Content / script: [PASTE SCRIPT OR BEATS HERE]
Format: [1080x1920 vertical | 1920x1080 horizontal], [N] seconds.
Deliver one HTML file with a paused GSAP timeline in window.__timelines and a duration anchor.
```

## Files
`example.html` — the 6 s vertical reference composition (the micro-story "AI writes a note to its future self").
Render: `npx hyperframes@0.6.6 render . -c styles/13-pixel-8bit/example.html -o out.mp4 -w 2` from the pack root.
