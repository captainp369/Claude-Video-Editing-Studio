# RENDER & EXPORT PHILOSOPHY — How this studio hands work back to you

> Required reading before any render or composite step. Defines the two delivery
> modes, when each is the right call, the wall-time you should expect, and the
> question the agent must always ask before kicking off a long render.

---

## 0 · The non-negotiable rule

> **Before any render that produces a deliverable, the agent MUST ask the user
> which mode they want and quote the time estimate.**

Never silently default. Both modes are valid; the wrong one wastes hours.

---

## 1 · The two modes

### Mode A — Full composite (`final.mp4`)

The studio renders **everything**: trimmed base + motion-graphics overlay + face-crop transitions + (optional) burned subtitles, all baked into a single H.264 MP4 ready to upload.

```
sources → trim → base.mp4 → render overlay.mov → ffmpeg composite → final.mp4
```

**You get one file.** No NLE needed. Upload-ready.

### Mode B — Layered handoff (separate files for an NLE)

The studio renders the **base cut** and the **motion-graphics overlays** as separate assets. You composite in Premiere / Resolve / FCP at the timeline level — drop the base on V1, overlays on V2, scrub freely.

```
sources → trim → base.mp4 + render overlay.mov  → handoff
                                                  ↓
                                        you composite in NLE
```

**You get a folder of assets.** Real-time preview, free iteration, your color/audio decisions live in your NLE.

---

## 2 · When to pick which

| Situation | Mode | Why |
|---|---|---|
| Short-form (<2 min): intro, hook, social cut, end card | **A — Full composite** | Composite cost is small; one-file convenience wins |
| Long-form (>10 min) | **B — Handoff** | Full composite scales poorly; NLE preview is real-time |
| You'll iterate on card timings or fonts after the first render | **B — Handoff** | NLE drag-edit > re-running 30 min of ffmpeg |
| You want to add B-roll, music ducking, cutaways | **B — Handoff** | Audio/B-roll judgment lives in the NLE |
| Hand-off to a teammate without an NLE | **A — Full composite** | Universal MP4, no setup |
| The motion graphics cover < 30% of the video duration | **B — Handoff** | Don't render alpha frames over an hour of nothing |
| You're producing for an automated pipeline (CI, scheduled cron, social autoposter) | **A — Full composite** | Single artifact, deterministic, no human in the loop |

