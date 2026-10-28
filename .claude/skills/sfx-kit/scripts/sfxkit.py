#!/usr/bin/env python3
"""Synthesized UI sound effects for motion graphics — no samples, no licences, deterministic.

    python sfxkit.py events.json sfx.wav [--gain 1.0] [--skip a:b ...] [--no type,type] [--report]
events.json comes from extract_events.mjs. Each animation becomes at most one sound, chosen by what moved:
  stamp slam → stamp (a light rubber-stamp tock: no sub-bass, so it never sounds like a big branded sting)
  pop of a photo → photo (paper flick) · of a card → card (soft paper slide) · of a chip/tag → chip (soft click) · of an svg → bubble (3 pitches)
  line draw → pen (scribble) · data-sfx="tear" → tear (paper rip) · number run → ticks · marker sweep → marker · text rise → air
  clip-path typing reveal → keys (soft key clicks) · big slide-in → swoosh · scale-from-0 wipe → card slide
Density control: low-priority sounds (bubble, chip, card, air) are dropped when another sound played less than THIN seconds before,
and a run of many pops in a row keeps only every other one. The point is texture, not a sound on every move.
"""
import json, argparse
import numpy as np

SR = 48000
rng = np.random.default_rng(7)                      # seeded: a re-render must give the same file

def env(n, a_ms, tau):                               # fast attack, exponential decay
    t = np.arange(n) / SR; e = np.exp(-t / tau); a = max(1, int(SR * a_ms / 1000)); e[:a] *= np.linspace(0, 1, a); return e

def lp(x, k):                                        # one-pole low-pass; smaller k = darker
    y = np.empty_like(x); acc = 0.0
    for i, s in enumerate(x): acc += k * (s - acc); y[i] = acc
    return y

def bp(x, k_hi, k_lo):                               # crude band-pass = low-pass(k_hi) minus low-pass(k_lo)
    return lp(x, k_hi) - lp(x, k_lo)

def norm(x): m = np.abs(x).max(); return x / m if m > 0 else x

# ── voices (each returns a peak-normalised signal; GAIN sets the level) ──
def bubble(f0=880, f1=520, dur=0.09):
    n = int(SR * dur); t = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-t / 0.018)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 2, 0.028))

def chip(f=1900, dur=0.03):                          # soft click: a tiny tone plus a tick of noise
    n = int(SR * dur); t = np.arange(n) / SR
    return norm(0.7 * np.sin(2 * np.pi * f * t) * env(n, 0.5, 0.006) + 0.5 * bp(rng.standard_normal(n), 0.6, 0.2) * env(n, 0.2, 0.003))

def card(dur=0.16):                                  # soft paper slide: filtered noise that swells then settles
    n = int(SR * dur); x = bp(rng.standard_normal(n), 0.35, 0.05); sh = np.sin(np.linspace(0, np.pi, n)) ** 1.2
    return norm(x * sh)

def photo(dur=0.11):                                 # paper flick: two quick bright transients
    n = int(SR * dur); x = bp(rng.standard_normal(n), 0.7, 0.15); e = env(n, 0.3, 0.012); e2 = np.roll(env(n, 0.3, 0.01), int(0.035 * SR)) * 0.7
    return norm(x * (e + e2))

def stamp(dur=0.16):                                 # light rubber-stamp tock: wood-ish knock + paper slap, no low boom
    n = int(SR * dur); t = np.arange(n) / SR; f = 210 + 120 * np.exp(-t / 0.01)
    knock = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.5, 0.025)
    slap = bp(rng.standard_normal(n), 0.65, 0.12) * env(n, 0.3, 0.018)
    return norm(0.8 * knock + 0.6 * slap)

def pen(dur):                                        # pen line: a bright scratch with a writing wobble
    n = int(SR * max(0.25, min(1.2, dur))); x = bp(rng.standard_normal(n), 0.6, 0.25)
    t = np.arange(n) / SR; wob = 0.55 + 0.45 * np.sin(2 * np.pi * 11 * t) ** 2; sh = np.minimum(1, t / 0.04) * np.minimum(1, (t[-1] - t) / 0.08)
    return norm(x * wob * sh)

def tear(dur=0.6):                                   # paper rip: crackle of tiny fibre snaps riding on a rising hiss
    n = int(SR * dur); t = np.arange(n) / SR
    hiss = bp(rng.standard_normal(n), 0.55, 0.08) * (0.25 + 0.75 * t / t[-1])
    imp = (rng.random(n) < (300 + 1500 * t / t[-1]) / SR).astype(float) * rng.uniform(0.5, 1.0, n)
    crackle = bp(lp(imp, 0.5) * 6, 0.7, 0.2)
    sh = np.minimum(1, t / 0.03) * np.minimum(1, (t[-1] - t) / 0.05)
    return norm((0.5 * hiss + crackle) * sh)

