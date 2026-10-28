# HyperFrames rules every style shares

Read this once; each `STYLE.md` only lists what is specific to its style.

## Contract (HyperFrames 0.6.6, Node 22)
- One composition = one HTML file with a root `.stage` carrying `data-composition-id`, `data-start="0"`, `data-duration`, `data-width`, `data-height`.
- Animation is ONE paused GSAP timeline registered as `window.__timelines["<composition-id>"] = tl`. The renderer seeks it; never use `requestAnimationFrame`, `setTimeout`, CSS animations or video playback for motion.
- Always end the timeline with a duration anchor so the clip length is exact: `tl.to({}, { duration: N }, 0);`
- Render from the pack root (needs `index.html` there): `npx hyperframes@0.6.6 render . -c styles/NN-name/example.html -o out.mp4 -w 2`
- Everything is code: HTML/CSS/SVG/Canvas/Three.js + GSAP. No AI image or video models, no remote assets. Fonts are local (`_shared/fonts/fonts.css`).
- Examples are 1080×1920 vertical, 6 s. For 16:9 (1920×1080) re-lay out the composition; do not just scale. Each STYLE.md has a short 16:9 note.

## Motion law (all styles)
- Every beat has an entrance, a hold with ambient motion, and (once) an emphasis. Nothing is ever frozen: slow drift/zoom on the camera layer, a blink, a breathe.
- Stagger entrances 0.15–0.4 s apart; one idea per beat; the key word/number gets the biggest move.
- Ease with intent: `power3/4.out` slam-ins, `back.out(1.4–2)` pop, `elastic.out(1,.5)` rubber, `steps(n)` for retro, `none` for conveyor/ambient.

## Techniques that bit us (apply everywhere)
1. **SVG draw-on leaves round-cap dots.** Setting `strokeDashoffset = length` still shows a dot with `stroke-linecap: round`. Use `strokeDasharray: "L L+40"` and `strokeDashoffset: L+20`, animate offset → 0. Helper:
   ```js
   document.querySelectorAll(".d").forEach(p => { const L = p.getTotalLength();
     gsap.set(p, { strokeDasharray: `${L} ${L + 40}`, strokeDashoffset: L + 20 }); });
   tl.to(p, { strokeDashoffset: 0, duration: .4, ease: "power1.inOut" }, at);
   ```
2. **Typing Thai:** never reveal per character (vowels/tone marks detach). Reveal the whole line with `clip-path: inset(0 100% 0 0)` → `inset(0 0% 0 0)`; for a typewriter feel use `ease: "steps(n)"` with n ≈ number of visible glyph clusters.
3. **Thai line breaks:** there are no spaces; browsers wrap mid-phrase. Put `<br>` at phrase boundaries yourself and use `white-space: nowrap`.
4. **Canvas / WebGL scenes** (pixel, 3D): drive from a proxy tween, not rAF:
   ```js
   const clock = { t: 0 };
   tl.to(clock, { t: DURATION, duration: DURATION, ease: "none", onUpdate: () => renderAt(clock.t) }, 0);
   renderAt(0);
   ```
   `renderAt(t)` must be a pure function of `t`. Three.js: `setPixelRatio(1)`, `preserveDrawingBuffer: true`.
5. **Canvas text needs the font loaded.** Call `document.fonts.load("700 104px Kanit").then(repaint)`; do not cache bitmaps made before the font is ready.
6. **Randomness must be seeded** (mulberry-style PRNG), or two renders differ.
7. **Grain/paper textures** are inline SVG `feTurbulence` data-URIs (escape `#` as `%23`) layered with `mix-blend-mode: multiply`. Cheap and deterministic.
8. **exFAT drives** write `._*` sidecar files; delete them after renders (`find . -name '._*' -delete`).
9. **Text size:** mobile viewers read at ~1/3 scale. Titles 120–160 px, supporting 60–76 px, microcopy ≥ 24 px, at 1080 wide.
10. **Label pill** (`.label` in `_shared/shared.css`) exists only in the gallery clips. Remove it in real videos.

## Fonts available locally (`_shared/fonts/fonts.css`)
Bai Jamjuree · Bebas Neue · Caveat · Charm · Chonburi · IBM Plex Mono · IBM Plex Sans Thai · Inter · Itim · Kanit · Mali · Mitr · Noto Sans Thai · Pattaya · Permanent Marker · Playfair Display · Press Start 2P · Space Grotesk · Sriracha · Trirong · VT323
(All Google Fonts, SIL OFL.) Adding a font: download woff2 for the `thai` and `latin` subsets and add `@font-face` with `font-display: block`.
