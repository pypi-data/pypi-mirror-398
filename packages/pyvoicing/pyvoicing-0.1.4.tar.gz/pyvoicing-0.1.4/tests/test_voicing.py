from pyvoicing import Pitch, Spelling, Voicing


def test_voicing_add_remove_transpose_and_tones():
    v = Voicing("C4 E4 G4", root="C")
    assert v.tones == ["1", "maj3", "5"]
    assert ~v == [60, 64, 67]
    assert v.spell() == ["C4", "E4", "G4"]

    v2 = v.add("B4")
    assert "B4" in [str(p) for p in v2]

    v3 = v2.remove("E4")
    assert "E4" not in [str(p) for p in v3]

    v4 = v >> "M2"
    assert str(v4[0]) == "D4"
    assert str(v4[1]) in {"F#4", "Gb4"}


def test_voicing_add_sub_operators():
    v = Voicing("C4 E4 G4", root="C")
    v2 = v + Pitch("B4")
    v3 = v2 - "E4"
    assert "B4" in [str(p) for p in v2]
    assert "E4" not in [str(p) for p in v3]


def test_voicing_spelling_preference():
    prev = Spelling.prefer_flat
    try:
        Spelling.prefer_flat = True
        v = Voicing("C#4 F#4", root="C#")
        assert v.spell() == ["Db4", "Gb4"]
        assert v.spell(prefer_flat=False) == ["C#4", "F#4"]
    finally:
        Spelling.prefer_flat = prev
