# local-asr: offline transcription (Scribe-compatible)

Transcribes on your Mac, with no API key, and writes the **same JSON shape as
ElevenLabs Scribe**. `pack_transcripts.py` and the rest of the video-use
pipeline read it unchanged.

Everything stays inside the repo: the venv (`tools/local-asr/.venv/`), the model
weights (`.models/`) and the pip cache (`.cache/`). All three are git-ignored.

## Setup (once)

```bash
brew install whisper-cpp                         # whisper-cli, with Metal on Apple Silicon
mkdir -p .models/whisper-cpp
curl -L -o .models/whisper-cpp/ggml-large-v3-turbo-q5_0.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin      # 574 MB
curl -L -o .models/whisper-cpp/ggml-silero-v5.1.2.bin \
  https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v5.1.2.bin             # 0.9 MB (speech detection)
cd tools/local-asr && source env.sh && uv sync
```

## Use

```bash
cd tools/local-asr && source env.sh
# writes <video_parent>/edit/transcripts/<stem>.json, the same place Scribe does
.venv/bin/python transcribe_local.py "$ROOT/raw_media/clip.mov" --out-dir "$ROOT/video_projects/<name>/edit/transcripts"
```

Several videos in one call share one model load. Useful flags:
- `--glossary` passes `glossary.txt` as a vocabulary hint (edit it for your own terms).
- `--force` re-transcribes a cached source.

## Stack

| Step | What |
|---|---|
| Speech detection | Silero VAD (`ggml-silero-v5.1.2.bin`, 0.9 MB). Only speech is decoded. |
| Windows | ≤ 12 s, cut in pauses. Whisper decodes ≤ 224 tokens per window, and ~17 s of fast Thai hits that cap and silently loses the tail. |
| ASR | whisper.cpp `whisper-cli` (Homebrew, Metal) + `ggml-large-v3-turbo-q5_0.bin` (574 MB) |
| Timing | whisper.cpp DTW token timestamps (`--dtw large.v3.turbo`) |
| Thai words | PyThaiNLP `newmm`. Scribe's Thai "words" are sub-syllable pieces (`เ`,`ริ่`,`ม`); these are real words. |

Runs at **~1× realtime on an 8 GB Apple Silicon Mac** (a 10-min video takes ~10 min), using about 1 GB of RAM.

## How it compares with Scribe (17 Thai/English clips, 16.8k characters)

| | Standard large-v3-turbo | Typhoon Whisper Turbo (Thai fine-tune) |
|---|---|---|
| Text differs from Scribe | 3–13% on clean takes; ~20–30% on raw takes | worse on the one clip tested (13% vs 6.8%) |
| English terms kept in Latin | mostly | often transliterated or misheard ("Claude"→"Cloth") |
| Word-onset vs Scribe | median ~0.1 s | **broken** (median 3.4 s). The fine-tune moved the attention heads DTW relies on. |

Most of the remaining "difference" is spelling style, not error. Local writes
`18%`, `8,000 token` and `Motion Graphics`, where Scribe writes
`สิบแปดเปอร์เซ็นต์`, `แปดพันโทเคน` and `โมชั่นกราฟิก`.

**Real weaknesses of local:**
1. **Raw takes with retakes and stutters.** Whisper tidies repetition:
   "สามารถ สามารถใส่ซับไตเติล" becomes one clean phrase. video-use's retake
   detection needs the verbatim version. Keep Scribe for raw multi-take footage.
2. Occasional mishearings on fast Thai.
3. No speaker diarization and no audio-event tags.

**Prompting:** a term list or a filler-style Thai sentence did not beat no
prompt, and the prompt is what Whisper repeats when it hallucinates on
noise. It is off by default (`--glossary` opts in). Filler words (`เนี่ย`,
`นะครับ`) come through at about the same rate as Scribe with no prompt.

**Where it fits:** scripted and clean takes (intros, outros, shorts, sponsor
reads), captions, re-transcribing finished cuts, and offline work. Raw
multi-take recordings still go to Scribe.

## Gotchas

- **Don't run the PyTorch/transformers path on an 8 GB Mac.** A first attempt
  swapped for an hour on a 20 s clip. whisper.cpp exists for this reason.
- **exFAT drives:** macOS writes `._*` sidecar files next to everything, and
  `transformers` crashes trying to read them as Python. After any
  `uv sync`, run `find .venv -name '._*' -delete`.
- **Spinning external drives** make the first import of a big Python package slow. whisper-cli starts fast.
- `--timing ctc` (the Typhoon CTC aligner) needs PyTorch, so it has the same memory warning.
