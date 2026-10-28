# EDIT DYNAMICS PHILOSOPHY — Camera moves + graphic variety, mechanically enforced

> **Required reading before planning any edit that includes overlay graphics or
> camera moves.** This file exists because of one observed failure mode: every
> graphic fades in at the same screen position, sits still, fades out — over a
> static camera. "Slide-projector editing." The fix is not taste, it's a
> checklist: a **Dynamics Ledger** filled in before building, validated against
> the **Variety Laws** below. A cheaper model following this file mechanically
> will produce a dynamic edit; a smart model ignoring it will not.
>
> **There is an opposite failure, and it is just as real:** applying the energy
> rules to a video that needed stillness — a restless camera punching on every
> emphasis word in a tutorial. Read **§0.5 first**; it decides which half of
> this file applies. Every rule below about *movement for its own sake* is an
> intro rule.

Companion files: implementation math for base-video camera moves lives in
`RENDER_AND_EXPORT_PHILOSOPHY.md` §7.6 (crop expressions, smoothstep ramps,
punch magnitudes, THE BREATHE RULE). Composition quality rules live in
`MOTION_PHILOSOPHY.md`. This file decides **what happens when and where**.

---

## 0 · The two style packs

Every video declares ONE style pack in the plan, before any graphic is built:

| Pack | File | Look |
|---|---|---|
| **Premium Dark** | `MOTION_PHILOSOPHY.md` | Black canvas, chrome type, light streaks, glass |
| **Vox Editorial** | not included in this repo | Paper, serif, cutouts, highlighter, maps/charts |

If the user hasn't said which, **ask** — it changes every asset. The Variety
Laws in this file apply to both packs.

---

## 0.5 · Video type decides what the camera is FOR (read before §2)

The camera menu in §2 is not a free buffet. **What the camera is allowed to do
depends on what kind of video this is**, and getting this wrong produces an edit
that feels restless and arbitrary even though every individual move is "correct."

| Type | What the camera is for | Sanctioned moves |
|---|---|---|
| **Intro / hook / shorts** | **Energy.** Movement exists to create dynamism and hold attention. Punches land on emphasis words because the *delivery* is the content. | `punch`, `creep`, `whip`, `push` — the full menu |
| **Explainer / tutorial / walkthrough** | **Pointing.** Movement exists to direct the eye to something specific on screen. A move must answer "what am I showing you right now?" | `area-zoom` almost exclusively. `none` is the correct default. |

**The explainer rule (from user feedback, learned on `ghostfont-explain`):**

> Zoom in an explanation video means: *there is information on screen that goes
> with what is being said, so you may zoom into that specific part to highlight
> it.* It does NOT mean zooming in and out to create dynamic like in an intro.

Consequences for explainers:

1. **Every camera move must name the on-screen thing it is pointing at.** Not the
   word being spoken — the *region of the frame*. If the ledger row can't name a
   screen element (a paragraph, a chart, a terminal line, a UI control), there is
   no camera move on that row. "Anchored to a word" is an intro test; it is not
   sufficient here.
2. **`none` is not a defect.** Long stretches of neutral framing are correct and
   normal in an explainer. The energy comes from the graphics assembling, not
   from the frame breathing.
3. **If the screen is static or irrelevant, do almost nothing.** When the source
   is a frozen page, a slide that never changes, or footage unrelated to the
   words, there is nothing to point at — so the honest camera track is close to
   empty. Do not manufacture punches to fill it.
4. Rhythmic emphasis punches in an explainer read as nervous, not energetic.
   The viewer is trying to follow an argument; a frame that keeps lurching
   competes with the thing they're reading.

> **How this was learned:** `ghostfont-explain` shipped with 16 punches anchored
> to emphasis words — correct by every law below, and wrong for the format. The
> source screen was static from 4.2s onward, so the moves pointed at nothing;
> they were pure decoration on a video whose job was to explain a mechanism.
> Law 4 (camera pulse) is what mechanically forced it — that law is now scoped
> to intros only.