**Default if the user is unsure:** Mode B. It loses you nothing (you can always run Mode A's composite step later) and saves the most painful 30+ minutes of iteration.

---

## 3 · Wall-time you should quote

These are real measurements from this workspace (1080p @ 24fps, on an external exFAT drive, M-series Mac). Internal SSD gets ~2–4× faster on the composite step.

| Step | Wall time | Scales with |
|---|---|---|
| Transcribe (ElevenLabs Scribe) | ~10s per minute of audio | source duration |
| Pack transcripts | <1s | constant |
| Render base cut (`render.py`) | ~1 min per minute of OUTPUT | output duration |
| Hyperframes overlay render | **2–4 min per minute of overlay** | overlay duration only |
| ffmpeg composite | **~30 min per minute of output** (exFAT) / **~6–10 min** (SSD) | output duration |

### Mode A (full composite) total time

```
T_A ≈ T_transcribe + T_basecut + T_overlay + T_composite
    ≈ (0.2 × in)  +  (1 × out)  +  (3 × ovl)  +  (15–30 × out)
```

Where `in` = input duration, `out` = output duration, `ovl` = overlay duration.

### Mode B (handoff) total time

```
T_B ≈ T_transcribe + T_basecut + T_overlay
    ≈ (0.2 × in)  +  (1 × out)  +  (3 × ovl)
```

`T_B` is **~10–30× faster than `T_A`** for any output longer than a few minutes. The composite step is the dominant cost in Mode A.

### Examples (rough, exFAT external drive)

| Output length | Overlay length | Mode A total | Mode B total | Difference |
|---|---|---|---|---|
| 0:37 (intro) | 0:37 | ~35 min | ~5 min | 30 min |
| 5:00 | 0:30 | ~2.5 hours | ~10 min | 2 hours saved |
| 30:00 | 2:00 | ~16 hours | ~35 min | most of a day saved |
| 60:00 | 5:00 | ~32 hours | ~75 min | not viable in Mode A |

For anything over ~5 min of output, Mode A becomes hostile to iteration.

---

## 4 · The script the agent should run

Before any render, the agent says (in plain language, replacing the bracketed values):

> The cut is ready: **[X] minutes** of output, **[Y] seconds** of motion graphics planned. Two options:
>
> **A. Full composite — single `final.mp4`.** Estimated wall time: **~[T_A]**.
> **B. Layered handoff — `final_basecut.mp4` + `overlay_*.mov` you composite in your NLE.** Estimated wall time: **~[T_B]** (saves ~[T_A − T_B]).
>
> Which one?

Do not start rendering until the user picks.

If they pick B, the deliverables are:

```
edit/
  final_basecut.mp4              # H.264, loudness-normalized, ready for V1
  overlays/
    <segment>_<start>-<end>.mov  # ProRes 4444 alpha, drop on V2 at <start>
  edl.json                       # for re-deriving timing
  transcripts/<source>.json      # for re-deriving subs / karaoke
  master.srt                     # if subtitles were authored
```

If they pick A, the deliverable is:

```
edit/
  final.mp4
```

Plus the intermediates above, kept around for re-runs.

---

## 5 · Format conventions for handoff (Mode B)

| Asset | Codec | Container | Notes |
|---|---|---|---|
| Base cut | H.264 yuv420p, CRF 18 | `.mp4` | Universal NLE import |
| Motion-graphics overlay | **ProRes 4444 yuva444p12le** | `.mov` | Native alpha in every major NLE |
| Subtitles | SRT (UTF-8) | `.srt` | Track in NLE OR burn at export |
| Audio | AAC 48k stereo passthrough from base | `.mp4` (in base) | Never re-encoded |

**Avoid** WebM VP9 alpha for handoff — it's smaller but Premiere and FCP need a transcode step on import. Resolve handles it natively, but the universal choice is ProRes 4444.

---

## 6 · For long videos: render only what changes

Don't render a 60-minute `overlay_full.mov`. Most of that file is empty alpha and Puppeteer would still capture every frame.

**Right approach** for a 60-minute video with motion graphics on:

```
0:00–0:37   → intro mograph
14:30–14:38 → lower-third name card
59:20–60:00 → end card
```

Render three short overlay clips (`intro.mov`, `lower_third.mov`, `end_card.mov`), each only as long as its window. Place them at the right offsets in your NLE. Total overlay-render wall time: ~3 min instead of ~3 hours.

The `data-start` and `data-duration` on each composition root determine the overlay's own internal timeline; the NLE handles where to drop it on the master timeline.

---

## 7 · Anti-patterns

- ❌ Defaulting to Mode A "to be safe." If the output is over a few minutes, Mode A is the unsafe choice — slow, hard to iterate.
- ❌ Rendering an overlay longer than the actual motion-graphics windows. Render only the seconds where something is on screen.
- ❌ Picking Mode A for anything you're not 100% sure is final. The first composite always reveals one more nudge to make.
- ❌ Re-rendering the base cut to fix a card timing. The base cut is locked once approved. Card timing is a Mode B (or hyperframes-only) iteration.
- ❌ Quoting "fast" without numbers. Always give a real estimate.

---

## 7.5 · Verification & re-render gotchas (learned the hard way)

Two traps that produce **false conclusions** when iterating on an alpha overlay. Both wasted a full re-render before being caught.

### A. Input-seek lies on ProRes 4444 alpha — verify with output-seek

`ffmpeg -ss <t> -i overlay.mov …` (seek **before** `-i`) does a demuxer/keyframe seek and can land on a **blank or wrong frame** for ProRes 4444 `.mov`. You'll see graphics "missing" at a timestamp where they're actually present — a phantom bug. It bit us verifying a fast (~1s) fly-in beat: input-seek showed blank frames mid-animation; the overlay was fine.

**Rule:** to spot-check an alpha overlay at time `t`, use **output-seek** (put `-ss <t>` *after* the `-i`), or composite-then-extract (the composite decodes every frame, so it's frame-accurate):
```bash
# WRONG for spot-checks — can show false blanks on ProRes 4444:
ffmpeg -ss 79.1 -i overlay.mov -frames:v 1 out.jpg
# RIGHT — accurate frame:
ffmpeg -f lavfi -i color=c=0x222428:s=1920x1080:d=1 -i overlay.mov \
  -filter_complex "[0:v][1:v]overlay" -ss 79.1 -frames:v 1 out.jpg
```
The final Mode A composite is always frame-accurate regardless — only the *verification* shortcut is the liar. If a beat looks broken at one timestamp but fine at neighbors, suspect the seek before suspecting the composition.

### B. Re-rendering to an existing path: a "wait for file" loop exits on the STALE file

When you render a second time to the **same** output path (`overlay_full.mov` already exists from the first pass), a "wait until the file exists and stopped changing" loop is satisfied **instantly by the old file** — so you proceed to verify a stale render and conclude your edits "didn't apply."

**Rule:** before a re-render, **`rm -f` the target first**, and/or gate the wait on the *render process completing* (run it in the foreground or wait on its task id) rather than on file mtime. A clean signal that the new render landed: the file size/duration changes and the lint/edit you made is visibly reflected.

---

## 7.5a · `gsap.set()` OUTSIDE the timeline does not survive the renderer

**Symptom:** past some point in a long composition, **every beat is on screen at
once**, at mixed opacities, and never clears. Lint is clean. The probe render is
clean. Only the full render is wrong.

**Cause:** `gsap.set(...)` at construction is a **one-shot DOM write at page
load** — it is not an event on the timeline. The capture engine seeks a *paused*
timeline, and its workers **do not seek in frame order**. Once any worker has
rendered a late frame, every `tl.set(sel, {opacity: 1}, t)` has fired, and there
is nothing in the timeline for GSAP to rewind them to when that same worker
seeks back to an earlier frame. The beats stay on.

This is why the probe render cannot catch it: the probe drives `tl.time()`
explicitly from a single page, so it never exercises the out-of-order seek.

**Two more shapes of the same fault, both worse because they fail silently:**

- **A plain `to()` captures its START lazily** — on whatever frame that worker
  rendered first. If that was a late frame, the tween becomes a no-op.
- **A RELATIVE value (`y: "-=117"`) is computed from that arbitrary state.** It
  can resolve to 0, or to −240. This is the one that broke the meta pull-back on
  `aibuilder-thanks`: the shot stayed full-frame for most of the segment and
  flicked to the pulled-back page for a frame here and there.

**Rule: every initial state goes INSIDE the timeline at t=0, and every tween is
an explicit `fromTo` with ABSOLUTE values.** Never `"+="`/`"-="` in a
composition the engine will seek.

```js
// WRONG — a DOM write, invisible to the timeline
gsap.set(BEATS, { opacity: 0 });
gsap.set(["#r1","#r2"], { opacity: 0 });

// RIGHT — timeline-owned, resolves for any seek in either direction
tl.set(BEATS, { opacity: 0 }, 0);
tl.set(["#r1","#r2"], { opacity: 0 }, 0);
```

This generalises the SKILL's rule 10 ("use `tl.set(selector, vars, timePosition)`
inside the timeline"): it is not only about clip elements that do not exist at
page load — it is about *all* authored state.

**It is intermittent, which makes it dangerous.** `aibuilder-intro` (947 frames)
carries the same pattern and rendered correctly; `aibuilder-thanks` (1707 frames)
did not. Length and worker count decide whether you see it. Do not conclude a
composition is safe because it rendered once.

**How to check an existing render:** extract a frame from the back half onto a
flat background and count the beats. One beat should be visible, plus whatever
you deliberately made persistent.

```bash
ffmpeg -y -f lavfi -i color=c=0x2a2f3a:s=1920x1080:d=1 -i overlay_full.mov \
  -filter_complex "[1:v]trim=start_frame=1140:end_frame=1141,setpts=PTS-STARTPTS[o];\
                   [0:v][o]overlay=0:0:format=auto[v]" -map "[v]" -frames:v 1 chk.png
```

## 7.5c · The renderer is NON-DETERMINISTIC when a `<video>` is in the composition

**Measured on `aibuilder-thanks/meta`: the same unchanged file rendered correctly
twice and incorrectly once, back to back.** In the bad run the `#pip` wrapper's
transform simply never applied — the shot stayed full-frame for the whole
segment instead of pulling back into the page.

The tell is wall time: the broken run took **1m28s**, the good runs **17s** and
**23s**. A 5× spread on identical work points at the `<video>` element stalling
on seek/decode while workers snapshot around it.

Fixing the timeline does not fix this. §7.5a's rules (timeline-owned state,
absolute `fromTo`) were already applied to that file; they removed one failure
mode and left this one. Lint passes. The probe render passes. Only the finished
file tells the truth.

**So gate it.** Write a check that proves the effect actually happened, and make
the render retry until it does:

```python
# verify_meta.py — once #pip has shrunk to the player rect, the page's own dark
# gutter at x 1528..1538 is exposed. While the pip is still full-frame that
# strip is video (luma ~130). Dark strip == pull-back landed.
vals = [frame(n)[300:700, 1528:1538].mean() for n in (21, 45, 70, 100)]
sys.exit(0 if max(vals) < 40 else 1)
```

```bash
for attempt in 1 2 3 4 5; do
  rm -f renders/meta.mp4
  npx hyperframes render --fps 30 --output renders/meta.mp4
  python3 verify_meta.py && exit 0
done
exit 1     # never composite from an unverified render
```

Call the same check at the top of the composite so a bad render cannot reach the
deliverable. **Pick a probe region whose value is unambiguous** — a strip that is
page in the good case and video in the bad case — not a general "does it look
right" heuristic.

**Retrying is a stopgap, and it ran out.** On the next edit to that file all five
attempts failed, with the probe flickering *frame to frame within a single
render* (f21 wrong, f45 right, f70 wrong) — each worker carrying its own DOM
state. At that point stop gambling and take the `<video>` out of the composition:

- render the page **opaque, with a flat plate where the clip goes**;
- composite the clip in ffmpeg with `scale=w='…':h='…':eval=frame` feeding an
  `overlay=x='…':y='…':eval=frame`, driven by the same measured numbers;
- `enable='lt(t,T)'` to drop the clip before anything that must sit above it.

Two things move into your lap when you do this, and both bit on the first pass:

- **Anything that must appear ABOVE the clip can no longer live in the comp.**
  The cursor's path had to move out of the player rect (it now runs down the
  sidebar), and the browser load bar was cut entirely — it sat at y 0–7, which
  the clip covers.
