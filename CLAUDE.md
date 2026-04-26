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

# Copy env template (then open .env and add ELEVENLABS_API_KEY)
cp .env.example .env
```

This workspace is a personal video-editing pipeline driven by two skills:

- **video-use** (`.claude/skills/video-use/`) — transcribe, cut fillers/retakes, color grade, burn subtitles, generate overlay animations (Manim / PIL / Remotion). Audio-first, text-reasoning editor. See `.claude/skills/video-use/SKILL.md` and `install.md`.
- **hyperframes** (`.claude/skills/hyperframes/`) — HTML → MP4 motion-graphics renderer (GSAP, Lottie, CSS, Three.js). Use for branded intros, lower-thirds, data viz, end cards. Top-level sub-skills are symlinked as `hf-*` in `.claude/skills/`.

## Folder layout

- `raw_media/` — source footage (read-only; never modify originals).
- `video_projects/<name>/` — per-project working directory. This is `<videos_dir>` for video-use. All cuts, transcripts, renders, and overlays for a given project live here under `edit/`.
- `MOTION_PHILOSOPHY.md` — **required reading before any hyperframes motion-graphics work.** The user's design bible — the 11 Laws, palette rules, timing, reference deconstruction. Re-read every time before building a composition.
- `TRIMMING_PHILOSOPHY.md` — **required reading before any cut.** Captures the word-level cut heuristics, the stop-consonant tail trick, the iteration loop, and anti-patterns learned from the first intro video. Re-read every time before writing an EDL.
- `RENDER_AND_EXPORT_PHILOSOPHY.md` — **required reading before any render or composite step.** Defines the two delivery modes (A — full composite vs. B — layered handoff for an NLE), the wall-time estimates, and the rule that the agent **must always ask the user which mode they want before starting**. Re-read every time before kicking off a render.

## Standard pipeline

Given a raw video file the user drops into this workspace:

1. **Ingest + transcribe** (video-use): ElevenLabs Scribe → word-level JSON → `takes_packed.md`.
2. **Propose cut strategy** in plain English. Wait for user confirmation before touching the cut.
3. **Assemble base cut** (video-use): filler removal, retake resolution, per-segment extract + `-c copy` concat, 30ms audio fades, master SRT on output timeline.
4. **Motion graphics** (hyperframes): author HTML compositions for intros / lower-thirds / callouts, render MP4, then composite over the base cut via ffmpeg overlay (follow video-use overlay rules — `setpts=PTS-STARTPTS+T/TB`, subtitles applied LAST).
5. **Verify** a handful of cut boundaries + overlay windows before presenting `edit/final.mp4`.

All session outputs go to `<videos_dir>/edit/`. Never write inside the skill directories.

## Environment

- `.env` holds `ELEVENLABS_API_KEY` (required for video-use). `.env.example` documents all variables.
- Node 22 is required by hyperframes. If `node --version` shows an older version, find the Node 22 binary path (e.g. `which node` after activating the right version, or check `/opt/homebrew/opt/node@22/bin` on Apple Silicon Macs) and prepend it to PATH before running hyperframes commands.
- Python env for video-use is at `.claude/skills/video-use/.venv` (managed by `uv`).
- `ffmpeg`, `bun`, `uv`, `node@22`, `git` are all installed on this machine.

## Key commands

```bash
# video-use (from <videos_dir>)
uv run --project .claude/skills/video-use python -m video_use <...>   # or invoke via the skill

# hyperframes (from a composition dir, after `npx hyperframes init`)
export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
npx hyperframes preview    # live browser preview
npx hyperframes render     # export MP4
```

## Hard rules inherited from video-use

See the "Hard Rules" section of `.claude/skills/video-use/SKILL.md`. The non-negotiables:
subtitles last, per-segment extract + lossless concat, 30ms audio fades, overlay PTS shift,
word-boundary cuts, 30–200ms pad, verbatim word-level ASR, strategy confirmation before execution,
all outputs under `<videos_dir>/edit/`.