---

## 1 · The Dynamics Ledger (mandatory, non-negotiable)

Declare the **video type** (§0.5) on the line above the table — `intro` or
`explainer`. It decides which camera rules apply and is the first thing to get
right; the ledger is not valid without it.

Before building anything, extend the approved cut plan with this table — one
row per beat where *anything* visual happens (graphic, camera move, or both):

| beat | time (out) | what's said | camera | graphic | zone | entrance | exit |
|---|---|---|---|---|---|---|---|
| 1 | 0.0–4.2 | hook line | creep 1.00→1.06 | — | — | — | — |
| 2 | 4.2–6.0 | "three tools" | punch 1.18 on "three" | 3 chips | MR | slide-from-right | shrink-to-chip |
| 3 | 6.0–9.5 | tool #1 detail | none (return to 1.0) | glass card | TL | glass materialize | shatter |
| … | | | | | | | |

*(That example is an `intro` ledger — note the punches. An `explainer` ledger's
camera column is mostly `none`, with `area-zoom` rows that each name the
on-screen region being pointed at, e.g. `area-zoom -> the pricing table`.)*

Then **run the Variety Laws (§5) against the table as a mechanical check**
before writing any code. If two consecutive rows violate a law, change one of
them. Present the ledger together with the cut strategy for user approval —
it costs 20 lines of markdown and prevents the entire failure mode.

Column vocabularies come from §2 (camera), §3 (zone), §4 (entrance/exit).
Use the exact names so the law check is string comparison, not judgment.

---

## 2 · Camera move menu

All implemented per §7.6 of the render philosophy (eased crop expressions,
same-length clip, overlays composite on top in final coords).

| Move | Name in ledger | What it feels like | Parameters | Rule |
|---|---|---|---|---|
| **Punch-in** | `punch Z` | Emphasis hit on one word | 1.08–1.22, in ~0.4s, hold 0.5–1s, return to 1.0 | **Intro/shorts only** (§0.5). Anchor to the exact word. Return always. |
| **Creep zoom** | `creep A→B` | Slow tension build (hooks, intros, storytelling) — **intro/shorts only** (§0.5) | 1.00→1.06/1.08 over 4–8s, `ease: none` or gentle | Must END in a hard cut or a return — never park, never chain two creeps. This is the only sanctioned slow constant zoom; see [[camera-zoom-breathe-rule]]. |
| **Zoom-to-area** | `area-zoom` | "Look at THIS part" — push into a region (screen recording, object, side of frame) while a graphic annotates it | Z up to 1.5 on non-face regions; keep faces ≥ 1.22 only briefly | **The explainer's default and near-only move** (§0.5). Graphic must track the region — coordinate math in §6.1. Ledger row must name the screen element. |
| **Push-aside** | `push BX` | Subject slides over to make room | Momentary only; returns with the punch | See §7.6 — try zones at Z=1.0 first. |
| **Lateral pan** | `pan L`/`pan R` | Camera TRAVELS to the next graphic without changing zoom | Re-anchor the crop window over 0.5–0.7s at constant Z | **The correct transition between two consecutive graphic beats** — see §2.1. Never zoom out and back in to change sides. |
| **Whip pan** | `whip` | Violent reframe between two framings, blur hides the cut | 0.25–0.35s, directional blur overlay at peak | Hero move — max 2 per video. |
| **Frame-in-frame** | `pip` | Whole video shrinks into a rounded glass card, freeing the canvas for a big graphic | Scale to 0.55–0.65, slide to one side, border-radius 24px, return after the graphic's beat | Hero move — max 1–2 per video. Recipe §6.2. |
| **Freeze + takeover** | `freeze` | Frame freezes, desaturates/dims, graphics annotate ON the frozen frame | 1–2.5s, then resume | Great for "let me break this down." Max 2 per video. |
| **None** | `none` | Baseline 1.0 framing | — | Intros: fine, but not >~10s straight (Law 4). **Explainers: this is the correct default**, for as long as there is nothing on screen to point at. |

