"""bedkit — a tiny synth library for building background music beds.

The point of this file is that the DSP is *solved*. You should not be deriving
envelopes and harmonic stacks from scratch every time you score a video; you
should be spending your judgement on the arrangement — which instrument, what
tempo, and where the music opens up relative to what the narrator is saying.

Everything here is deterministic: the same arrangement renders identically on
every run, which matters because a re-render must not silently change the mix.

Run with:
    uv run --python 3.12 --with numpy --with soundfile python your_arrangement.py
"""
from __future__ import annotations

import numpy as np
import soundfile as sf

# ─────────────────────────────────────────────────────────── notes

_SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note(name: str) -> float:
    """'A4' -> 440.0, 'Bb3' -> 233.08, 'F#2' -> 92.50.

    Write arrangements in note names, not raw floats. Frequency typos are
    invisible in code review and very audible in the render.
    """
    name = name.strip()
    letter, i = name[0].upper(), 1
    semi = _SEMI[letter]
    while i < len(name) and name[i] in "#b":
        semi += 1 if name[i] == "#" else -1
        i += 1
    octave = int(name[i:])
    return 440.0 * (2 ** ((semi - 9) / 12 + (octave - 4)))


def notes(*names: str) -> list[float]:
    return [note(n) for n in names]


# ─────────────────────────────────────────────────────── instruments
#
# Every voice takes `sr` first and returns a mono float array. They all apply a
# short attack ramp — without one, a waveform that starts at non-zero amplitude
# produces a click on every single note, which is the most common way a
# synthesized bed ends up sounding cheap.


def _attack(x: np.ndarray, ms: float) -> np.ndarray:
    return np.minimum(1.0, x / max(ms, 1e-6))


def pluck(sr: int, f: float, dur: float = 0.9, tau: float = 0.30,
          bright: float = 1.0, gain: float = 0.33) -> np.ndarray:
    """Marimba / kalimba-ish. Short decay, wooden. Good for brisk, upbeat beds."""
    x = np.arange(int(sr * dur)) / sr
    env = np.exp(-x / tau) * _attack(x, 0.004)
    y = (np.sin(2 * np.pi * f * x)
         + 0.28 * bright * np.sin(2 * np.pi * 2 * f * x) * np.exp(-x / (tau * 0.5))
         + 0.10 * bright * np.sin(2 * np.pi * 4 * f * x) * np.exp(-x / (tau * 0.3)))
    return y * env * gain


def felt(sr: int, f: float, dur: float = 2.6, tau: float = 0.85,
         gain: float = 0.30) -> np.ndarray:
    """Felt-piano-ish. Soft attack, long decay, a little hammer glint.

    Rounder and slower-speaking than `pluck`. Use when the video is reflective
    and you want the music to feel patient rather than propulsive.
    """
    x = np.arange(int(sr * dur)) / sr
    env = np.exp(-x / tau) * _attack(x, 0.010)
    y = (np.sin(2 * np.pi * f * x)
         + 0.22 * np.sin(2 * np.pi * 2 * f * x) * np.exp(-x / (tau * 0.45))
         + 0.07 * np.sin(2 * np.pi * 3 * f * x) * np.exp(-x / (tau * 0.25))
         + 0.03 * np.sin(2 * np.pi * 5.02 * f * x) * np.exp(-x / 0.12))
    return y * env * gain


def drone(sr: int, f: float, dur: float, attack: float = 1.6,
          gain: float = 0.09) -> np.ndarray:
    """Sustained pad. Two slightly detuned partials so it breathes instead of
    sitting dead-still. This is what stops a sparse bed sounding empty."""
    x = np.arange(int(sr * dur)) / sr
    env = (1 - np.exp(-x / attack)) * np.exp(-x / (dur * 0.85))
    y = (np.sin(2 * np.pi * f * x)
         + np.sin(2 * np.pi * f * 1.004 * x)
         + 0.45 * np.sin(2 * np.pi * f * 2 * x)
         + 0.20 * np.sin(2 * np.pi * f * 3 * x))
    return y * env * gain


def pulse(sr: int, f0: float = 92.0, f1: float = 48.0, dur: float = 0.30,
          gain: float = 0.55) -> np.ndarray:
    """Soft low heartbeat — a sine with a fast downward pitch sweep. Reads as
    a gentle kick without any click or transient spike."""
    x = np.arange(int(sr * dur)) / sr
    f = f1 + (f0 - f1) * np.exp(-x / 0.05)
    ph = 2 * np.pi * np.cumsum(f) / sr
    return np.sin(ph) * np.exp(-x / 0.12) * _attack(x, 0.002) * gain


def shaker(sr: int, rng: np.random.Generator, dur: float = 0.09,
           gain: float = 0.10) -> np.ndarray:
    """Bright tick. Differentiated noise — crisp, forward, slightly ticky.
    Suits energetic beds; at high gain it starts to sound like a clock."""
    x = np.arange(int(sr * dur)) / sr
    hp = np.diff(np.concatenate([[0.0], rng.standard_normal(len(x))]))
    return hp * np.exp(-x / 0.022) * gain


