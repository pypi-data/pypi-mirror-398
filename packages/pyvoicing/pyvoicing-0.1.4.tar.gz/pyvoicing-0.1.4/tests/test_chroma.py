import pytest

from pyvoicing import Chroma, Spelling


def test_chroma_transpose_and_distance():
    c = Chroma("C")
    assert str(c >> "M2") == "D"
    assert str(c << "m2") == "B"
    assert c.distance_to("E").distance == 4


def test_chroma_plus_raises():
    c = Chroma("C")
    with pytest.raises(TypeError):
        _ = c + 1


def test_chroma_spelling_preference():
    prev = Spelling.prefer_flat
    try:
        Spelling.prefer_flat = True
        assert Chroma("C#").spell() == "Db"
        assert Chroma("C#").spell(prefer_flat=False) == "C#"
        assert Chroma("C#").enharmonic == "C#"

        Spelling.prefer_flat = False
        assert Chroma("C#").spell() == "C#"
        assert Chroma("C#").spell(prefer_flat=True) == "Db"
        assert Chroma("C#").enharmonic == "Db"
    finally:
        Spelling.prefer_flat = prev