### 2.1 · Travel between graphics — do NOT bounce through neutral

When two graphic beats sit on opposite sides of the frame, the naive track is
`zoom in right -> return to 1.0 -> zoom in left`. **That reads as a twitch, not
a move**, and the return serves nothing: the viewer is shown a neutral frame for
half a second on the way to somewhere else.

> User feedback, verbatim, on `horizons-intro` v1: *"when transition to #2, you
> zoom out back to normal first, then zoom in again, which is not good, thats too
> quick and not helpful… instead of zoom out and zoom in, dont zoom out yet, just
> move camera to the left to emphasize #2 graphic."*

The rule: **commit to the graphic, then travel.**

1. Zoom in ONCE and **hold** while a graphic is on screen. Either park the zoom
   or let it creep slowly (a creep across a beat that is *building* — a list
   filling in, chips stacking — is the better of the two).
2. To reach a graphic on the other side, **pan at constant zoom** (`pan L`/`pan R`).
3. Return to 1.0 only at a real story point — the end of a section, or a hero
   beat that wants the full frame — and then **hold it there**.
4. A whole beat is allowed to be one slow continuous move (`1.0 -> 1.18` across
   6s as five chips land). Constant motion in one direction reads as intent;
   in-out-in-out reads as nerves.

This applies to **intros too** — it is not the explainer rule from §0.5. §0.5
decides *whether* the camera moves for energy; this decides *how* it gets from
one graphic to the next once it does.

**Implementation:** a single anchor ramp `A(t)` (0 = left-anchored, 1 = right-
anchored) alongside the zoom ramp — see `RENDER_AND_EXPORT_PHILOSOPHY.md` §7.6.
`A` is only visible while `Z > 1`, so park any bookkeeping flip where `Z = 1.0`.
Panning also *creates* margin: at Z 1.18 left-anchored, a centred subject shifts
right by ~350px, which is what makes a narrow side margin usable at all.

### 2.2 · A worked camera track (copy this shape)

`horizons-intro` — 29s sponsor intro, centred presenter, graphics living in the
narrow side margins. This is the shape a graphic-heavy intro should have. Note
there are only **four** moves for eight graphic beats, and the frame is never
zoomed without a graphic to justify it.

| beat | graphic zone | camera | zoom |
|---|---|---|---|
| 1 | right | zoom in, right-anchored, **hold** | 1.00 → 1.18 |
| 1→2 | — | **`pan L`** — no zoom-out | holds 1.18 |
| 2 | left | slow creep as 5 list rows land | 1.18 → 1.26 |
| 2→3 | — | zoom back to neutral | 1.26 → 1.00 |
| 3 | top-right | `none`, held | 1.00 |
| 4 | right | **constant zoom in** as 5 chips stack | 1.00 → 1.18 |
| 4→5 | — | **`pan L`** — no zoom-out | holds 1.18 |
| 5 | left | held | 1.18 |
| 5→6 | — | **`pan R`** — no zoom-out | holds 1.18 |
| 6 | right | **constant zoom out** through the converge | 1.18 → 1.00 |
| 7 (hero) | right | `none`, held — stillness lands the logo | 1.00 |
| 8 (CTA) | left + right | `none`, held | 1.00 |

Three things worth stealing:

1. **A whole beat can be one continuous move.** Beats 2, 4 and 6 are each a
   single slow ramp that runs the length of the beat, timed so it *finishes* as
   the beat's content completes. A build (list filling, chips stacking) pairs
   naturally with a push in; a resolution (elements converging) pairs with a pull
   out. Constant motion in one direction reads as intent.
2. **The hero beat is the one with NO camera move.** Everything before it moves,
   so stillness is what makes the logo land (MOTION_PHILOSOPHY Law 9).