- **Anything the comp scrolls, the ffmpeg layer must scroll too.** The page
  scrolled 123px and the clip did not follow, so the player sat still while the
  page slid up underneath it and covered the description. Same "two halves of one
  number" trap as a composited logotype: change both or neither.

**Write the gate against the thing that broke, and make it RELATIVE.** Sampling a
background patch and hoping is not a test — two versions of this check gave false
failures, one because the patch contained the video title, one because it
contained the description text. Measure the clip's own edge instead:

```python
band = g[300:1080, 1440:1520].mean(axis=1)   # a column where the page is EMPTY
rows = np.where(band > 60)[0]                # lowest bright row = the clip's bottom
```
```
pull-back failed   -> ~1079 (clip fills the frame)
pull-back OK       ->  ~860
scroll not tracked -> stays ~860 after the scroll
scroll tracked     -> drops ~130 to ~720
```
Assert `860 ± 65` for the pull-back and `moved >= 100px` for the scroll — relative,
because the exact reading drifts 10–20px with whatever the clip happens to be
showing at its own bottom edge.

---

## 7.5b · THE PROBE RENDER — verify N moments in one ~20s render

**Use this before every full overlay render.** Tool: `tools/probe_render.py`.

The browser preview cannot verify these compositions. It was tried three ways
on `horizons-thanks` and failed all three: pages are served as `data:` URLs so
relative assets break; a local `http.server` is sandboxed off `/Volumes`
(`PermissionError` on `os.getcwd()`); and self-contained base64 pages hit the
8-tab cap, then had their data URIs stripped outright.

