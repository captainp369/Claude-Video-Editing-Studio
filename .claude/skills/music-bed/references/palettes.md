# Palettes — choosing tempo, voices and harmony by video temperature

Pick by what the video is *for*, not by what you like. The bed's job is to agree
with the narration's posture: a product pitch leans forward, a reflective piece
sits back. Getting this wrong is more damaging than any wrong note — cheerful
marimba under a story about burnout reads as tone-deaf no matter how well voiced.

---

## 1 · Brisk product pitch / feature demo

Forward motion, optimistic, never frantic. The viewer should feel the product is
efficient.

| | |
|---|---|
| Tempo | 92–104 BPM |
| Voices | `pluck` ostinato · `pulse` on 1 and 3 · `shaker` on offbeats · thin `drone` |
| Subdivision | 8ths (`b.beats(t, subdiv=2)`) |
| Progression | Am–F–C–G · roots `A2 F2 C3 G2` |
| Arp (Am/F/C/G) | `A4 C5 E5 C5` · `F4 A4 C5 A4` · `C5 E5 G5 E5` · `G4 B4 D5 B4` |
| Shape | thin on the problem → full on the turn → octave-up lift on the proof → ring out |

Keep `shaker` at or below 0.10 gain. The energy should come from the 8th-note
ostinato, not from percussion volume.

---

## 2 · Calm, personal, reflective

Patient, warm, a little wistful. Suits habit/wellbeing/journalling products,
personal essays, anything about time passing.

| | |
|---|---|
| Tempo | 72–80 BPM |
| Voices | `felt` · `drone` (prominent) · `brush` · no `shaker`, no `pulse` |
| Subdivision | quarters, with one passing 8th every other bar |
| Progression | Dm–Bb–F–C (vi–IV–I–V in F) · roots `D2 Bb1 F2 C2` |
| Arp | `D4 F4 A4 F4` · `Bb3 D4 F4 D4` · `F4 A4 C5 A4` · `C4 E4 G4 E4` |
| Shape | quiet and low → warm → **bloom on the emotional peak** → full → resolve on F |

The bloom is the move: at the peak, double the ostinato an octave up on alternate
beats and lift the drone. It reads as the piece opening its chest.

```python
if PEAK_START <= ts < PEAK_END and k % 2 == 0:
    b.add(ts, felt(b.sr, n * 2, dur=2.0, tau=0.6), gain * 0.42, pan=1 - pan)
```

---

## 3 · Tense / investigative

Unease without melodrama. For "here's what's broken" segments and problem-heavy
openings. Usually only the first act of a video wants this.

| | |
|---|---|
| Tempo | 84–92 BPM |
| Voices | `drone` (low, close intervals) · sparse `pluck` · `pulse` alone on 1 |
| Progression | static tonic with a semitone rub: hold `D2` and add `Eb3` against it |
| Shape | almost nothing → a single pulse per bar → cut hard into the turn |

The tension comes from a held minor second and from *space*, not from speed. Let
bars go by with only the drone. Resolve it the instant the video pivots — the
contrast is the payoff.

---

## 4 · Warm storytelling / documentary

Human, unhurried, slightly nostalgic. For narrative arcs and profile pieces.

| | |
|---|---|
| Tempo | 66–76 BPM |
| Voices | `felt` · `drone` · occasional `pluck` an octave up as a highlight |
| Progression | C–Am–F–G · roots `C2 A1 F2 G2` |
| Arp | `C4 E4 G4 E4` · `A3 C4 E4 C4` · `F4 A4 C5 A4` · `G4 B4 D5 B4` |
| Shape | follow the story beats, not a fixed pattern — dip at setbacks, lift at turns |

This is the one palette where it's worth adding an envelope corner mid-act: if
the narration has a reversal inside act four, pull the gain down for those four
seconds and bring it back. That's the difference between scoring and wallpaper.

---

## Choosing a key

Any of these transpose freely — `bedkit.note()` takes note names, so shifting is
a text edit. Two practical notes:

- Keep the ostinato roughly **C4–C5**. Below that it muddies against a male
  narrator's fundamental; above it starts to whistle and draw attention.
- Put the drone root **at or below A1–F2** so it occupies a band the voice
  doesn't. This is most of what makes a bed sit "under" rather than "beside" the
  narration.

## Duration and structure

Build the bed slightly longer than the video (1–2 bars over) and let the final
fade do the trimming. Ending exactly on the last frame tends to clip the ring-out
of the closing chord, which is the one note the viewer is most likely to notice.
