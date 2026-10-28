# Video Editing Studio

## First-time setup

If the skills are not yet installed (`.claude/skills/video-use/` or `.claude/skills/hyperframes/` are missing), run these commands from the repo root:

```bash
# Clone the two skills
git clone https://github.com/browser-use/video-use.git .claude/skills/video-use
git clone https://github.com/heygen-com/hyperframes.git .claude/skills/hyperframes

# Install Python deps for video-use
cd .claude/skills/video-use && uv sync && cd -

# Install Node deps for hyperframes
cd .claude/skills/hyperframes && bun install && cd -

# Create hf-* symlinks
ln -sf hyperframes/skills/hyperframes .claude/skills/hf-hyperframes
ln -sf hyperframes/skills/hyperframes-cli .claude/skills/hf-hyperframes-cli
ln -sf hyperframes/skills/hyperframes-registry .claude/skills/hf-hyperframes-registry
ln -sf hyperframes/skills/gsap .claude/skills/hf-gsap
ln -sf hyperframes/skills/claude-design-hyperframes .claude/skills/hf-claude-design-hyperframes
ln -sf hyperframes/skills/website-to-hyperframes .claude/skills/hf-website-to-hyperframes

# GSAP for the video-styles examples (not bundled in this repo; fetched from its official npm package)
curl -L -o video-styles/_shared/gsap.min.js https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js

# Copy env template (then open .env and add ELEVENLABS_API_KEY)
cp .env.example .env
```

## Upgrading an existing studio

When the user asks to upgrade or update the studio (e.g. "Upgrade my studio to v2"):
1. `git status`. If tracked files have local edits, show the user which ones and `git stash` them before pulling.
2. `git pull origin main`.
3. If you stashed, `git stash pop`. On a conflict, show both versions and ask the user which to keep; never discard their edits silently.
4. Run any first-time setup step above whose result is missing (e.g. `video-styles/_shared/gsap.min.js`); leave existing installs alone.
5. Tell the user what's new: summarise `git log --oneline <old-head>..HEAD` and list new files at the top level, in `video-styles/`, `tools/` and `.claude/skills/`.

Their own `raw_media/`, `video_projects/` and `.env` are git-ignored, so an upgrade never touches them.

Optional tools have their own one-time setup: offline transcription in `tools/local-asr/README.md`, Thai voice-over in `tools/local-tts/README.md`. Only install them when the user asks for them.

This workspace is a video-editing pipeline driven by two skills:

- **video-use** (`.claude/skills/video-use/`): transcribe, cut fillers/retakes, color grade, burn subtitles, generate overlay animations (Manim / PIL / Remotion). Audio-first, text-reasoning editor. See `.claude/skills/video-use/SKILL.md` and `install.md`.
- **hyperframes** (`.claude/skills/hyperframes/`): HTML → MP4 motion-graphics renderer (GSAP, Lottie, CSS, Three.js). Use for branded intros, lower-thirds, data viz, end cards. Top-level sub-skills are symlinked as `hf-*` in `.claude/skills/`.

