# AI Video Editing Studio

A Claude Code workspace that edits your videos through conversation — transcribe, cut, grade, animate, and export, all by chatting with your AI.

## Quick Start

1. Clone this repo and open Claude Code inside the folder
2. Paste this prompt:

> Set up my video editing studio

Claude will clone the required tools, install dependencies, and walk you through adding your API key.

## Usage

1. Drop your raw footage into `raw_media/`
2. Say: *"Edit [filename] into a polished video"*
3. Your output lands in `video_projects/<name>/edit/final.mp4`

## What's in this repo

| File / Folder | Purpose |
|---|---|
| `CLAUDE.md` | Instructions your AI assistant reads every session |
| `MOTION_PHILOSOPHY.md` | Design rules for motion graphics and animations |
| `TRIMMING_PHILOSOPHY.md` | Rules for cutting dialogue and removing filler |
| `RENDER_AND_EXPORT_PHILOSOPHY.md` | Export strategy — full composite vs. layered handoff |
| `.env.example` | Template for your API keys |
| `raw_media/` | Drop source footage here (never modified by the AI) |
| `video_projects/` | AI creates a project folder here for each video |

## Prerequisites

Install these before running the setup prompt:

- [Claude Code](https://claude.ai/code)
- [Node.js 22](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/)
- [ffmpeg](https://ffmpeg.org/)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [bun](https://bun.sh/) — JavaScript runtime
- [ElevenLabs API key](https://elevenlabs.io/) — for transcription