But the preview is also the **wrong oracle** even when it works, for the reason
in [[measure-base-luma-before-styling-text]]: it cannot show you how a graphic
sits against real footage luma, and it does not exercise the actual render path
(font embedding, gradient clipping, `filter` support, `clip-path`).

So don't preview — **render, but only the frames you care about.** The script
copies the composition, overrides `data-duration`, and replaces the two-line
timeline registration with an outer timeline that hand-seeks the real one:

```js
const __CK = [1.2, 3.0, 4.0, …], __STEP = 0.2;
const __outer = gsap.timeline({ paused: true });
const __proxy = { i: 0 };
__outer.to(__proxy, { i: __CK.length, duration: __CK.length * __STEP, ease: "none",
  onUpdate: () => tl.time(__CK[Math.min(__CK.length - 1, Math.floor(__proxy.i))]) }, 0);
window.__timelines["main"] = __outer;
```

Each checkpoint is held for `__STEP`, so frame `i*fps*step + 3` is checkpoint
`i`. With `--base FOOTAGE [--base-offset T]` each probe frame is composited
onto the footage frame it will really sit on — which is the entire point.

```bash
python3 tools/probe_render.py COMP_DIR OUT_DIR \
  --checkpoints 0.9,1.25,1.7,2.4,3.0,3.7,4.6,5.1,5.6,6.7 \
  --alpha --base raw_media/clip.mov [--base-offset 3.30]
```