Three more skills ship with the repo: **music-bed** (an original background bed from your story beats), **sfx-kit** (sound effects placed from the composition's own timeline) and **sketch-svg** (hand-drawn icons and graphics).

## Folder layout

- `raw_media/`: source footage (read-only; never modify originals).
- `video_projects/<name>/`: per-project working directory. This is `<videos_dir>` for video-use. All cuts, transcripts, renders, and overlays for a given project live here under `edit/`.
- `video-styles/`: ready-made visual styles for motion graphics. Each `styles/NN-name/STYLE.md` is a philosophy file (palette, type, motion, technique, don'ts, and a prompt) with a working `example.html`. Read `video-styles/_shared/HYPERFRAMES_RULES.md` once, then the chosen style's `STYLE.md`, before building in that style.
- `MOTION_PHILOSOPHY.md`: **required reading before any hyperframes motion-graphics work.** The design bible for the **Premium Dark** style pack: the 11 Laws, palette rules, timing, reference deconstruction. Re-read every time before building a composition.
- `EDIT_DYNAMICS_PHILOSOPHY.md`: **required reading before planning any edit that includes overlay graphics or camera moves.** Defines the Dynamics Ledger (a per-beat table of camera move / graphic / zone / entrance / exit that ships with the cut strategy for approval) and the nine Variety Laws that mechanically prevent static "same graphic, same spot, fade in/out" edits. **Start at §0.5: video type decides what the camera is for.** In an intro the camera creates energy (punches on emphasis words); in an explainer it only *points* at on-screen information (`area-zoom` onto a named region), and `none` is the correct default. Never apply intro punch cadence to an explainer.
- `MEDIA_SOURCING.md`: **read before downloading any photo or clip for a video.** When outside media may be used (make it → open licence → creator's own media with the user's OK → nothing else), `tools/fetch-media/fetch.py` (X posts, Wikimedia Commons, direct links, yt-dlp sites; writes credits), the renderer prep (`--prep`: 30 fps, SDR bt709, keyframes) and where credits go.
- `AUDIO_PIPELINE.md`: **music bed, sound effects and levels for every video.** House settings (bed at 0.22, final −16 LUFS), the music-bed arranger, the sfx-kit pass, and the rules (vary the pops, no booms on stamps). Read it before adding music or effects.
- `TRIMMING_PHILOSOPHY.md`: **required reading before any cut.** Captures the word-level cut heuristics, the stop-consonant tail trick, the iteration loop, and anti-patterns learned from real edits. Re-read every time before writing an EDL.
- `RENDER_AND_EXPORT_PHILOSOPHY.md`: **required reading before any render or composite step.** Defines the two delivery modes (A: full composite vs. B: layered handoff for an NLE), the wall-time estimates, and the rule that the agent **must always ask the user which mode they want before starting**. Re-read every time before kicking off a render.

## Standard pipeline

Given a raw video file the user drops into this workspace:

1. **Ingest + transcribe** (video-use): ElevenLabs Scribe → word-level JSON → `takes_packed.md`. For clean, scripted takes, the offline `tools/local-asr/` works too.
2. **Propose cut strategy** in plain English, including the visual style (Premium Dark by default, or one from `video-styles/`; ask if unclear) and the Dynamics Ledger from `EDIT_DYNAMICS_PHILOSOPHY.md` §1 if graphics/camera moves are planned. Wait for user confirmation before touching the cut.
3. **Assemble base cut** (video-use): filler removal, retake resolution, per-segment extract + `-c copy` concat, 30ms audio fades, master SRT on output timeline.
4. **Motion graphics** (hyperframes): author HTML compositions for intros / lower-thirds / callouts, render MP4, then composite over the base cut via ffmpeg overlay (follow video-use overlay rules: `setpts=PTS-STARTPTS+T/TB`, subtitles applied LAST). **Never invent beat content for an existing edit.** If the user hands over a pre-edited clip without per-beat timestamps or content, **transcribe first or ask**: what's said drives what the graphics show. Generic guessed copy (recap chips, "Thanks for watching") is the failure mode.
5. **Verify** a handful of cut boundaries + overlay windows before presenting `edit/final.mp4`.

All session outputs go to `<videos_dir>/edit/`. Never write inside the skill directories.

## Tools (`tools/`)

| Tool | What it does |
|---|---|
| `fetch-media/` | Fetch one photo or clip with its credit (see `MEDIA_SOURCING.md`). Always ask the user before a download. |
| `probe_render.py` | Render chosen moments of a composition as stills (optionally over footage, with alpha) to check them before a full render. |
| `hf-mixer/` | A small web panel for per-clip volume, mute, trim and split in a HyperFrames composition (Studio has no audio mixer). |
| `canvas-render/` | Render a canvas-drawn composition straight to MP4. |
| `local-asr/` | Offline Thai/English transcription that writes Scribe-compatible JSON (optional, ~600 MB of models). |
| `local-tts/` | Thai voice-over with free stock voices (optional). English terms go through `lexicon.tsv`; check new terms by ear. |
| `patch-studio-scroll.mjs` | Only for hyperframes 0.6.x: stops HyperFrames Studio's number fields changing when you scroll past them. |

## Environment

- `.env` holds `ELEVENLABS_API_KEY` (required for video-use). `.env.example` documents all variables.
- Node 22 is required by hyperframes. If `node --version` shows an older version, find the Node 22 binary path (e.g. `which node` after activating the right version, or check `/opt/homebrew/opt/node@22/bin` on Apple Silicon Macs) and prepend it to PATH before running hyperframes commands.
- Python env for video-use is at `.claude/skills/video-use/.venv` (managed by `uv`).
- Needs `ffmpeg`, `bun`, `uv`, `node@22` and `git` (see the README's prerequisites).

## Key commands

```bash
# video-use (from <videos_dir>)
uv run --project .claude/skills/video-use python -m video_use <...>   # or invoke via the skill

# hyperframes (from a composition dir, after `npx hyperframes init`)
export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
npx hyperframes preview    # live browser preview
npx hyperframes render     # export MP4

# a video-styles example
cd video-styles && ./render.sh 04        # → video-styles/renders/04-terminal.mp4
```

## Hard rules inherited from video-use

See the "Hard Rules" section of `.claude/skills/video-use/SKILL.md`. The non-negotiables:
subtitles last, per-segment extract + lossless concat, 30ms audio fades, overlay PTS shift,
word-boundary cuts, 30–200ms pad, verbatim word-level ASR, strategy confirmation before execution,
all outputs under `<videos_dir>/edit/`.