def keys(dur):                                       # typing: soft key clicks, about 13 a second, slightly uneven
    n = int(SR * max(0.2, min(2.5, dur))); out = np.zeros(n); t = 0.0
    while t < dur - 0.03:
        k = chip(f=1500 + 400 * rng.random(), dur=0.025) * (0.6 + 0.4 * rng.random()); i = int(t * SR); j = min(n, i + len(k)); out[i:j] += k[: j - i]
        t += 0.06 + 0.035 * rng.random()
    return norm(out)

def swoosh(dur=0.32):                                 # a fast pass of air for big slide-ins
    n = int(SR * dur); t = np.arange(n) / SR; x = bp(rng.standard_normal(n), 0.35, 0.04)
    sh = np.sin(np.linspace(0, np.pi, n)) ** 3 * (0.5 + 0.5 * t / t[-1])
    return norm(x * sh)

def tick(f=2600, dur=0.018):
    n = int(SR * dur); t = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * f * t) * env(n, 0.3, 0.004))

def marker(dur=0.45):
    n = int(SR * dur); x = lp(rng.standard_normal(n), 0.5) - lp(rng.standard_normal(n), 0.05)
    return norm(x * np.sin(np.linspace(0, np.pi, n)) ** 1.5)

def air(dur=0.30):
    n = int(SR * dur); x = lp(rng.standard_normal(n), 0.12)
    return norm(x * np.sin(np.linspace(0, np.pi, n)) ** 2)

GAIN = {"swoosh": 0.07, "keys": 0.06, "bubble": 0.10, "chip": 0.09, "card": 0.07, "photo": 0.12, "stamp": 0.22, "pen": 0.05, "tear": 0.16, "tick": 0.06, "marker": 0.05, "air": 0.035}
PRIO = {"swoosh": 1, "keys": 2, "stamp": 3, "tear": 3, "count": 3, "photo": 2, "pen": 2, "marker": 1, "card": 1, "chip": 0, "bubble": 0, "air": 0}
THIN = {0: 1.2, 1: 0.8, 2: 0.25, 3: 0.0}            # a sound of this priority needs this much quiet before it

def voice_of(e):
    if e.get("hint") == "none": return None
    if e.get("hint"): return e["hint"]
    ty = e["type"]
    if ty == "pop": return {"photo": "photo", "card": "card", "chip": "chip", "stamp": "stamp"}.get(e.get("kind"), "bubble")
    return {"stamp": "stamp", "marker": "marker", "draw": "pen", "count": "count", "rise": "air", "type": "keys", "swoosh": "swoosh", "wipe": "card"}.get(ty)

def build(events, dur, gain=1.0, skips=(), drop=()):
    out = np.zeros(int(SR * (dur + 1))); placed = []; last_t = -9; pops_in_row = 0
    def put(t, sig, g):
        i = int(t * SR); j = min(len(out), i + len(sig)); out[i:j] += sig[: j - i] * g * gain
    for e in events:
        vo = voice_of(e); t = e["t"]
        if not vo or vo in drop or any(a <= t < b for a, b in skips): continue
        pr = PRIO.get(vo, 0)
        if t - last_t < THIN[pr]: continue
        if vo in ("bubble", "chip"):
            pops_in_row = pops_in_row + 1 if t - last_t < 2.5 else 1
            if pops_in_row % 2 == 0: continue            # in a run of pops, every other one stays silent
        if vo == "count":
            d = e.get("dur", 1.0); k = int(min(36, max(6, 12 * d)))
            for i in range(k): put(t + d * (1 - np.sqrt(1 - i / k)), tick(2600 - 10 * i), GAIN["tick"])
        elif vo == "bubble": put(t, bubble(f0=[880, 760, 980][len(placed) % 3]), GAIN["bubble"])
        elif vo == "pen": put(t, pen(e.get("dur", 0.6)), GAIN["pen"])
        elif vo == "keys": put(t, keys(e.get("dur", 0.8)), GAIN["keys"])
        elif vo == "marker": put(t, marker(min(0.6, e.get("dur", 0.45) + 0.1)), GAIN["marker"])
        elif vo == "tear": put(t, tear(max(0.45, min(0.8, e.get("dur", 0.6)))), GAIN["tear"])
        else: put(t, {"chip": chip, "card": card, "photo": photo, "stamp": stamp, "air": air, "swoosh": swoosh}[vo](), GAIN[vo])
        placed.append((round(t, 2), vo)); last_t = t
    return out[: int(SR * dur)], placed

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("events"); ap.add_argument("out"); ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--skip", action="append", default=[], help="a:b seconds with no effects (e.g. under real footage)")
    ap.add_argument("--no", default="", help="comma list of voices to drop, e.g. air,marker"); ap.add_argument("--report", action="store_true")
    a = ap.parse_args(); d = json.load(open(a.events))
    x, placed = build(d["events"], d["dur"], a.gain, [tuple(map(float, s.split(":"))) for s in a.skip], set(filter(None, a.no.split(","))))
    import soundfile as sf; sf.write(a.out, x.astype(np.float32), SR)
    from collections import Counter; c = Counter(v for _, v in placed)
    print(f"wrote {a.out}  {len(placed)} sounds from {len(d['events'])} events  {dict(c)}  peak {np.abs(x).max():.3f}")
    if a.report: print(placed)
