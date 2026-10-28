"""Thai text-to-speech with VachanaTTS (MIT, Piper/VITS ONNX, runs locally on CPU).

The Thai counterpart to Kokoro for English: stock voices (not your own),
free and offline. Before synthesis:
  1. English terms are replaced from lexicon.tsv with Thai spellings that
     VachanaTTS pronounces well (its own English fallback reads "subscribe"
     as "sub cibe" and "Prompt Cache" as nonsense). Tuned by tune_lexicon.py.
  2. Numbers are spelled out as Thai words (5.5 -> ห้าจุดห้า).

Voices (in tools/local-tts/voices/): th_m_1, th_m_2 (male), th_f_1, th_f_2 (female).

Usage (Kokoro's venv, which also has vachanatts):
    .tts-venv/bin/python tools/local-tts/thai_tts.py "ข้อความ" -o out.wav [--voice th_m_1] [--speed 1.0]
    .tts-venv/bin/python tools/local-tts/thai_tts.py -f script.txt -o out.wav
    .tts-venv/bin/python tools/local-tts/thai_tts.py "..." --show-text      # print the text actually spoken
"""

from __future__ import annotations

import argparse
import re
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
VOICES = HERE / "voices"
LEXICON = HERE / "lexicon.tsv"
VOICE_NAMES = ["th_m_1", "th_m_2", "th_f_1", "th_f_2"]
HF = "https://huggingface.co/VIZINTZOR/VachanaTTS/resolve/main"


def load_lexicon(path: Path = LEXICON) -> list[tuple[str, str]]:
    """(term, thai spelling) pairs, longest term first so 'Claude Code' wins over 'Claude'."""
    if not path.exists():
        return []
    pairs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        term, spelling = line.split("\t")[:2]
        pairs.append((term.strip(), spelling.strip()))
    return sorted(pairs, key=lambda p: -len(p[0]))


def apply_lexicon(text: str, pairs: list[tuple[str, str]]) -> str:
    for term, spelling in pairs:
        if re.search(r"[A-Za-z]", term):
            pat = r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])"
            text = re.sub(pat, f" {spelling} ", text, flags=re.IGNORECASE)
        else:
            text = text.replace(term, spelling)
    return re.sub(r"\s+", " ", text).strip()


def spell_numbers(text: str) -> str:
    from pythainlp.util import num_to_thaiword

    def repl(m: re.Match) -> str:
        s = m.group().replace(",", "")
        if "." in s:
            whole, frac = s.split(".", 1)
            return num_to_thaiword(int(whole)) + "จุด" + "".join(num_to_thaiword(int(d)) for d in frac)
        return num_to_thaiword(int(s))

    text = re.sub(r"\d[\d,]*(?:\.\d+)?", repl, text)
    return text.replace("%", "เปอร์เซ็นต์")


def prepare(text: str, lexicon: list[tuple[str, str]] | None = None) -> str:
    return spell_numbers(apply_lexicon(text, load_lexicon() if lexicon is None else lexicon))


_voices: dict = {}


def get_voice(name: str):
    from vachanatts.voice import Voice

    if name not in _voices:
        model, cfg = VOICES / f"{name}.onnx", VOICES / "speaker_config.json"
        for p, url in ((model, f"{HF}/voices/{name}.onnx"), (cfg, f"{HF}/speaker_config.json")):
            if not p.exists():
                import urllib.request
                VOICES.mkdir(parents=True, exist_ok=True)
                print(f"downloading {url}")
                urllib.request.urlretrieve(url, p)
        _voices[name] = Voice.load(str(model), str(cfg))
    return _voices[name]


def synthesize(text: str, out: Path, voice: str = "th_m_1", speed: float = 1.0,
               lexicon: list[tuple[str, str]] | None = None, prepared: bool = False) -> str:
    from vachanatts.config import SpeechConfig

    spoken = text if prepared else prepare(text, lexicon)
    cfg = SpeechConfig(volume=1.0, length_scale=1 / speed, noise_scale=0.667, noise_w_scale=0.8)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as wf:
        get_voice(voice).synthesize_wav(spoken, wf, cfg)
    return spoken


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("text", nargs="?")
    ap.add_argument("-f", "--file", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--voice", default="th_m_1", choices=VOICE_NAMES)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--show-text", action="store_true", help="print the text after lexicon + numbers")
    a = ap.parse_args()

    text = a.file.read_text(encoding="utf-8") if a.file else a.text
    if not text:
        ap.error("give text or -f FILE")
    spoken = prepare(text.strip())
    if a.show_text or not a.out:
        print(spoken)
    if a.out:
        synthesize(spoken, a.out, a.voice, a.speed, prepared=True)
        print(f"saved: {a.out}")


if __name__ == "__main__":
    main()
