# PyVoicing

A Python library for symbolic music analysis, focusing on chord voicings and tensions, providing intuitive Python classes for working with pitches, chromas, intervals, and voicings.
* Pythonic syntax
* Lightweight, no dependency
> PyVoicing is currently in Alpha stage.
> API and type hints are subject to change.
> Latest release: 0.1.4

## Installation

```bash
pip install pyvoicing
```

## Usage

```python
from pyvoicing import Pitch, Chroma, Interval, Voicing
# shorthands
from pyvoicing import P, C, I, V
# or simply
from pyvoicing import *

# Pitch
middle_c = Pitch('C', 4)
middle_c.value  # 60
~middle_c       # 60, shorthand
middle_c.octave # 4
middle_c.offset # 0
middle_c.name   # 'C'
middle_c.chroma # Chroma("C")

g = Pitch('G')  # default octave=4
b = P('B')      # shorthand P for Pitch
e = P('E5')     # octave as part of the string

a = e >> 'P4'   # transpose up a perfect 4th
a <<= 12        # transpose down an octave

# Voicing
Cmaj7 = Voicing([middle_c, g, b, e], root='C')
Cmaj7       # Voicing('C4 G4 B4 E5', 'C')
Cmaj7.tones # ['1', '5', 'maj7', 'maj3']
~Cmaj7      # [60, 67, 71, 76]

C69 = Cmaj7 + a - 'B4' + 'D5'
C69.tones   # ['1', '5', '6', '9', 'maj3']
C69 >> 3    # Voicing('Eb4 Bb4 C5 F5 G5', 'Eb')

Bm7b5 = V('B D5 F5 A5', 'B')  # shorthand
Bm7b5.tones # ['1', 'min3', 'b5', 'min7']
Bm7b5.root = 'G'
Bm7b5.tones # ['maj3', '5', 'dom7', '9']
G9 = V(Bm7b5)

C9 = G9 // 'C'
C9          # Voicing('E4 G4 Bb4 D5', 'C')
C913 = V(C9)
C913[1] >>= 'M2'
C913        # Voicing('E4 A4 Bb4 D5', 'C')
C913.tones  # ['maj3', '13', 'dom7', '9']
C913.drop2  # Voicing('Bb3 E4 A4 D5', 'C')
C913.drop2.tones # ['dom7', 'maj3', '13', '9']
```

## API Map (Quick Reference)
- `Pitch(value, octave=4)`: MIDI-backed pitch with properties like `name`, `octave`, `offset`, `chroma`, `abc`, `lilypond`, `freq`.
- `Chroma(value)`: pitch class without octave; supports transposition with intervals.
- `Interval(value, octave=0)`: interval distance with `offset`, `octave`, `interval`.
- `Voicing(pitches, root=None)`: collection of pitches with transposition, drop voicings, and chord-tone analysis via `tones`.
- `Rest()`: singleton rest placeholder.
- Constants: `CHROMA_OF`, `ABC_OF`, `INTERVAL_OF`, `OFFSET_OF`.

## Operator Semantics (Proposed)
Keep operator meanings consistent and numeric-like; use named methods for collection or analysis.

```python
# Pitch/Chroma transposition
Pitch("C4") >> "M2"          # Pitch("D4")
Chroma("C") << "m2"          # Chroma("B")

# Explicit named methods
Pitch("C4").transpose("M2")  # Pitch("D4")
Pitch("C4").distance_to("E4")  # Interval("M3")

# Spelling
from pyvoicing import Spelling
Spelling.prefer_flat = True
Pitch("C#4").spell()          # "Db4"
Pitch("C#4").spell(False)     # "C#4"

# Voicing composition
v = Voicing("C4 E4 G4", root="C")
v2 = v.add("B4")
v3 = v2.remove("E4")
v4 = v >> "M2"
```

**Pitch**
- `Pitch >> Interval -> Pitch` (transpose up)
- `Pitch << Interval -> Pitch` (transpose down)
- `pitch.distance_to(other) -> Interval`
- `Pitch == int|Pitch` compares MIDI values; string comparison is name-based unless it includes octave
- `Spelling.prefer_flat = True` controls default spelling; `pitch.spell(prefer_flat=...)` overrides once
- `pitch.lilypond` uses LilyPond English note names (e.g., `cs`, `df`)

**Chroma**
- `Chroma >> Interval -> Chroma`
- `Chroma << Interval -> Chroma`
- `chroma.distance_to(other) -> Interval` (distance modulo 12)
- `Spelling.prefer_flat = True` controls default spelling; `chroma.spell(prefer_flat=...)` overrides once

**Interval**
- `interval.add(other) -> Interval`
- `interval.subtract(other) -> Interval`
- Comparisons use semitone distance

**Voicing**
- Use named methods: `transpose(interval)`, `transpose_down(interval)`, `add(pitch)`, `remove(pitch)`, `find_interval(interval)`, `to_root(target)`
- Avoid overloading `%` and `//` for analysis/normalization
- `~voicing` returns MIDI values for all pitches
- `voicing + pitch` adds pitches; `voicing - pitch` removes pitches

## License
PyVoicing is licensed under the MIT License.

## Contributing
Feature suggestions and bug reports are welcome!

## Testing Matrix (Suggested)
- Parsing: `Pitch("C4")`, `Pitch("C#5")`, `Pitch("=C")` (ABC), `Chroma("Db")`, `Interval("M3")`.
- Transposition: `Pitch("C4") >> "M2"`, `Chroma("C") << "m3"`, `Voicing("C4 E4 G4") >> 12`.
- Equality: `Pitch("C4") == 60`, `Chroma("C") == Pitch("C5")`, `Voicing("C4 E4 G4") == Voicing("D4 F#4 A4") << "M2"`.
- Notation: `Pitch("C4").abc` octave shifts, rest handling.
- Regression: any reported bug gets a focused test.

## Changelog
See [CHANGELOG.md](https://github.com/lyk91471872/PyVoicing/blob/main/CHANGELOG.md) for version history and release notes.