3. **Returning to 1.0 for the last beats is also a correctness win**, not just a
   look: any graphic that must align to something *in the footage* (an arrow
   pointing at a prop, a callout on a UI element) can then use exact measured
   pixel coordinates instead of chasing a moving target.

---

## 3 · Placement zones (stop centering everything)

Divide the frame into a 3×3 grid. Ledger `zone` values:

```
TL  TC  TR
ML   C  MR
BL  BC  BR
```

- For a centered talking head, **TL / TR / ML / MR** are usually free at
  Z = 1.0. **TC** works for titles; **BC** is reserved for captions.
- **`C` is banned for informational graphics** while the speaker is visible —
  center is only for full-takeover beats (freeze, pip, chapter cards).
- Before locking the ledger, composite one probe frame per graphic beat over
  the base at Z=1.0 and check for subject overlap (this is the §7.6 rule).

---

## 4 · Entrance / exit catalog

`entrance` and `exit` values for the ledger. Family is the bold name.

| Family | GSAP sketch | Feels like |
|---|---|---|
| **rise-blur** | `from { y: 40, opacity: 0, filter: blur(12px) } power3.out 0.5s` | Default premium enter |
| **slide-edge** | `from { x: ±80, opacity: 0 } power3.out 0.4s` — always from the NEAREST edge to its zone | Directional energy |
| **scale-pop** | `from { scale: 0.7, opacity: 0 } back.out(1.6) 0.45s` | Playful, chips/badges |
| **draw-on** | SVG `stroke-dashoffset` → 0, 0.5–0.8s | Hand-made (Vox pack) |
| **glass-materialize** | `from { scale: 0.92, opacity: 0, filter: blur(14px) } back.out(1.3) 0.6s` + specular sweep 0.3s later | Liquid-glass panels |
| **wipe-mask** | `clip-path: inset()` tween, 0.35s | Documents, screenshots |
| **counter-run** | number rolls from 0 via proxy tween | Stats |
| **shatter** *(exit)* | card splits into 8–12 clip-path shards flying outward — recipe §6.3 | Hero exit, max 1/video |
| **shrink-to-chip** *(exit)* | graphic scales to 0.35 and docks in a corner, STAYS as a persistent chip | Recap elements |
| **whip-out** *(exit)* | `to { x: ±300, filter: blur(20px) } power2.in 0.3s` | Matches whip cuts |
| **dissolve-down** *(exit)* | `to { y: 20, opacity: 0, filter: blur(8px) } 0.35s` | Quiet default exit |