def brush(sr: int, rng: np.random.Generator, dur: float = 0.26,
          gain: float = 0.16) -> np.ndarray:
    """Airy sweep. Smoothed noise — the calm alternative to `shaker` when a
    tick would feel nagging under a slow, warm narration."""
    x = np.arange(int(sr * dur)) / sr
    y = np.convolve(rng.standard_normal(len(x)), np.ones(180) / 180, mode="same")
    return y * np.exp(-x / 0.11) * _attack(x, 0.03) * gain


# ─────────────────────────────────────────────────────────── the bed


class Bed:
    """A stereo timeline you place voices onto.

    Typical use:

        b = Bed(duration=90, bpm=76)
        warmth = b.env([(0, 0.3), (14, 0.9), (72, 1.1), (88, 0.0)])
        for i, t in b.bars():
            root = ROOTS[i % 4]
            b.add(t, drone(b.sr, root, b.bar * 1.2), warmth(t))
            for beat, ts in b.beats(t):
                b.add(ts, felt(b.sr, ARP[i % 4][beat]), warmth(ts), pan=0.36)
        b.master().write("music.wav")
    """

    def __init__(self, duration: float, sr: int = 48000, bpm: float = 96.0,
                 seed: int = 7):
        self.sr = sr
        self.duration = duration
        self.n = int(sr * duration)
        self.bpm = bpm
        self.beat = 60.0 / bpm
        self.bar = 4 * self.beat
        self.rng = np.random.default_rng(seed)
        self.t = np.arange(self.n) / sr
        self._L = np.zeros(self.n)
        self._R = np.zeros(self.n)

    # -- placement ---------------------------------------------------------

    def add(self, start: float, sig: np.ndarray, gain: float = 1.0,
            pan: float = 0.5) -> "Bed":
        """Place `sig` at `start` seconds. pan 0=left, 0.5=centre, 1=right.
        Out-of-range or zero-gain placements are silently ignored so callers
        can loop past the end of the timeline without guarding."""
        if gain <= 0:
            return self
        i = int(start * self.sr)
        if i < 0 or i >= self.n:
            return self
        k = min(len(sig), self.n - i)
        self._L[i:i + k] += sig[:k] * gain * np.sqrt(1 - pan)
        self._R[i:i + k] += sig[:k] * gain * np.sqrt(pan)
        return self

    def bars(self):
        """Yield (bar_index, start_seconds) for every bar in the timeline."""
        i, t = 0, 0.0
        while t < self.duration:
            yield i, t
            i += 1
            t += self.bar

    def beats(self, bar_start: float, subdiv: int = 1):
        """Yield (index, seconds) for beats inside a bar. subdiv=2 gives 8ths."""
        for k in range(4 * subdiv):
            ts = bar_start + k * self.beat / subdiv
            if ts >= self.duration:
                return
            yield k, ts

    # -- arrangement -------------------------------------------------------

    def env(self, points: list[tuple[float, float]]):
        """Piecewise-linear gain envelope over the timeline.

        `points` is [(seconds, gain), …] and the returned callable takes a time
        and gives the gain there. This is the mechanism that ties the music to
        the edit: put a point at each act boundary and the bed changes shape
        exactly where the story does.
        """
        ts = np.array([p[0] for p in points], dtype=float)
        vs = np.array([p[1] for p in points], dtype=float)
        table = np.interp(self.t, ts, vs)

        def at(sec: float) -> float:
            idx = int(np.clip(sec, 0, self.duration - 1e-6) * self.sr)
            return float(table[idx])

        return at

    # -- output ------------------------------------------------------------

    def master(self, peak: float = 0.30, soft: float = 1.1,
               fade: float = 0.015) -> "Bed":
        """Gentle saturation, peak-normalise, and fade the ends.

        peak=0.30 lands the bed around -24 LUFS, which is roughly where a bed
        wants to sit under narration before the final mix is normalised.
        """
        y = np.stack([self._L, self._R], axis=1)
        y = np.tanh(y * soft) / soft
        m = float(np.max(np.abs(y)))
        if m > 0:
            y = y / m * peak
        f = int(fade * self.sr)
        if f > 0:
            y[:f] *= np.linspace(0, 1, f)[:, None]
            y[-f:] *= np.linspace(1, 0, f)[:, None]
        self._out = y
        return self

    def write(self, path: str) -> str:
        y = getattr(self, "_out", None)
        if y is None:
            raise RuntimeError("call .master() before .write()")
        sf.write(path, y, self.sr)
        print(f"wrote {path}  {y.shape[0] / self.sr:.2f}s  peak {np.max(np.abs(y)):.3f}")
        return path
