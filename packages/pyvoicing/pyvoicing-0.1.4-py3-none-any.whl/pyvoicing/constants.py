from typing import Dict, Union

from .rest import Rest

# Mapping from pitch offset to chroma name (flat-preferred)
CHROMA_OF: Dict[int, str] = {
    0: "C",
    1: "Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
    Rest(): "rest",
}

# Mapping from pitch offset to chroma name (sharp-preferred)
CHROMA_OF_SHARP: Dict[int, str] = {
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
    Rest(): "rest",
}

# Mapping from pitch offset to ABC notation (octave=4, flat-preferred)
ABC_OF: Dict[int, str] = {
    0: "=C",
    1: "_D",
    2: "=D",
    3: "_E",
    4: "=E",
    5: "=F",
    6: "_G",
    7: "=G",
    8: "_A",
    9: "=A",
    10: "_B",
    11: "=B",
    Rest(): "z",
}

# Mapping from pitch offset to ABC notation (octave=4, sharp-preferred)
ABC_OF_SHARP: Dict[int, str] = {
    0: "=C",
    1: "^C",
    2: "=D",
    3: "^D",
    4: "=E",
    5: "=F",
    6: "^F",
    7: "=G",
    8: "^G",
    9: "=A",
    10: "^A",
    11: "=B",
    Rest(): "z",
}

# Mapping from pitch offset to LilyPond name (english, flat-preferred)
LILYPOND_OF: Dict[int, str] = {
    0: "c",
    1: "df",
    2: "d",
    3: "ef",
    4: "e",
    5: "f",
    6: "gf",
    7: "g",
    8: "af",
    9: "a",
    10: "bf",
    11: "b",
    Rest(): "r",
}

# Mapping from pitch offset to LilyPond name (english, sharp-preferred)
LILYPOND_OF_SHARP: Dict[int, str] = {
    0: "c",
    1: "cs",
    2: "d",
    3: "ds",
    4: "e",
    5: "f",
    6: "fs",
    7: "g",
    8: "gs",
    9: "a",
    10: "as",
    11: "b",
    Rest(): "r",
}

# Mapping from interval offset to interval name
INTERVAL_OF: Dict[int, str] = {
    0: "U",  # Unison
    1: "m2",  # minor second
    2: "M2",  # Major second
    3: "m3",  # minor third
    4: "M3",  # Major third
    5: "P4",  # Perfect fourth
    6: "T",  # Tritone
    7: "P5",  # Perfect fifth
    8: "m6",  # minor sixth
    9: "M6",  # Major sixth
    10: "m7",  # minor seventh
    11: "M7",  # Major seventh
}

# Mapping from pitch/interval name to offset
OFFSET_OF: Dict[str, int] = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "rest": Rest(),
    "=C": 0,
    "^C": 1,
    "_D": 1,
    "=D": 2,
    "^D": 3,
    "_E": 3,
    "=E": 4,
    "=F": 5,
    "^F": 6,
    "_G": 6,
    "=G": 7,
    "^G": 8,
    "_A": 8,
    "=A": 9,
    "^A": 10,
    "_B": 10,
    "=B": 11,
    "z": Rest(),
    "U": 0,  # Unison
    "m2": 1,  # minor second
    "M2": 2,  # Major second
    "m3": 3,  # minor third
    "M3": 4,  # Major third
    "P4": 5,  # Perfect fourth
    "T": 6,  # Tritone
    "P5": 7,  # Perfect fifth
    "m6": 8,  # minor sixth
    "M6": 9,  # Major sixth
    "m7": 10,  # minor seventh
    "M7": 11,  # Major seventh
    "1": 0,
    "b9": 1,
    "add2": 2,
    "sus2": 2,
    "9": 2,
    "add9": 2,
    "min3": 3,
    "#9": 3,
    "maj3": 4,
    "add4": 5,
    "sus4": 5,
    "11": 5,
    "add11": 5,
    "b5": 6,
    "#11": 6,
    "5": 7,
    "#5": 8,
    "b13": 8,
    "6": 9,
    "dim7": 9,
    "13": 9,
    "min7": 10,
    "dom7": 10,
    "maj7": 11,
}
