# hf-mixer

The audio + cut/trim panel HyperFrames Studio doesn't ship. Works on any hyperframes project.

```bash
export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
node tools/hf-mixer/server.mjs <comp-dir> [--port 3010]
# → http://localhost:3010
```

Run it **alongside** `hyperframes preview` (port 3002). Every edit writes `index.html`;
the studio hot-reloads, so you change a level here and hear it there.

## Why it exists

Studio is a *layout* editor — X/Y/W/H/Layer/Opacity and timeline drag. Searching its
bundle: `Volume` → 0 matches, `Mute` → 0, `Split` → 0. There is no audio control in the
product, and trim exists only as drag handles that become **physically unreachable** once
a clip runs past the composition end (a 154.8s music clip in a 63.5s comp puts its right
handle ~91s outside the visible timeline). That's not user error — it's a gap.

## What it does

| Section | Controls |
|---|---|
| **Audio mixer** | Per-clip volume slider (`data-volume`), **M**ute, **S**olo. Mute stashes the prior level in `data-hf-prevol` so un-mute restores it exactly. Solo mutes every other `<audio>`. |
| **Cut & trim** | Typed `start` / `dur` / `in` (`data-media-start`) fields + read-only `end`. **Fit** clamps duration to the composition end. **Split** cuts a media clip in two at a time you type, advancing `data-media-start` on the second half so the source stays in sync. **✕** deletes. |
| **Visual layers** | Show/hide toggle for A/B decisions (writes `display:none`). |
| **Banners** | Warn on clips running past the composition end (with one-click *Fit all*), hidden layers, and muted clips — the three states that silently ruin a render. |
| **Undo** | 50-deep, in-memory. Restores the file byte-exact. |

## Design notes

- **Surgical edits, no DOM round-trip.** It rewrites only the one attribute on the one tag
  by byte offset. Your hand-authored formatting, SVG casing (`clipPath`), and comments
  survive byte-exact — unlike the studio's writer, which re-serializes the whole file.
- **Scroll never changes a value.** Fields are typed; drag the field's *label* sideways to
  scrub; Arrow keys step (Shift = ×10). Deliberately no wheel handler.
- `data-hf-prevol` / `data-hf-hidden` are bookkeeping attributes the runtime ignores.
  They disappear when you un-mute / un-hide.

## Limits (by design)

Audio **fades, speed, and reverse can't be live** — `data-volume` is a static number, not
an automation curve, and the runtime has no audio graph. Bake those with ffmpeg:

```bash
ffmpeg -i in.mp3 -t 63.5 -af "afade=t=in:st=0:d=0.6,afade=t=out:st=61:d=2.5" out.mp3
```

Delete/split are limited to `<audio>`/`<video>` (visual clips carry scene content and
GSAP timeline references — removing them needs the tweens updated too).
