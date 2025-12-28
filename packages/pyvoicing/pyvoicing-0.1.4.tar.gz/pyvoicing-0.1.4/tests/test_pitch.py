import pytest

from pyvoicing import Pitch, Spelling


def test_pitch_transpose_distance_freq_eq():
    c4 = Pitch("C4")
    assert str(c4 >> "M2") == "D4"
    assert str(c4 << "m2") == "B3"

    e4 = Pitch("E4")
    assert c4.distance_to(e4).distance == 4
    assert e4.distance_to(c4).distance == -4

    a4 = Pitch("A4")
    assert a4.freq == pytest.approx(440.0)

    assert c4 == "C"
    assert c4 == "C4"
    assert c4 != "C5"


def test_pitch_plus_raises():
    c4 = Pitch("C4")
    with pytest.raises(TypeError):
        _ = c4 + Pitch("E4")


def test_pitch_spelling_preference():
    prev = Spelling.prefer_flat
    try:
        Spelling.prefer_flat = True
        assert Pitch("C#4").name == "Db"
        assert Pitch("C#4").spell(prefer_flat=False) == "C#4"
        assert Pitch("C#4").enharmonic == "C#4"

        Spelling.prefer_flat = False
        assert Pitch("C#4").name == "C#"
        assert Pitch("C#4").spell(prefer_flat=True) == "Db4"
        assert Pitch("C#4").enharmonic == "Db4"
    finally:
        Spelling.prefer_flat = prev


def test_pitch_lilypond_spelling():
    prev = Spelling.prefer_flat
    try:
        Spelling.prefer_flat = True
        assert Pitch("C4").lilypond == "c'"
        assert Pitch("C#4").lilypond == "df'"
        assert Pitch("C#4").lilypond_for(False) == "cs'"

        Spelling.prefer_flat = False
        assert Pitch("C4").lilypond == "c'"
        assert Pitch("C#4").lilypond == "cs'"
        assert Pitch("C#4").lilypond_for(True) == "df'"
    finally:
        Spelling.prefer_flat = prev