**~20s for 10 checkpoints**, versus minutes for a full render plus a composite.

Two implementation notes that are load-bearing:
- Build the harness string with `.replace()`, **not** `str.format()` — it is
  JavaScript, and every brace would have to be doubled.
- Clean up with `rm -rf`, **not** `shutil.rmtree` — this repo lives on exFAT,
  which materialises AppleDouble `._` sidecars that make `rmtree` die mid-walk.

**What it has actually caught**, across two videos, all before a single full
render was spent: a `fromTo` whose default `immediateRender` painted a solid
accent slab over a coupon from frame 0; a 486×470 panel sitting near-empty for
1.8s; a callout ring still circling an address bar two frames before the URL
under it changed; a browser load bar thrown off-frame by a camera push it was
nested inside; invisible grey-on-grey line art; an X-strike painted *under* the
boxes it was meant to cross; and a docked ribbon whose right edge ran 50px past
the canvas.

---

## 7.6 · Camera moves on the base video (zoom / push-aside)

> **FIRST: read `EDIT_DYNAMICS_PHILOSOPHY.md` §0.5 to decide whether this section
> applies at all.** The magnitudes and rhythms below are for **intros / hooks /
> shorts**, where the camera exists to create energy. In an **explainer or
> tutorial** the camera exists only to POINT at on-screen information, so the
> correct track is mostly `none` plus a few `area-zoom` moves onto specific
> regions — and if the screen is static or unrelated to the words, there is
> nothing to point at and you should add essentially no camera at all. Do not
> apply the punch cadence below to an explainer; that is a known past mistake
> (`ghostfont-explain`).

When the user invites editing the footage itself — punch-in zooms, "play with space"
(push the talking head aside to free room for a graphic), filters — do it in ffmpeg with
an eased **`zoompan`** expression over the original (no upscale needed if zoom ≤ source):

```
zoompan=z='ZEXPR':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*0.36':d=1:s=1920x1080:fps=30,
eq=contrast=1.04:saturation=1.06:gamma=0.98, vignette=PI/5
```

> ⚠️ **Do NOT use `crop` with time-varying `w`/`h` — it does not work.** Earlier
> revisions of this file recommended
> `crop=w='floor((1920/Z)/2)*2':h='...'`. On ffmpeg 8.1.2 crop's output size is
> fixed at filter-init, so an animated w/h either produces **no movement at all**
> (silently — the render succeeds and the file looks fine) or aborts the encoder
> with `Invalid argument`. This shipped `ghostfont-intro` with zero camera moves.
> `zoompan` is the working path. See [[ffmpeg-zoom-use-zoompan-not-crop]].

