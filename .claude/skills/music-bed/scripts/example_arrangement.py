#!/usr/bin/env python3
"""A complete 90-second bed for a calm, reflective narrated pitch.

Copy this file next to your project, replace ACTS with your real measured act
map, adjust the palette, and run:

    uv run --python 3.12 --with numpy --with soundfile python example_arrangement.py

Then always verify:

    python inspect_bed.py music.wav --map "0:problem,14:turn,56:bloom,81:resolve"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bedkit import Bed, brush, drone, felt, notes  # noqa: E402

OUT = "music.wav"
DUR = 90.5          # a little longer than the video; the fade trims it

# ── the act map ───────────────────────────────────────────────────────────
# Measured from the rendered narration, NOT guessed. Every envelope corner
# below is one of these numbers — that is what ties the music to the edit.
ACTS = {
    "problem":  0.0,    # thin, a touch cold
    "turn":    14.2,    # the product arrives; warmth enters
    "ritual":  29.1,    # quiet, intimate — pull back
    "howto":   37.7,    # steady forward motion
    "bloom":   55.5,    # the emotional peak — open it up
    "room":    71.9,    # full and warm
    "cta":     81.3,    # resolve
}

b = Bed(duration=DUR, bpm=76, seed=11)

# ── palette: calm / reflective (see references/palettes.md §2) ────────────
ROOTS = notes("D2", "Bb1", "F2", "C2")            # Dm – Bb – F – C
ARPS = [
    notes("D4", "F4", "A4", "F4"),
    notes("Bb3", "D4", "F4", "D4"),
    notes("F4", "A4", "C5", "A4"),
    notes("C4", "E4", "G4", "E4"),
]

# ── envelopes: every corner is an act boundary ────────────────────────────
arp_g = b.env([
    (0, 0.00), (2.0, 0.30),
    (ACTS["turn"], 0.42), (ACTS["turn"] + 0.6, 0.85),
    (ACTS["ritual"], 0.85), (ACTS["ritual"] + 0.4, 0.45),
    (ACTS["howto"], 0.45), (ACTS["howto"] + 0.6, 0.80),
    (ACTS["bloom"], 0.80), (ACTS["bloom"] + 0.6, 1.15),
    (ACTS["room"], 1.15), (ACTS["room"] + 0.4, 1.05),
    (ACTS["cta"], 1.05), (ACTS["cta"] + 1.0, 0.55),
    (DUR - 2.0, 0.0), (DUR, 0.0),
])
drone_g = b.env([
    (0, 1.00), (ACTS["turn"], 1.00), (ACTS["turn"] + 0.6, 0.72),
    (ACTS["ritual"], 0.72), (ACTS["ritual"] + 0.4, 0.95),
    (ACTS["howto"], 0.95), (ACTS["howto"] + 0.6, 0.65),
    (ACTS["bloom"], 0.65), (ACTS["bloom"] + 0.6, 0.90),
    (ACTS["room"], 0.90), (ACTS["room"] + 0.4, 1.10),
    (ACTS["cta"], 1.10), (DUR, 0.55),
])
brush_g = b.env([
    (0, 0.0), (ACTS["turn"], 0.0), (ACTS["turn"] + 0.6, 0.55),
    (ACTS["ritual"], 0.55), (ACTS["ritual"] + 0.4, 0.0),
    (ACTS["howto"], 0.0), (ACTS["howto"] + 0.6, 0.70),
    (ACTS["bloom"] + 0.6, 0.95), (ACTS["room"], 0.95),
    (ACTS["room"] + 0.4, 0.70), (ACTS["cta"] - 0.5, 0.0), (DUR, 0.0),
])

# ── the arrangement ───────────────────────────────────────────────────────
for i, t in b.bars():
    ch = i % 4
    b.add(t, drone(b.sr, ROOTS[ch], b.bar * 1.25), drone_g(t))
    b.add(t, drone(b.sr, ROOTS[ch] * 1.5, b.bar * 1.25), drone_g(t) * 0.42)

    for k, ts in b.beats(t):
        n = ARPS[ch][k]
        g = arp_g(ts) * (1.0 if k % 2 == 0 else 0.68)
        pan = 0.36 if k % 2 == 0 else 0.64
        b.add(ts, felt(b.sr, n), g, pan)

        # the bloom: double an octave up on alternate beats so the peak
        # audibly opens out instead of merely getting louder
        if ACTS["bloom"] <= ts < ACTS["room"] and k % 2 == 0:
            b.add(ts, felt(b.sr, n * 2, dur=2.0, tau=0.6), g * 0.42, 1 - pan)

        # a passing note every other bar keeps it off the metronome grid
        if i % 2 == 1 and k == 2:
            b.add(ts + b.beat / 2, felt(b.sr, ARPS[ch][(k + 1) % 4], dur=1.8, tau=0.5),
                  g * 0.45, 0.5)

        b.add(ts + b.beat / 2, brush(b.sr, b.rng), brush_g(ts) * (0.9 if k % 2 else 0.6), 0.55)

# closing tonic chord under the CTA, left to ring past the last frame
for f, g in zip(notes("F3", "C4", "F4", "C5"), (0.95, 0.75, 0.60, 0.30)):
    b.add(ACTS["cta"], felt(b.sr, f, dur=8.5, tau=3.4), g * 0.85)

b.master().write(OUT)
