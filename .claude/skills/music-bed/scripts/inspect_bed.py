#!/usr/bin/env python3
"""inspect_bed.py — the substitute for ears.

You cannot hear the bed you just rendered. What you *can* do is confirm that
the thing on disk has the shape you intended, and that it has none of the
defects that make synthesized music sound broken. This script does both and
prints a verdict.

    python inspect_bed.py music.wav --map "0:problem,14:turn,56:bloom,81:resolve"

It writes <name>-inspect.png (waveform above spectrogram) — open it and check
that the loud/quiet/bright/dark regions line up with your act map. If you asked
for a bloom at 56s and the spectrogram looks identical either side of 56s, your
envelope is not doing what you think it is.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stderr or ""


def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=sample_rate,channels", "-of", "json", path],
        capture_output=True, text=True).stdout
    d = json.loads(out or "{}")
    st = (d.get("streams") or [{}])[0]
    return {
        "duration": float(d.get("format", {}).get("duration", 0) or 0),
        "sample_rate": int(st.get("sample_rate", 0) or 0),
        "channels": int(st.get("channels", 0) or 0),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--map", default="", help="'sec:label,sec:label' act boundaries")
    ap.add_argument("--target", type=float, default=-24.0,
                    help="expected integrated LUFS for a bed under narration")
    a = ap.parse_args()

    p = Path(a.wav)
    if not p.exists():
        print(f"missing: {p}")
        return 1

    info = probe(str(p))
    err = sh(["ffmpeg", "-i", str(p), "-af", "ebur128=framelog=quiet", "-f", "null", "/dev/null"])
    lufs = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", err)
    lra = re.search(r"LRA:\s*(-?[\d.]+)", err)
    vol = sh(["ffmpeg", "-i", str(p), "-af", "volumedetect", "-f", "null", "/dev/null"])
    peak = re.search(r"max_volume:\s*(-?[\d.]+)", vol)
    mean = re.search(r"mean_volume:\s*(-?[\d.]+)", vol)

    png = p.with_name(p.stem + "-inspect.png")
    w, s = p.with_name("_w.png"), p.with_name("_s.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-filter_complex",
                    "showwavespic=s=1400x200:colors=0xB3552E", "-frames:v", "1", str(w)])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-lavfi",
                    "showspectrumpic=s=1400x340:legend=0:scale=log", "-frames:v", "1", str(s)])
    subprocess.run(["magick", str(w), str(s), "-append", str(png)])
    w.unlink(missing_ok=True)
    s.unlink(missing_ok=True)

    L = float(lufs.group(1)) if lufs else 0.0
    P = float(peak.group(1)) if peak else 0.0

    print(f"file       {p.name}")
    print(f"duration   {info['duration']:.2f}s   {info['sample_rate']}Hz  {info['channels']}ch")
    print(f"loudness   {L:.1f} LUFS (target ~{a.target:.0f})   LRA {lra.group(1) if lra else '?'}")
    print(f"peak       {P:.1f} dBFS   mean {mean.group(1) if mean else '?'} dBFS")
    print(f"picture    {png}")

    if a.map:
        print("\nact map — check these boundaries are visible in the picture:")
        for part in a.map.split(","):
            sec, _, label = part.partition(":")
            try:
                frac = float(sec) / max(info["duration"], 1e-6)
            except ValueError:
                continue
            print(f"  {float(sec):6.1f}s  ({frac * 100:4.1f}% across)  {label}")

    print("\nchecks")
    ok = True
    if P > -1.0:
        print(f"  ✗ peaking at {P:.1f} dBFS — clipping risk, lower Bed.master(peak=…)")
        ok = False
    else:
        print(f"  ✓ headroom fine ({P:.1f} dBFS)")
    if abs(L - a.target) > 4.0:
        print(f"  ✗ {L:.1f} LUFS is far from the ~{a.target:.0f} target for a bed")
        ok = False
    else:
        print(f"  ✓ sits in bed range ({L:.1f} LUFS)")
    if info["channels"] != 2:
        print(f"  ✗ {info['channels']} channel(s) — beds should be stereo for width")
        ok = False
    else:
        print("  ✓ stereo")

    print("\nStill unverified by this script: whether it sounds good, whether the")
    print("harmony is pleasant, and whether it fights the narration. Say so when")
    print("you hand the video over, and offer to swap or drop the music.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