`Z(t)` (zoom) is a **piecewise smoothstep** ramp generated from keyframes `(t, Z)` —
`P=clip((t-t0)/(t1-t0),0,1)`, `smooth=P*P*(3-2P)`. Generate the expression string with a
tiny Python helper (don't hand-write the nested `if(lt(…),…)`).

**`zoompan`'s time base is the OUTPUT FRAME COUNTER `on`, not `t`** — build the ramps
against `(on/30)`, and process the stream from frame 0 (seeking restarts `on`, which
shifts every timing). Choose the anchor with x/y: centre is `x='(iw-iw/zoom)/2'`,
bottom-left (keeps a corner webcam PIP in frame) is `x='0':y='ih-ih/zoom'`, and an
`area-zoom` onto a region at source `(sx,sy)` is `x='sx-(iw/zoom)/2':y='sy-(ih/zoom)/2'`
clamped to the frame.

This keeps the clip the **same length** (no concat/xfade → no A/V drift), and the overlay
graphics composite on top in final-frame coords (independent of the base move).

**Always verify the move landed in the FINAL file**, not just in the filter graph: extract
one frame at a neutral time and one at a punch peak and compare framing. A silent no-op is
the failure mode here, so "the render completed" proves nothing.

> **The anchor ramp `A(t)` — how to pan without zooming.** Drive the crop window's x
> with a second smoothstep ramp: `x='(AEXPR)*(iw-iw/zoom)'`. `A=1` is right-anchored
> (subject shifts LEFT, opening the RIGHT margin), `A=0` is left-anchored (mirror).
> Moving `A` at constant `Z` **is** a lateral pan — the sanctioned way to travel from
> a graphic on one side to a graphic on the other (EDIT_DYNAMICS §2.1). Two bonuses:
> `A` has no visible effect while `Z = 1.0`, so bookkeeping flips can be parked there
> for free; and anchoring toward the active graphic pushes the subject AWAY from it,
> which is what makes a narrow side margin usable (at Z 1.18 a centred subject moves
> ~350px, turning a 350px margin into ~420px). Always check subject-vs-graphic
> clearance at each beat's *shallowest* zoom — that is the worst case.

**THE BREATHE RULE — applies to intro-style energy moves (learned from feedback — the #1
mistake to avoid): moves must return to 1.0× ORIGINAL size.** Don't park the whole clip — or even a whole beat — on a held zoom
or push. Zoom/push *in* for a specific emphasis moment (~0.4s in), hold ~0.5–1s, then
**ease back to 1.0 original framing.** Neutral → move → neutral → move is the rhythm.

**Why this is non-negotiable — a zoom only READS as a move when contrasted against an
original-size baseline.** If the video is *already* zoomed (e.g. parked at 1.27 for a whole
6s beat), a punch to 1.34 is only a 5% change and is invisible — the viewer "sees the same."
The eye needs the unzoomed reference to feel the push-in. So the baseline is the real
footage at 1.0, and moves are momentary departures from it. Concretely: a 1.0→1.20→1.0
punch is FAR more visible and dynamic than a 1.27→1.34→1.27 punch, even though the second
is "bigger." **Bias toward a bigger move-vs-baseline delta, not a bigger absolute zoom.**

**Don't reach for sustained push-aside to make room for a graphic.** First position the
graphic in the frame's genuinely-empty regions (side thirds, upper band) so it clears a
centered subject at 1.0 — most talking-head shots have empty space on both sides of the
subject. Verify this by compositing the overlay over the source at Z=1.0, X=0 and checking
each beat for overlap *before* adding any camera move. Reserve push-aside for a graphic that
genuinely fills >50% of the frame (a big diagram), and even then treat it as a move that
returns. When a punch-in centered on a subject would grow them into a side graphic, add a
**momentary** X shift away from the graphic (subject shifts to the far side) that returns to
0 with the punch — not a held push.

**Punch magnitudes that work — INTROS/SHORTS ONLY** (1080p source, `flags=lanczos`): hero
moment 1.18–1.22, hook/CTA 1.12–1.15, minor beat 1.08–1.10 or none. In an explainer, ignore
this cadence entirely: use `area-zoom` sized to frame the region you're pointing at (often
1.3–1.5 on a screen recording), hold it as long as the viewer needs to read it, and return
when you're done pointing — driven by content, not by beat rhythm. Keep `y='(ih-oh)*0.30–0.34'` so the face
keeps headroom at the punch peak. Anchor each punch to the exact word/graphic it emphasizes.

