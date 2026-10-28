# local-tts: Thai text-to-speech (stock voices)

`thai_tts.py` runs [VachanaTTS](https://huggingface.co/VIZINTZOR/VachanaTTS) locally on CPU. It is free and
MIT-licensed (its training data is undocumented). The voices are stock voices, not a clone of anyone:
`th_m_1` and `th_m_2` (male), `th_f_1` and `th_f_2` (female). They download from Hugging Face on first use.

## Setup (once, from the repo root)

```bash
uv venv .tts-venv --python 3.12
uv pip install --python .tts-venv vachanatts==0.0.7 pythainlp
```

## Use

```bash
.tts-venv/bin/python tools/local-tts/thai_tts.py "ข้อความ" -o out.wav --voice th_m_1 [--speed 1.0]
.tts-venv/bin/python tools/local-tts/thai_tts.py -f script.txt -o out.wav
.tts-venv/bin/python tools/local-tts/thai_tts.py "..." --show-text     # print what will actually be spoken
```

The script does two things before synthesis:
1. **English terms are replaced** using `lexicon.tsv`. VachanaTTS's own English fallback garbles words (Subscribe
   becomes "sub cibe", Prompt Cache becomes nonsense). To add a term, put it in `CANDIDATES` in `tune_lexicon.py`
   and run `tune_lexicon.py <Term>` (it needs the local-asr Whisper model to score candidates), or edit
   `lexicon.tsv` by hand.
2. **Numbers are spelled out in Thai** (4.6 → สี่จุดหก, 30% → สามสิบเปอร์เซ็นต์).

Known weak spots:
- **Cache** (`แค้ต`): check it by ear.
- **Like**: only works as `ไล้`.
- Rare words can be read syllable by syllable. Fix those with a lexicon entry.

**Check new English terms by ear** before a voice-over goes out.
