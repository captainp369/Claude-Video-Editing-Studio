"""Pick, per English term, the Thai spelling VachanaTTS pronounces best.

Each candidate is spoken inside a carrier sentence by two voices, transcribed
back with the local whisper.cpp model, and scored by how close the heard word
is to what a listener should hear. The winner per term is written to
lexicon.tsv. Edit CANDIDATES (or lexicon.tsv by hand) to add your own terms.

    .tts-venv/bin/python tools/local-tts/tune_lexicon.py
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from rapidfuzz.distance import Levenshtein

import thai_tts

WHISPER = Path(__file__).resolve().parents[2] / ".models/whisper-cpp/ggml-large-v3-turbo-q5_0.bin"   # from tools/local-asr setup
VOICES = ["th_m_1", "th_m_2"]
CARRIER = "คำว่า {} นะครับ"

# term: (candidate Thai spellings, forms a listener should hear)
CANDIDATES = {
    "Cache": (["แคช", "แค็ด", "แค้ด", "แคด"], ["cache", "cash", "แคช", "แค็ช", "แค็ด"]),
    "Claude Code": (["คลอด โค้ด", "คล้อด โค้ด"], ["claudecode", "คลอดโค้ด"]),
    "Claude": (["คลอด", "คล้อด", "คลอดด์"], ["claude", "คลอด", "claud"]),
    "Prompt": (["พรอมต์", "พรอมท์", "พร้อมท์", "พรอม"], ["prompt", "พรอมต์", "พรอมท์"]),
    "Subscribe": (["ซับสไครบ์", "ซับสะไคร้บ์", "ซับสะไคร", "ซับสะไกร", "ซับ สะ ไคร้"], ["subscribe", "ซับสไครบ์", "ซับสะไคร"]),
    "Like": (["ไลก์", "ไล้", "ไลค", "ไล้ก์"], ["like", "ไลก์", "ไลค์", "ไล้"]),
    "Token": (["โทเคน", "โทเค็น", "โท-เค่น"], ["token", "โทเคน", "โทเค็น"]),
    "Anthropic": (["แอนโทรปิก", "แอนโธรปิก", "แอน-ทรอ-ปิก", "แอนทรอปิก"], ["anthropic", "แอนโทรปิก", "แอนโธรปิก"]),
    "AI": (["เอไอ", "เอ ไอ"], ["ai", "เอไอ"]),
    "Code": (["โค้ด", "โค้ต"], ["code", "โค้ด", "โคต"]),
    "Session": (["เซสชัน", "เซสชั่น", "เซ็ทชั่น"], ["session", "เซสชัน", "เซสชั่น"]),
    "Limit": (["ลิมิต", "ลิมิท"], ["limit", "ลิมิต"]),
    "YouTube": (["ยูทูบ", "ยูทูป"], ["youtube", "ยูทูบ", "ยูทูป"]),
    "Google": (["กูเกิล", "กูเกิ้ล"], ["google", "กูเกิล", "กูเกิ้ล"]),
    "Gemini": (["เจมิไน", "เจมินี่", "เจมิไน่"], ["gemini", "เจมิไน", "เจมินี"]),
    "OpenAI": (["โอเพนเอไอ", "โอเพ่นเอไอ"], ["openai", "โอเพนเอไอ", "โอเพ่นเอไอ"]),
    "GPT": (["จีพีที", "จี พี ที"], ["gpt", "จีพีที"]),
    "Hostinger": (["โฮสติงเกอร์", "โฮสติ้งเกอร์"], ["hostinger", "โฮสติงเกอร์", "โฮสติ้งเกอร์"]),
    "Opus": (["โอปุส", "โอพัส"], ["opus", "โอปุส", "โอพัส"]),
    "Sonnet": (["ซอนเน็ต", "ซอนเนต"], ["sonnet", "ซอนเน็ต", "ซอนเนต"]),
    "Fable": (["เฟเบิล", "เฟเบิ้ล", "เฟ-เบิ้ล", "เฟเบิน"], ["fable", "เฟเบิล", "เฟเบิ้ล"]),
}


def heard(wav: Path) -> str:
    with tempfile.TemporaryDirectory() as d:
        w16 = Path(d) / "a.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-ar", "16000",
                        "-ac", "1", str(w16)], check=True)
        r = subprocess.run(["whisper-cli", "-m", str(WHISPER), "-f", str(w16), "-l", "th",
                            "-np", "-nt"], capture_output=True, text=True)
    return r.stdout.strip()


def norm(s: str) -> str:
    s = s.lower()
    for w in ("คำว่า", "นะครับ", "คําว่า"):
        s = s.replace(w, "")
    return re.sub(r"[\s,.\-!?\"']", "", s)


def main() -> None:
    import sys

    only = set(sys.argv[1:])           # e.g. tune_lexicon.py Cache Like  -> retune just these
    path = thai_tts.HERE / "lexicon.tsv"
    rows = {}
    if only and path.exists():
        for l in path.read_text(encoding="utf-8").splitlines():
            if l and not l.startswith("#"):
                rows[l.split("\t")[0]] = l
    tmp = Path(tempfile.mkdtemp())
    for term, (cands, targets) in CANDIDATES.items():
        if only and term not in only:
            continue
        scored = []
        for c in cands:
            dists, got = [], []
            for v in VOICES:
                out = tmp / f"{v}.wav"
                thai_tts.synthesize(CARRIER.format(c), out, v, lexicon=[])
                h = heard(out)
                got.append(h)
                dists.append(min(Levenshtein.normalized_distance(norm(h), norm(t)) for t in targets))
            scored.append((sum(dists) / len(dists), c, got))
        scored.sort(key=lambda x: x[0])
        best = scored[0]
        print(f"{term:12} -> {best[1]:14} score {best[0]:.2f}   heard: {' | '.join(best[2])}")
        rows[term] = f"{term}\t{best[1]}\t{best[0]:.2f}"
    order = [t for t in CANDIDATES if t in rows] + [t for t in rows if t not in CANDIDATES]
    header = "# term\tthai spelling\t(score: 0 = heard exactly as intended; tuned by tune_lexicon.py)"
    path.write_text("\n".join([header] + [rows[t] for t in order]) + "\n", encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
