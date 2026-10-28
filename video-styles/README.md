# Video styles

Code-only visual styles for [HyperFrames](https://github.com/heygen-com/hyperframes) + Claude. Each style has a
**philosophy file** (`STYLE.md`) you hand to Claude together with your script, and a **6-second reference
composition** (`example.html`) that shows the style working.

No AI image or video models: HTML, CSS, SVG, Canvas, Three.js and GSAP only.

## How to use a style
1. Pick a style below and open `styles/NN-name/STYLE.md`.
2. Give Claude the **Prompt for Claude** block from the bottom of that file, plus your script.
3. Claude builds a composition that follows the style's palette, type, motion and don'ts, using `example.html` as
   the structural reference.
4. Render: `./render.sh 04` renders an example into `renders/` (or `npx hyperframes@0.6.6 render . -c styles/04-terminal/example.html -o out.mp4 -w 2`).

Read [`_shared/HYPERFRAMES_RULES.md`](_shared/HYPERFRAMES_RULES.md) once. It covers the rules every style shares
and the techniques that apply everywhere (draw-on strokes, typing Thai, canvas/WebGL timing, seeded randomness).

## Included here (free)
| # | Style | Tech | Best for | Preview |
|---|---|---|---|---|
| 04 | [Terminal](styles/04-terminal/STYLE.md) | css | AI/dev demos, "watch it run" | [mp4](renders/04-terminal.mp4) · [with audio](renders/04-terminal-audio.mp4) |
| 05 | [Blueprint](styles/05-blueprint/STYLE.md) | svg | architectures, "anatomy of X" | [mp4](renders/05-blueprint.mp4) |
| 07 | [Keynote minimal (Premium Dark)](styles/07-keynote-dark/STYLE.md) | css | premium product/tech default | [mp4](renders/07-keynote-dark.mp4) · [with audio](renders/07-keynote-dark-audio.mp4) |
| 13 | [Pixel art 8-bit](styles/13-pixel-8bit/STYLE.md) | canvas | games, counters, nostalgia (keep Thai text large) | [mp4](renders/13-pixel-8bit.mp4) |

## 16 more styles in the community
Editorial collage · Whiteboard marker · Kinetic typography · Newspaper · Retro desktop · Data infographic ·
Corkboard · 3D isometric diorama · Flat vector explainer · Neon synthwave · Sketchbook pencil · Ink brush ·
Watercolor · Paper-craft stop-motion · Manga panels · Thai retro movie poster

Each comes with the same `STYLE.md` + `example.html` pair, ready to drop into `styles/`.
They're in the **Everyday AI Crew** community: [everydaywithcaptain.com/join](https://everydaywithcaptain.com/join) *(coming soon)*.

## Layout
```
styles/NN-name/STYLE.md      philosophy, palette, type, motion, technique, don'ts, prompt
styles/NN-name/example.html  6 s vertical reference (1080x1920)
_shared/                     fonts (OFL), three.js (MIT), shared.css, HYPERFRAMES_RULES.md
                             gsap.min.js is fetched at setup (see the repo's CLAUDE.md), not stored here
_template/STYLE_TEMPLATE.md  template for adding your own style
index.html                   needed by HyperFrames at the project root
render.sh                    renders the examples to renders/
```

## Adding a style
Copy `_template/STYLE_TEMPLATE.md`, build `example.html` first, and write the file *after* the example works: the
"Pitfalls & tips" section is the most valuable part.

## Licences
Fonts: Google Fonts under the SIL Open Font License (`_shared/fonts/OFL.txt`). three.js: MIT (`_shared/THREE_LICENSE`).
GSAP is not redistributed here; it is downloaded from its official npm package under GreenSock's standard
"no charge" licence (https://gsap.com/standard-license).
