"""Transcribe a video locally and write Scribe-compatible JSON.

Drop-in alternative to .claude/skills/video-use/helpers/transcribe.py: the
output has the same shape as an ElevenLabs Scribe response (`text`,
`language_code`, `words[]` of type word/spacing with start/end/speaker_id),
so pack_transcripts.py and every downstream step read it unchanged.

Pipeline:
  1. ffmpeg -> mono 16 kHz wav
  2. Silero VAD finds speech; only speech is decoded, in <= 12 s windows
  3. whisper.cpp (`whisper-cli`, Metal) running Whisper large-v3-turbo
     (q5_0 ggml, 574 MB) with DTW token timestamps. Weights live in
     <root>/.models/whisper-cpp/ (see README.md for why not Typhoon).
  4. Thai text is re-segmented into real words with PyThaiNLP (Whisper's
     and Scribe's own Thai "words" are sub-syllable byte pieces)
  5. optional --timing ctc: re-time Thai characters with the
     typhoon-whisper-medium-ctc forced aligner (~20 ms onsets). Needs
     PyTorch, so ~2 GB extra RAM. Latin words (Claude, Prompt...) are not in
     its vocab and are placed in the gap between their Thai neighbours.

Diarization and audio-event tags are not produced; every word is speaker_0.

Usage (source env.sh first so weights stay inside the repo):
    .venv/bin/python transcribe_local.py <video>... [--out-dir DIR] [--model NAME] [--prompt TEXT]
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

ROOT = Path(os.environ.get("ROOT", Path(__file__).resolve().parents[2]))   # repo root
MODELS = ROOT / ".models" / "whisper-cpp"
CTC_HEAD = "typhoon-ai/typhoon-whisper-medium-ctc"
SR = 16000
VAD_MODEL = "ggml-silero-v5.1.2.bin"

THAI = re.compile(r"[฀-๿]")
TOKEN_RE = re.compile(r"[฀-๿]+|[^\s฀-๿]+")


def extract_audio(video: Path, dest: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", str(SR),
         "-c:a", "pcm_s16le", str(dest)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


# ------------------------------------------------------------- ASR (whisper.cpp)

def silence_mids(wav_path: Path) -> list[float]:
    r = subprocess.run(
        ["ffmpeg", "-i", str(wav_path), "-af", "silencedetect=noise=-35dB:d=0.2",
         "-f", "null", "-"], capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return [(x + y) / 2 for x, y in zip(starts, ends)]


def speech_segments(wav_path: Path) -> list[tuple[float, float]]:
    """Silero VAD speech regions (seconds)."""
    r = subprocess.run(
        ["whisper-vad-speech-segments", "-vm", str(MODELS / VAD_MODEL), "-f", str(wav_path)],
        capture_output=True, text=True, check=True,
    )
    return [(float(x) / 100, float(y) / 100)
            for x, y in re.findall(r"start = ([\d.]+), end = ([\d.]+)", r.stdout)]


def find_chunks(wav_path: Path, duration: float, max_len: float) -> list[tuple[float, float]]:
    """Decode windows: speech only, each <= max_len, cut in pauses.

    - Non-speech (music, silence) is never sent to Whisper: on it, Whisper
      invents text, often by repeating the --prompt.
    - Whisper decodes at most 224 tokens per window and Thai is
      token-heavy (~17 s of fast Thai fills it), so a long window silently
      loses its tail. Adjacent speech regions are merged up to max_len;
      a longer region is split at the latest pause that fits.
    """
    PAD = 0.2
    segs = [(max(0.0, x - PAD), min(duration, y + PAD)) for x, y in speech_segments(wav_path)]
    mids = None
    pieces: list[tuple[float, float]] = []
    for x, y in segs:
        while y - x > max_len:
            if mids is None:
                mids = silence_mids(wav_path)
            cands = [m for m in mids if x + max_len / 4 < m <= x + max_len]
            cut = cands[-1] if cands else x + max_len
            pieces.append((x, cut))
            x = cut
        pieces.append((x, y))
    chunks: list[tuple[float, float]] = []
    for x, y in pieces:
        if chunks and y - chunks[-1][0] <= max_len and x - chunks[-1][1] < 1.0:
            chunks[-1] = (chunks[-1][0], y)
        else:
            chunks.append((x, y))
    return chunks


def write_chunks(wav_path: Path, chunks: list[tuple[float, float]], out_dir: Path) -> list[Path]:
    paths = []
    with wave.open(str(wav_path)) as src:
        params = src.getparams()
        for k, (a, b) in enumerate(chunks):
            src.setpos(int(a * SR))
            frames = src.readframes(int((b - a) * SR))
            p = out_dir / f"c{k:04d}.wav"
            with wave.open(str(p), "wb") as dst:
                dst.setparams(params)
                dst.writeframes(frames)
            paths.append(p)
    return paths


def parse_whisper_json(path: Path, offset: float) -> list[dict]:
    """Timestamped per-character pieces from one whisper-cli -ojf file.

    Token texts are BPE byte pieces, so a Thai character can be split across
    two tokens and a token's text is not valid UTF-8 on its own. We rebuild
    each segment's bytes with a start time per byte, decode once, and give
    each character the time of its first byte.
    """
    raw = path.read_bytes().decode("utf-8", errors="surrogateescape")
    doc = json.loads(raw, strict=False)
    pieces = []
    for seg in doc.get("transcription", []):
        toks = [t for t in seg.get("tokens", [])
                if not t["text"].startswith(("[_", "<|"))]
        if not toks:
            continue
        seg_end = offset + seg["offsets"]["to"] / 1000
        starts = []
        for t in toks:
            dtw = t.get("t_dtw", -1)
            rel = dtw / 100 if dtw is not None and dtw >= 0 else t["offsets"]["from"] / 1000
            starts.append(offset + rel)
        buf, btimes = bytearray(), []
        for k, t in enumerate(toks):
            b = t["text"].encode("utf-8", errors="surrogateescape")
            s = starts[k]
            e = max(starts[k + 1] if k + 1 < len(toks) else seg_end, s)
            for q in range(len(b)):
                btimes.append(s + (e - s) * q / max(1, len(b)))
            buf += b
        text = buf.decode("utf-8", errors="replace")
        pos = 0
        for ch in text:
            n = len(ch.encode("utf-8")) if ch != "\ufffd" else 1
            s = btimes[min(pos, len(btimes) - 1)]
            pos += n
            e = btimes[pos] if pos < len(btimes) else seg_end
            if ch != "\ufffd":
                pieces.append({"text": ch, "start": s, "end": max(e, s)})
        pieces.append({"text": " ", "start": seg_end, "end": seg_end})
    return pieces


def run_whisper_cpp(wav_path: Path, duration: float, model: Path, threads: int,
                    prompt: str | None, max_len: float) -> list[dict]:
    """Return timestamped per-character pieces [{text, start, end}] from whisper-cli."""
    chunks = find_chunks(wav_path, duration, max_len)
    paths = write_chunks(wav_path, chunks, wav_path.parent)
    cmd = ["whisper-cli", "-m", str(model), "-l", "th", "-t", str(threads),
           "--dtw", "large.v3.turbo", "-ojf", "-np"]
    if prompt:
        cmd += ["--prompt", prompt]
    for p in paths:
        cmd += ["-f", str(p)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pieces = []
    for (a, _), p in zip(chunks, paths):
        pieces += parse_whisper_json(Path(f"{p}.json"), a)
    return pieces


def pieces_to_chars(pieces: list[dict]) -> tuple[str, list[tuple[float, float]]]:
    """Flatten pieces into one string with a (start, end) per character."""
    text, times = [], []
    for p in pieces:
        t = p["text"]
        n = max(1, len(t))
        step = (p["end"] - p["start"]) / n
        for i, ch in enumerate(t):
            s = p["start"] + i * step
            text.append(ch)
            times.append((s, s + step))
    return "".join(text), times


# ---------------------------------------------------------- word segmentation

def segment_words(text: str) -> list[tuple[int, int]]:
    """Char spans [start, end) of words: Thai via newmm, Latin/digits by run."""
    from pythainlp.tokenize import word_tokenize

    spans = []
    for m in TOKEN_RE.finditer(text):
        tok, base = m.group(), m.start()
        if THAI.match(tok):
            k = 0
            for w in word_tokenize(tok, engine="newmm", keep_whitespace=False):
                spans.append((base + k, base + k + len(w)))
                k += len(w)
        else:
            spans.append((base, base + len(tok)))
    return spans


def build_words(text: str, times: list[tuple[float, float]]) -> list[dict]:
    words = []
    for a, b in segment_words(text):
        seg = text[a:b].strip()
        if not seg:
            continue
        words.append({
            "text": seg,
            "start": round(times[a][0], 3),
            "end": round(max(times[b - 1][1], times[a][0] + 0.02), 3),
        })
    # Keep monotonic: DTW occasionally lets a word start before its predecessor ends.
    for prev, cur in zip(words, words[1:]):
        if cur["start"] < prev["start"]:
            cur["start"] = prev["start"]
        if prev["end"] > cur["start"]:
            prev["end"] = cur["start"]
        if cur["end"] < cur["start"]:
            cur["end"] = cur["start"]
    return words


# ------------------------------------------------------------- CTC re-timing

@functools.cache
def load_ctc(device: str):
    import torch
    from huggingface_hub import hf_hub_download
    from transformers import WhisperFeatureExtractor, WhisperModel

    sys.path.insert(0, str(Path(hf_hub_download(CTC_HEAD, "standalone_align.py")).parent))
    from standalone_align import load_head  # bundled with the model repo

    head, cfg, symbols = load_head(CTC_HEAD, device)
    rev = cfg.get("encoder_revision")
    fe = WhisperFeatureExtractor.from_pretrained(cfg["encoder_id"], revision=rev)
    enc = WhisperModel.from_pretrained(
        cfg["encoder_id"], revision=rev, dtype=torch.float32, low_cpu_mem_usage=True
    ).encoder.to(device).eval()
    return head, symbols, fe, enc


def ctc_retime(wav_path: Path, text: str, times: list[tuple[float, float]]
               ) -> list[tuple[float, float]]:
    """Re-time Thai/digit characters with the CTC aligner, window by window.

    Windows (<= 28 s, one Whisper window) end at a space where possible.
    """
    import soundfile as sf
    import torch
    import torchaudio.functional as AF

    device = "cpu"  # 8 GB Macs: MPS + swap stalls; the encoder pass is cheap on CPU
    wav, _ = sf.read(wav_path, dtype="float32")
    head, symbols, fe, enc = load_ctc(device)
    sym2id = {s: i for i, s in enumerate(symbols)}

    new_times = list(times)
    n = len(text)
    MAX_WIN, PAD = 28.0, 0.25
    i = 0
    while i < n:
        w0 = max(0.0, times[i][0] - PAD)
        j = i
        while j < n and times[j][1] + PAD - w0 <= MAX_WIN:
            j += 1
        if j < n:
            k = text.rfind(" ", i, j)
            if k > i:
                j = k + 1
        j = max(j, i + 1)
        w1 = min(len(wav) / SR, times[j - 1][1] + PAD)

        idx = [c for c in range(i, j) if text[c] in sym2id and text[c] != " "]
        if idx:
            clip = wav[int(w0 * SR):int(w1 * SR)]
            fb = fe(clip, sampling_rate=SR, return_attention_mask=True, return_tensors="pt")
            mel_len = int(fb.attention_mask.sum())
            with torch.no_grad():
                h = enc(input_features=fb.input_features.to(device)).last_hidden_state
                h = h[:, : (mel_len - 1) // 2 + 1]
                logp = torch.log_softmax(head(h.float()), dim=-1).cpu().float()
            ids = torch.tensor([[sym2id[text[c]] for c in idx]], dtype=torch.int32)
            if logp.shape[1] >= ids.shape[1]:
                labels, _ = AF.forced_align(logp, ids, blank=0)
                lab = labels[0].tolist()
                k, t = 0, 0
                while t < len(lab) and k < len(idx):
                    if lab[t] == 0:
                        t += 1
                        continue
                    t0 = t
                    while t + 1 < len(lab) and lab[t + 1] == lab[t0]:
                        t += 1
                    new_times[idx[k]] = (w0 + t0 * 0.02, w0 + (t + 1) * 0.02)
                    k += 1
                    t += 1
                # Latin/other chars: fill the gap between aligned neighbours
                aligned = set(idx)
                c = i
                while c < j:
                    if c in aligned or text[c] == " ":
                        c += 1
                        continue
                    d = c
                    while d < j and d not in aligned:
                        d += 1
                    lo = new_times[c - 1][1] if c > i else times[c][0]
                    hi = new_times[d][0] if d < j else times[d - 1][1]
                    if hi <= lo:
                        hi = lo + 0.02 * (d - c)
                    step = (hi - lo) / (d - c)
                    for q in range(c, d):
                        new_times[q] = (lo + (q - c) * step, lo + (q - c + 1) * step)
                    c = d
        i = j
    return new_times


# ------------------------------------------------------------------- output

def to_scribe(words: list[dict], duration: float, meta: dict) -> dict:
    out_words: list[dict] = []
    for k, w in enumerate(words):
        if k:
            prev = out_words[-1]
            out_words.append({"text": " ", "start": prev["end"], "end": w["start"],
                              "type": "spacing", "speaker_id": "speaker_0"})
        out_words.append({**w, "type": "word", "speaker_id": "speaker_0"})
    return {
        "language_code": "tha",
        "language_probability": 1.0,
        "text": "".join(w["text"] for w in out_words),
        "words": out_words,
        "audio_duration_secs": duration,
        "local_asr": meta,
    }


def transcribe(video: Path, out_path: Path, model: Path, timing: str, threads: int,
               prompt: str | None, max_len: float) -> Path:
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "a.wav"
        extract_audio(video, wav_path)
        with wave.open(str(wav_path)) as w:
            duration = w.getnframes() / w.getframerate()

        print(f"  asr: {model.name} ({duration:.0f}s audio)", flush=True)
        pieces = run_whisper_cpp(wav_path, duration, model, threads, prompt, max_len)
        text, times = pieces_to_chars(pieces)
        t_asr = time.time() - t0

        if timing == "ctc":
            print(f"  timing: {CTC_HEAD}", flush=True)
            times = ctc_retime(wav_path, text, times)

    words = build_words(text, times)
    elapsed = time.time() - t0
    meta = {"engine": "whisper.cpp", "weights": model.name, "prompt": prompt,
            "timing": timing, "asr_secs": round(t_asr, 1), "total_secs": round(elapsed, 1),
            "realtime_factor": round(duration / elapsed, 2)}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(to_scribe(words, duration, meta), ensure_ascii=False, indent=2))
    print(f"  saved: {out_path.name} — {len(words)} words, {elapsed:.0f}s "
          f"({meta['realtime_factor']}x realtime)")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("videos", type=Path, nargs="+")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="default: <video_parent>/edit/transcripts")
    ap.add_argument("--model", default="large-v3-turbo-q5_0",
                    help="ggml-<model>.bin in .models/whisper-cpp")
    ap.add_argument("--prompt", default=None,
                    help="vocabulary hint for Whisper (off by default: in the bake-off it "
                         "did not beat no-prompt and it is what Whisper parrots on noise)")
    ap.add_argument("--glossary", action="store_true", help="use glossary.txt as --prompt")
    ap.add_argument("--max-chunk", type=float, default=12.0, help="seconds per decode window")
    ap.add_argument("--timing", choices=["whisper", "ctc"], default="whisper")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--suffix", default="", help="appended to the output stem")
    ap.add_argument("--force", action="store_true", help="overwrite a cached transcript")
    a = ap.parse_args()

    model = MODELS / f"ggml-{a.model}.bin"
    prompt = a.prompt
    glossary = Path(__file__).with_name("glossary.txt")
    if a.glossary and glossary.exists():
        prompt = ", ".join(l.strip() for l in glossary.read_text().splitlines()
                           if l.strip() and not l.startswith("#"))
    if not model.exists():
        sys.exit(f"model not found: {model} (see convert/README.md)")

    for video in (v.resolve() for v in a.videos):
        if not video.exists():
            print(f"video not found: {video}")
            continue
        out_dir = (a.out_dir or video.parent / "edit" / "transcripts").resolve()
        out_path = out_dir / f"{video.stem}{a.suffix}.json"
        if out_path.exists() and not a.force:
            print(f"cached: {out_path.name}")
            continue
        print(f"== {video.name}", flush=True)
        transcribe(video, out_path, model, a.timing, a.threads, prompt or None, a.max_chunk)


if __name__ == "__main__":
    main()