Never use plain `opacity` fade with no transform — that's the
slide-projector move (MOTION_PHILOSOPHY anti-pattern #1).

---

## 5 · The Variety Laws (check these against the ledger, row by row)

1. **Zone rotation.** Two consecutive graphic beats may not share a `zone`.
2. **Entrance rotation.** Two consecutive graphic beats may not share an
   entrance family. Across the whole video, no family more than 3 times
   (persistent chips exempt).
3. **Exit ≠ entrance mirror by default.** At most half the graphics may exit
   as the exact reverse of their entrance.
4. **Camera pulse — INTROS / HOOKS / SHORTS ONLY.** No stretch of talking head
   longer than ~10s with `camera: none` on every row. Something moves — a punch,
   a creep, a graphic-anchored area-zoom.
   **This law does NOT apply to explainers/tutorials** (§0.5). There, `camera:
   none` for 30s straight is fine, and inventing a punch to satisfy this law is
   itself the defect. Applying this law to an explainer is what broke
   `ghostfont-explain`.
5. **No identical consecutive camera events.** Two punches in a row must
   differ in magnitude or target word emphasis; a creep is never followed by
   another creep.
6. **THE BREATHE RULE** (from §7.6, memorized in [[camera-zoom-breathe-rule]]):
   punches return to 1.0; creeps end in a cut; never park zoomed.
7. **Hero moves are near-singletons.** `shatter`, `pip`, `whip`, `freeze`:
   max 1–2 uses each per video. A repeated hero move is no longer a hero move.
8. **Every camera move anchors to a word** *(intros)* **or to an on-screen
   region** *(explainers — the stricter test, see §0.5)*. If the ledger row's
   `camera` cell is filled but "what's said" doesn't name the anchor word — or,
   in an explainer, the row doesn't name the screen element being pointed at —
   the row is invalid.
9. **Graphics react to speech, never invent it.** Ledger content comes from
   the transcript (CLAUDE.md pipeline rule). No guessed recap chips.

A ledger that passes all nine laws will not produce a static edit. That is
the entire point of this file.

---

## 6 · Recipes for the marquee techniques

### 6.1 Zoom-to-area with a tracking graphic

The base zoom is a crop `(crop_x(t), crop_y(t), Z(t))` per §7.6. A graphic
anchored to source pixel `(sx, sy)` must be positioned in OUTPUT coords:

```
ox(t) = (sx − crop_x(t)) · Z(t)
oy(t) = (sy − crop_y(t)) · Z(t)
```

Generate `ox/oy` keyframes from the **same smoothstep helper** that generated
the crop expression, and mirror them as GSAP tweens on the overlay element
(same timing, same ease). If the graphic annotates the area only while zoomed,
enter it AFTER the zoom settles (+0.15s) and exit BEFORE the return starts.

### 6.2 Frame-in-frame (speaker resize) — build it in hyperframes, not ffmpeg

ffmpeg can't animate a scale over time cleanly; hyperframes can. Put the
beat's base-cut segment in a composition as a `<video muted>` layer and
animate the wrapper:

```html
<div class="pip-wrap"><video src="../edit/segments/seg07.mp4" muted></video></div>
```
```js
// full-bleed → glass card at left, graphic enters MR zone
tl.to('.pip-wrap', { scale: 0.6, x: -420, borderRadius: 24,
     boxShadow: '0 20px 60px rgba(0,0,0,.5)', duration: 0.6,
     ease: 'power3.inOut' }, T_IN);
tl.to('.pip-wrap', { scale: 1, x: 0, borderRadius: 0, duration: 0.6,
     ease: 'power3.inOut' }, T_OUT);   // ALWAYS return to full-bleed
```

Render **opaque** (the video fills the frame at the ends — no alpha needed).
Delivery: Mode B → an opaque `.mov`/`.mp4` clip dropped on V2 over its window;
Mode A → overlay with `enable='between(t,a,b)'` over the base (audio always
from the base track; the comp's video stays muted).

### 6.3 Liquid-glass panel: materialize in, shatter out

Enter with `glass-materialize` (§4) on a `.glass` card built per
MOTION_PHILOSOPHY §5.5 (opacity tier chosen by backdrop complexity).
Add a specular sweep: a rotated white gradient bar tweened `x: -120% → 220%`,
0.45s, `power2.inOut`, 0.3s after landing.

Shatter exit — pre-split the card into shards at build time (no runtime
randomness — determinism rule):

```html
<div class="card">…content…</div>
<div class="shards" aria-hidden="true">   <!-- 12 clones of the card visual -->
  <div class="shard s1"></div> … <div class="shard s12"></div>
</div>
```
```css
/* each shard is the full card with a different clip-path polygon —
   generate 12 irregular triangles/quads covering the card once, hardcode them */
.shard { position: absolute; inset: 0; clip-path: polygon(…); }
```
```js
tl.set('.card',   { opacity: 0 }, T_BREAK);
tl.set('.shards', { opacity: 1 }, T_BREAK);
tl.to('.shard', {
  x: i => 60 * Math.sin(i * 2.4),  y: i => 40 * Math.cos(i * 1.7) + 30,
  rotation: i => 25 * Math.sin(i * 3.1),
  opacity: 0, filter: 'blur(6px)',
  duration: 0.55, ease: 'power2.in',
  stagger: { each: 0.02, from: 'center' }
}, T_BREAK);
```

(Harmonic sin/cos hashes, not `Math.random()` — renders must be
deterministic.) Max once per video. Pairs beautifully with a cut on the
last shard frame.

### 6.4 Creep zoom (the "slowly constantly zoom in" look)

```
keyframes: (t_start, 1.00) → (t_end, 1.06)      # 4–8s span, ease: none
```

Rules: amplitude ≤ 1.08; the beat AFTER the creep starts at 1.00 via a hard
cut (the cut IS the reset — that contrast is what makes the creep readable);
use on hooks, story beats, and quiet tension, not on information-dense beats
where punches do the work.

### 6.5 Meta zoom-out to the description (sponsor `pip`, hero move, max 1)

Built on `horizons-code`. The frame pulls back to reveal it is playing inside a
video-platform watch page — *the page the viewer is on* — the description
expands, a cursor clicks the sponsor link, and **the click cuts to the link's
destination**. It removes the "where do I click" gap entirely, which is why it
converts: most viewers have never opened a description, so the motion has to be
shown, not described.

**Build it as ONE opaque composition, with the base clip embedded** (§6.2's
`<video>` recipe). Do not try to keep an ffmpeg-scaled video registered to a
hole in an alpha overlay — that is two systems agreeing frame by frame, and it
will drift. Structure:

```
#stage    the camera — one transform for the whole scene
  #page   the watch-page mock, STATIC, never transformed
  #pip    non-timed wrapper around <video>; starts at scale 1, full frame
  #cursor above both
#loadbar  OUTSIDE #stage — browser chrome, must not inherit the camera
#veil
```

Five things that are load-bearing:

1. **`#pip` starts full-frame and covers the page entirely, so the pull-back
   IS the reveal.** No fade, no hole, nothing to keep registered.
2. **Put a black plate under the player, 2px proud on every side.** Any
   sub-pixel edge on the scaled video then lands on black, not on page grey.
3. **Do NOT scroll the page — expand the description.** Scrolling to reach the
   description decapitates the speaker while he is still talking. Expanding the
   collapsed box is real platform behaviour, keeps him fully visible, and means
   the video never moves after the pull-back.
4. **Two clicks, not one:** "…more", then the link. The first click is the gap
   you are actually closing.
5. **Anything that is browser chrome (load bar, veil) lives outside the camera
   group**, or a push with a low transform-origin throws it off frame.

Anchor the beats to words, not to a stopwatch. On `horizons-code` the sentence
"ก็สามารถกดลิงก์จากใน **Description** **ตรงนี้** ได้เลย" supplied all of them:
pull-back on "click the link", expand on "Description", click on "ตรงนี้"
(*right here*). If the line does not contain those beats, this is the wrong
technique for it.

**The exit is the payoff, not a transition.** Cut on the click to footage of
that link loading. If you have a screen recording of the URL, cut into it just
before it resolves — the click then *causes* the next shot instead of merely
preceding it.

---

## 7 · Anti-patterns

- ❌ **All graphics in the same zone.** The #1 cheap-model tell. The ledger
  check exists precisely for this.
- ❌ **Opacity-only entrances.** Always at least one transform channel.
- ❌ **Camera move with no word anchor.** Motion without meaning reads as jitter.
- ❌ **Hero move spam.** Four shatters = zero shatters.
- ❌ **Skipping the ledger because the edit is "simple".** Three graphics
  placed identically is exactly how simple edits go static.
- ❌ **Chained or parked creeps.** See Law 6.
- ❌ **Building graphics before the ledger is approved.** Ledger rides along
  with the cut-strategy approval — one approval, both tables.

---

## 8 · One-line summary

> **Fill the ledger, pass the nine laws, anchor every move to a word, rotate
> zones and entrances, spend hero moves once, and always come home to 1.0.**
