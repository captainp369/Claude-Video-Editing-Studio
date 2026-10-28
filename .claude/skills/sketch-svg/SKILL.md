---
name: sketch-svg
description: Author hand-drawn / marker-style SVG icons and graphics inside HyperFrames compositions (or any HTML). Use whenever a beat needs sketchy, hand-drawn iconography instead of crisp UI icons — Word/Excel/PowerPoint-style app logos, coffee cups, X-strikes, arrows, checkmarks, frames, banners, anything that should read "drawn by hand, not designed in Figma." Covers the four core techniques (wavy paths, sloppy outline coordinates, stroke-dasharray draw-in animation, handwritten labels) plus a library of ready-to-paste icon templates.
---

# Sketch SVG — Hand-Drawn Icons in HyperFrames

## When to use this skill

Reach for these patterns when a beat calls for:

- **Brand-app icons without licensing risk.** Word / Excel / PowerPoint / Photoshop / Figma / etc. — draw approximations instead of copying real logos.
- **Cross-outs, X-strikes, eliminations.** "These tools are obsolete." "Don't do this." "Remove X."
- **Coffee, food, objects, gestures, arrows.** Anything that should feel personal rather than corporate-clean.
- **Hand-annotated highlights.** Circling text on a screenshot, drawing arrows pointing at UI elements.
- **Whiteboard / sketch / explainer-video aesthetic.** When the design philosophy is "drawn while talking" rather than "polished motion graphic."

**Don't use this skill for:**
- Crisp UI elements (use Hyperframes registry blocks or clean SVG).
- Anything where the icon needs to be pixel-perfect recognizable as a real brand.
- Photoreal imagery (use real images, never sketch).

## The four core techniques

### Technique 1 — Wavy paths replace straight lines

A perfectly straight line reads as machine-drawn. A line with a barely-noticeable curve reads as hand-drawn. The trick is the **quadratic Bézier with an off-axis control point**.

```html
<!-- BAD: machine-straight -->
<line x1="44" y1="64" x2="144" y2="64" stroke="#2B579A" stroke-width="4"/>

<!-- GOOD: wavy via Q + T -->
<path d="M44 64 Q70 60 110 64 T144 62"
      stroke="#2B579A" stroke-width="4" fill="none" stroke-linecap="round"/>
```

- `M44 64` — move pen to start
- `Q70 60 110 64` — curve via control point (70, 60) to (110, 64). The control point's `y=60` is **4px off-axis** from the endpoints' `y=64`, creating a subtle bulge upward.
- `T144 62` — smooth reflected curve to (144, 62). The endpoint y also drifts (62 vs 64) so the line doesn't end exactly where it started.

**Rule of thumb:** for a line of length L, drift the control point 3–5% of L off-axis. Tiny drift = subtle hand. Big drift = sloppy / cartoonish.

### Technique 2 — Sloppy outlines via offset coordinates + rounded joins

A perfect rectangle has corners at exactly the four points. A hand-drawn rectangle has corners that the pen "pulled away from" slightly. Use Bézier curves at the corners with 1–3px offset, and always set `stroke-linejoin="round"` + `stroke-linecap="round"`.

```html
<!-- A sketchy document/page outline -->
<path d="M30 22 Q26 20 24 26 L26 158 Q24 168 32 166 L150 162 Q158 164 156 154 L152 26 Q156 18 148 20 Z"
      stroke="#2B579A" stroke-width="5"
      fill="rgba(43,87,154,0.18)"
      stroke-linejoin="round" stroke-linecap="round"/>
```

Notice every corner is `Q<control> <endpoint>` instead of a hard `L` join. The control points are 2–6px outside the "true" corner position, so the line bulges out slightly at each corner — like a marker tip wandering.

**Fill recipe:** `fill="rgba(<r>,<g>,<b>,0.18)"` using the SAME color as the stroke. The 18% tint reads as "lightly washed with the marker color" without competing with the outline.

### Technique 3 — `stroke-dasharray` draw-in animation

The signature move of hand-drawn motion graphics: the icon appears to be drawn by an invisible pen. Done via dasharray trickery.

```css
.icon-path {
  stroke-dasharray: 240;     /* total ≥ path length */
  stroke-dashoffset: 240;    /* fully hidden */
}
```

```js
// GSAP tweens the offset to 0 — the dash "uncovers" the path left-to-right.
tl.to(".icon-path", { strokeDashoffset: 0, duration: 0.45, ease: "power2.out" }, beatStart);
```

**Calibrating the dash length:** use a value ≥ the actual path length. For most icons inside an 0 0 100 100 viewBox, 200–280 covers it. If the path is longer, bump higher. Too short = path still cut off after animation completes.

**Direction control:** by default the path draws from its `M` point onward. To reverse (draw "backwards"), flip the path's coordinate order, OR animate `stroke-dashoffset` from `-pathLength` to `0`.

