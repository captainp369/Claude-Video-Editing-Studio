#!/usr/bin/env python3
"""One arranger for every narrated video: reads the edit's timeline and shapes a six-act bed to it.

    python bed_from_timeline.py timeline.json music.wav --acts 1,4,8,9,11,13 [options]

timeline.json needs "starts" (start time of each narration line, seconds) and "end" (video length).
--acts gives six line numbers (0-based index into starts) where the music changes shape, in this order:
    tension  · the problem is stated (sparse; low drone if --mood tense)
    turn     · the answer/plan arrives (pulse and ostinato come in)
    build    · momentum (ostinato grows, kick firms up)
    peak     · the high point (fullest)
    settle   · after the peak (thins out)
    question · the closing question / call to action (pad only)
Add --seconds to give the six act times in seconds instead of line numbers.

Options:
  --key minor|major      minor = D minor (serious, history, business); major = C major (warm, light, food/travel)
  --mood tense|light     tense keeps a low drone under tension and settle; light drops it
  --bpm 104 --seed 1983  tempo and the seed for the noise voices (same seed → byte-identical file)
  --lead 0.35            visuals lead the voice by this much; act corners move with them
  --duck a:b             silence the bed between a and b seconds (0.3 s ramps), e.g. under real footage with its own sound; repeatable
  --duck-timeline        duck under every clip listed in timeline.json as "clipt" (start) + "clipd" (duration)
Run: uv run --python 3.12 --with numpy --with soundfile python bed_from_timeline.py ...
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from bedkit import Bed, pluck, felt, drone, pulse, shaker, notes  # noqa: E402

KEYS = {
    "minor": dict(R=("D2", "A#1", "F2", "C2"), low="D1",
                  ARP=[("D4", "A4", "F4", "A4"), ("D4", "F4", "A#4", "F4"), ("C4", "F4", "A4", "F4"), ("C4", "E4", "G4", "E4")],
                  PAD=[("D3", "A3", "F4"), ("A#2", "F3", "D4"), ("F3", "C4", "A4"), ("C3", "G3", "E4")]),
    "major": dict(R=("C2", "G1", "A1", "F1"), low="C1",
                  ARP=[("C4", "E4", "G4", "E4"), ("B3", "D4", "G4", "D4"), ("C4", "E4", "A4", "E4"), ("C4", "F4", "A4", "F4")],
                  PAD=[("C3", "G3", "E4"), ("G2", "D3", "B3"), ("A2", "E3", "C4"), ("F2", "C3", "A3")]),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline"); ap.add_argument("out")
    ap.add_argument("--acts", required=True); ap.add_argument("--seconds", action="store_true")
    ap.add_argument("--key", default="minor", choices=KEYS); ap.add_argument("--mood", default="tense", choices=("tense", "light"))
    ap.add_argument("--bpm", type=float, default=104); ap.add_argument("--seed", type=int, default=1983); ap.add_argument("--lead", type=float, default=0.35)
    ap.add_argument("--duck", action="append", default=[]); ap.add_argument("--duck-timeline", action="store_true")
    a = ap.parse_args()
    tl = json.load(open(a.timeline)); ST = tl["starts"]; DUR = tl["end"] + 0.05
    v = [float(x) for x in a.acts.split(",")]; assert len(v) == 6, "--acts needs six values"
    t = v if a.seconds else [round(ST[int(i)] - a.lead, 2) for i in v]
    A = dict(zip(("crisis", "plan", "brands", "moon", "today", "q"), t))
    K = KEYS[a.key]; R = notes(*K["R"]); ARP = [notes(*c) for c in K["ARP"]]; PAD = [notes(*c) for c in K["PAD"]]; LOW = notes(K["low"])[0]
    b = Bed(duration=DUR, bpm=a.bpm, seed=a.seed)
    arp = b.env([(0, 0.25), (A["crisis"], 0.0), (A["plan"] - 0.2, 0.0), (A["plan"] + 0.6, 0.35), (A["brands"], 0.5), (A["moon"], 0.62), (A["today"], 0.3), (A["q"], 0.0), (DUR, 0.0)])
    pad = b.env([(0, 0.5), (A["crisis"], 0.3), (A["plan"], 0.55), (A["moon"], 0.8), (A["today"], 0.5), (A["q"], 0.9), (DUR - 1, 0.5), (DUR, 0.0)])
    if a.mood == "tense":
        low = b.env([(0, 0.0), (A["crisis"], 0.0), (A["crisis"] + 0.8, 0.9), (A["plan"] - 0.2, 0.9), (A["plan"] + 0.5, 0.0), (A["today"] - 0.1, 0.0), (A["today"] + 0.8, 0.6), (A["q"], 0.0), (DUR, 0.0)])
    else:
        low = b.env([(0, 0.0), (DUR, 0.0)])
    kick = b.env([(0, 0.1), (A["crisis"], 0.0), (A["plan"], 0.0), (A["plan"] + 0.6, 0.3), (A["brands"], 0.42), (A["moon"], 0.55), (A["today"], 0.2), (A["q"], 0.0), (DUR, 0.0)])
    hat = b.env([(0, 0.0), (A["plan"] + 0.6, 0.03), (A["moon"], 0.07), (A["today"], 0.02), (A["q"], 0.0), (DUR, 0.0)])
    for i, ts0 in b.bars():
        ch = i % 4
        for f in PAD[ch]: b.add(ts0, felt(b.sr, f, dur=b.bar * 1.25, tau=1.0), pad(ts0) * 0.36)
        b.add(ts0, drone(b.sr, R[ch], b.bar * 1.3), pad(ts0) * 0.42); b.add(ts0, drone(b.sr, LOW, b.bar * 1.3), low(ts0) * 0.9)
        for k, ts in b.beats(ts0, subdiv=2):
            b.add(ts, pluck(b.sr, ARP[ch][k % 4], dur=0.6, tau=0.2), arp(ts) * (1.0 if k % 2 == 0 else 0.6), 0.35 if k % 2 else 0.65)
            if k % 2 == 1: b.add(ts, shaker(b.sr, b.rng), hat(ts), 0.55)
        for k, ts in b.beats(ts0): b.add(ts, pulse(b.sr), kick(ts) * (1.0 if k in (0, 2) else 0.5))
    b.master(peak=0.30).write(a.out)
    ducks = [tuple(map(float, d.split(":"))) for d in a.duck]
    if a.duck_timeline and "clipt" in tl:
        ducks += [(s0, s0 + tl["clipd"][k]) for k, s0 in tl["clipt"].items()]
    if ducks:
        import numpy as np, soundfile as sf
        x, sr = sf.read(a.out); tt = np.arange(len(x)) / sr; g = np.ones(len(x))
        for s0, s1 in ducks:
            g = np.minimum(g, 1 - np.clip(np.minimum((tt - (s0 - 0.3)) / 0.3, ((s1 + 0.3) - tt) / 0.3), 0, 1))
        sf.write(a.out, (x.T * g).T if x.ndim > 1 else x * g, sr)
    print("wrote", a.out, {k: round(x, 2) for k, x in A.items()}, "ducked" if ducks else "")

if __name__ == "__main__":
    main()