> This was re-learned the hard way across several iterations on `claudecode101-intro`:
> parked/sustained zoom (even at big amplitude) reads as "constantly zoomed, no move";
> original-baseline + returning punches reads as a real edit. See [[camera-zoom-breathe-rule]].
>
> **Refined on `horizons-intro`:** "return to 1.0" means don't PARK the whole clip
> zoomed — it is NOT a licence to bounce through neutral between every consecutive
> graphic. Hold the zoom across a graphic beat, pan to the next graphic at that same
> zoom, and spend the return on a real story point. See EDIT_DYNAMICS §2.1.

---

## 7.7 · zoompan JUDDER on slow zooms — and the fix (measured)

**Symptom:** a slow/constant zoom (in or out) looks like it is *shaking* or
micro-stuttering, while fast punches look fine. Reported by the user on
`horizons-intro` v2.

**Cause:** `zoompan` rounds its crop rectangle to **integer pixels**. On a slow
ramp the true crop position falls between pixels, so the frame *holds* for a few
frames and then *jumps a double step*. Measured on a 2.25 px/frame ramp:

```
per-frame step:  -1.83  -1.81  -1.80  -3.68  -1.82  -1.75  -1.83  -1.66 ...
                                       ^^^^^ the catch-up jump
```

Zero direction reversals — it is **stair-stepping, not oscillation**. The slower
the ramp, the worse the *relative* error, which is why fast punches hide it. An
off-centre anchor makes it worse because the crop ORIGIN is quantised too, adding
a second stepping axis on top of the crop SIZE.

**Fix: supersample the input before `zoompan`.** Upscaling first puts the integer
grid at a fraction of an output pixel:

```
scale=5760:3240:flags=bicubic, zoompan=z='...':x='...':y='...':d=1:s=1920x1080:fps=30
```

The zoom expressions are written against `iw`/`ih` so they are scale-invariant —
nothing else changes. Measured on the same ramp (residual after detrending the
smoothstep ease, so this is judder only, not the intended acceleration):

| variant | judder (residual std) | verdict |
|---|---|---|
| 1080p direct | **0.864 px** | visible shake |
| 2× supersample (3840×2160) | 0.512 px | still marginal |
| **3× supersample (5760×3240)** | **0.216 px** | smooth |

3× is the working setting **for ordinary ramps**. Cost on a 29s 1080p clip:
composite went from ~35s to ~53s — cheap. **Always re-measure if you change it**;
do not drop the prescale because a render feels slow.

**Very slow creeps need 4×.** The residual scales with how slow the ramp is, and
3× is not always enough. Measured on `aibuilder-thanks`, whose slowest beat
creeps 1.12→1.20 across 6.8s (0.0118 zoom/s):

| ramp | 3× (5760×3240) | 4× (7680×4320) |
|---|---|---|
| 1.12→1.20 over 6.8s | **0.358 px — over threshold** | 0.282 px |
| 1.10→1.18 over 4.2s | 0.289 px | 0.209 px |
| 1.10→1.16 over 5.9s | 0.028 px | 0.027 px |

Cost of 4× on a 57s clip: 55s → 65s. So: if any beat creeps slower than about
0.015 zoom/s, start at 4× and measure. And measure **every** creep, not one —
the three above differ by more than 10× in residual on the same track, because
an off-centre anchor quantises the crop ORIGIN as well as its SIZE.

**How to measure** (do this, don't eyeball — judder is easy to miss on a still):
extract consecutive frames, find the best sub-pixel horizontal shift between each
pair on a *static background* patch, fit a cubic to the step sequence to remove
the legitimate ease, and take the residual std. Under ~0.35 px is smooth. Be sure
the patch does not contain the presenter's hands, or gesture motion contaminates
the measurement.

**Fallback if supersampling is ever unavailable** (the user's own suggestion, and
still a sound rule): use a slow/constant zoom only for a **centre-anchored** move,
and for an off-centre move onto a side graphic prefer a **short, decisive** zoom
over a long slow one — a fast ramp hides the quantisation.

---

## 8 · One-line summary

> **Always ask: full composite or layered handoff? Quote the time. Default to handoff
> for anything longer than a few minutes — composite is the bottleneck, your NLE is faster.**