**Order multiple paths via GSAP stagger:**
```js
tl.to("#cup .body",   { strokeDashoffset: 0, duration: 0.55 }, 0.0);
tl.to("#cup .handle", { strokeDashoffset: 0, duration: 0.35 }, 0.30);
tl.to("#cup .saucer", { strokeDashoffset: 0, duration: 0.30 }, 0.55);
tl.to("#cup .steam",  { strokeDashoffset: 0, duration: 0.45, stagger: 0.05 }, 0.75);
```

### Technique 4 — Caveat font labels under sketched icons

The icons alone aren't quite enough — the labels under them need to look hand-lettered too. Google Fonts' [Caveat](https://fonts.google.com/specimen/Caveat) is the right call: it reads as natural marker-script, has multiple weights, loads from a CDN, has full Latin glyphs.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&display=block" rel="stylesheet">
```

```css
.icon-label {
  font: 700 20px/1 "Caveat", "Inter", cursive;
  letter-spacing: 0.04em;
  color: rgba(255,255,255,0.85);
}
```

**Always `display=block` on the Google Fonts URL** for hyperframes renders — this forces deterministic loading. `display=swap` will render the icon labels in Inter on frame 1 and switch to Caveat on frame 60, which is visible in the rendered MP4.

**Pair with Inter or any clean sans for the headers.** Caveat for the icon label, Inter for the title above — the contrast sells the "system-generated explanation + my-marker annotation" feel.

## Icon library (copy-paste templates)

All icons assume `viewBox="0 0 180 180"` unless stated. Adjust stroke widths down for smaller viewports, up for larger.

### Document / Word page

```html
<svg viewBox="0 0 180 180">
  <!-- page outline with folded-corner-friendly shape -->
  <path d="M30 22 Q26 20 24 26 L26 158 Q24 168 32 166 L150 162 Q158 164 156 154 L152 36 L136 22 Z"
        stroke="#2B579A" stroke-width="5" fill="rgba(43,87,154,0.18)"
        stroke-linejoin="round" stroke-linecap="round"/>
  <!-- folded-corner indicator -->
  <path d="M136 22 L138 36 L152 36" stroke="#2B579A" stroke-width="5" fill="none" stroke-linejoin="round"/>
  <!-- wavy text lines -->
  <path d="M44 64 Q70 60 110 64 T144 62" stroke="#2B579A" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="M44 86 Q70 82 110 86 T140 84" stroke="#2B579A" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="M44 108 Q70 104 110 108 T142 106" stroke="#2B579A" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="M44 130 Q60 126 90 130 T122 128" stroke="#2B579A" stroke-width="4" fill="none" stroke-linecap="round"/>
</svg>
```

Recolor `#2B579A` (Word blue) to any brand or neutral. The wavy text lines are the iconic move.

### Spreadsheet / Excel page

Same outline as Document, replace the text lines with a wavy grid:

```html
<!-- horizontal rules -->
<path d="M30 60 Q88 56 154 62" stroke="#217346" stroke-width="4" fill="none" stroke-linecap="round"/>
<path d="M30 92 Q88 88 154 94" stroke="#217346" stroke-width="4" fill="none" stroke-linecap="round"/>
<path d="M30 124 Q88 120 154 126" stroke="#217346" stroke-width="4" fill="none" stroke-linecap="round"/>
<!-- vertical rules — note Q control point off the central axis -->
<path d="M70 30 Q66 88 72 158" stroke="#217346" stroke-width="4" fill="none" stroke-linecap="round"/>
<path d="M114 30 Q110 88 116 158" stroke="#217346" stroke-width="4" fill="none" stroke-linecap="round"/>
```

### Presentation / PowerPoint slide

Page outline + a header line + 3 bar-chart bars with rough rectangles:

```html
<!-- slide header underline -->
<path d="M44 50 Q80 46 120 50 T146 48" stroke="#B7472A" stroke-width="4" fill="none" stroke-linecap="round"/>
<!-- bar chart -->
<rect x="50"  y="120" width="22" height="30" stroke="#B7472A" stroke-width="3.5" fill="rgba(183,71,42,0.30)" rx="2"/>
<rect x="82"  y="98"  width="22" height="52" stroke="#B7472A" stroke-width="3.5" fill="rgba(183,71,42,0.30)" rx="2"/>
<rect x="114" y="80"  width="22" height="70" stroke="#B7472A" stroke-width="3.5" fill="rgba(183,71,42,0.30)" rx="2"/>
```

The `rx="2"` slightly rounds the bar corners — small touch but matters.

### X-strike (cross-out, animatable)

For striking through anything. The two crossing strokes draw in via dasharray.

```html
<svg viewBox="0 0 180 180">
  <path class="x-stroke" d="M20 24 L162 156 M158 28 L24 158"
        stroke="#e53935" stroke-width="6" stroke-linecap="round" fill="none"/>
</svg>
```

```css
.x-stroke {
  stroke-dasharray: 240;
  stroke-dashoffset: 240;
  filter: drop-shadow(0 0 6px rgba(229,57,53,0.4));
}
```

```js
tl.to(".x-stroke", { strokeDashoffset: 0, duration: 0.45, ease: "power2.out" }, time);
```

Position the X as an absolute overlay on top of the icon you want to cross out:
```html
<div class="icon" style="position:relative;">
  <svg class="base-icon">...</svg>
  <svg class="cross" style="position:absolute; inset:0;">...</svg>
</div>
```

### Coffee cup with steam

Four separately-animatable paths — `body`, `handle`, `saucer`, `steam` (3 strands). Each starts hidden via `stroke-dashoffset` and is drawn in by GSAP in order.

```html
<svg viewBox="0 0 130 130">
  <!-- steam squiggles (3 strands rising) -->
  <path class="steam" d="M50 18 Q56 8 50 0" />
  <path class="steam" d="M65 14 Q72 4 66 -4" />
  <path class="steam" d="M80 18 Q86 8 80 0" />
  <!-- cup body trapezoid (wider top, narrower bottom) -->
  <path class="body" d="M28 46 Q26 44 28 50 L40 110 Q42 122 54 122 L80 122 Q92 122 94 110 L102 50 Q104 44 100 46 Z" />
  <!-- handle on the right -->
  <path class="handle" d="M102 60 Q120 64 116 86 Q112 100 98 96" />
  <!-- saucer beneath -->
  <path class="saucer" d="M30 122 Q66 134 102 122" />
</svg>
```

```css
.steam, .body, .handle, .saucer {
  stroke: var(--teal);
  stroke-width: 5;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 8px rgba(31,184,118,0.6));
}
.body   { stroke-dasharray: 280; stroke-dashoffset: 280; }
.handle { stroke-dasharray:  90; stroke-dashoffset:  90; }
.saucer { stroke-dasharray:  80; stroke-dashoffset:  80; }
.steam  { stroke-dasharray:  50; stroke-dashoffset:  50; opacity: 0.7; }
```

### Arrow (sketchy, animatable)

A wavy shaft + an arrowhead, both drawable.

```html
<svg viewBox="0 0 200 60">
  <path class="shaft" d="M10 30 Q60 22 110 32 T170 28"
        stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path class="head" d="M155 14 L180 30 L155 46"
        stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

Animate shaft first, then head.

### Checkmark (drawn-in)

```html
<svg viewBox="0 0 100 100">
  <path class="check" d="M22 52 Q32 60 44 72 Q60 50 82 28"
        stroke="#1FB876" stroke-width="8" fill="none"
        stroke-linecap="round" stroke-linejoin="round"
        style="stroke-dasharray: 140; stroke-dashoffset: 140;"/>
</svg>
```

### Frame (circling something — highlight a UI element)

```html
<svg viewBox="0 0 200 100">
  <path class="frame"
        d="M10 50 Q10 20 50 16 Q100 12 150 18 Q190 20 188 50 Q190 80 150 84 Q100 88 50 84 Q10 80 10 50 Z"
        stroke="#fc0" stroke-width="6" fill="none" stroke-linecap="round"
        style="stroke-dasharray: 600; stroke-dashoffset: 600;"/>
</svg>
```

Imperfect oval — Bézier control points all slightly off the cardinal axes. Drops as a hand-drawn circle around any element it's overlaid on.

## Anti-patterns

- ❌ **Using `<rect>` / `<circle>` / `<line>` for sketch icons.** They're geometrically perfect — that's the opposite of what we want. Always `<path>` with Béziers.
- ❌ **`stroke-linejoin="miter"` (the SVG default).** Creates sharp pointed corners — reads as crisp UI, not hand-drawn. Always round.
- ❌ **Solid fills at 100% opacity.** Looks like Adobe Illustrator output. Use `rgba(<color>, 0.15–0.25)` tint — reads as "lightly washed with the same marker."
- ❌ **`display=swap` on the Caveat font URL.** Hyperframes captures frame 1 before the font has loaded, so the label renders in fallback Inter for the first frames. Always `display=block` for any text inside a rendered composition.
- ❌ **`stroke-dasharray` smaller than the path length.** The path will draw, then "wrap around" and the dash pattern will become visible at the end of animation. Always overshoot — pick a dasharray ≥ 1.2× the actual path length, or precompute with `getTotalLength()` in JS.
- ❌ **One giant SVG with everything in it.** Split each draw-in element into its own `<path>` with a distinct class so GSAP can animate them on independent timelines. The coffee cup has 4 separate path classes for a reason.
- ❌ **Hard-coded coordinates assuming a fixed viewBox.** Always include `viewBox` so the icon scales to its container. SVG inside a `width:180px; height:180px` div with `viewBox="0 0 180 180"` works at any output resolution.
- ❌ **Using sketch icons in a clean / corporate / fintech aesthetic.** They clash with crisp UI. Sketch icons want a friendly explainer-video context. Match aesthetic before reaching for this skill.

## Origin

These patterns were first proven in a real explainer: Word/Excel/PowerPoint sketch icons crossed out under "NO NEED TO LEARN", plus a hand-drawn coffee cup.

## One-line summary

> **Wavy paths, sloppy corners, round joins, washed fills, dasharray draw-in, Caveat labels — sketch icons are SVG `<path>` elements with deliberately imperfect Bézier control points and stroke-based animation.**
