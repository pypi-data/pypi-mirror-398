from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .constants import CHROMA_OF, CHROMA_OF_SHARP, OFFSET_OF
from .spelling import Spelling
from .interval import Interval

if TYPE_CHECKING:
    from .pitch import Pitch


class Chroma:
    """Represents a pitch class (chroma) without a specific octave."""

    def __init__(self, value: Union[int, str, "Chroma", "Pitch"]):
        # Import here to avoid circular imports
        from .pitch import Pitch

        match value:
            case int():
                self.offset = value % 12
            case str():
                self.offset = OFFSET_OF[value]
            case Chroma():
                self.offset = value.offset
            case Pitch():
                self.offset = value.offset
            case _:
                raise TypeError("expected value of type int|str|Chroma|Pitch")

    def __str__(self) -> str:
        mapping = CHROMA_OF if Spelling.prefer_flat else CHROMA_OF_SHARP
        return mapping[self.offset]

    def __repr__(self) -> str:
        return f"Chroma('{self}')"

    def __invert__(self) -> int:
        """Return the offset value of the chroma."""
        return self.offset

    def __eq__(self, other: Any) -> bool:
        from .pitch import Pitch

        match other:
            case int():
                return self.offset == other % 12
            case str():
                return self.offset == OFFSET_OF[other]
            case Chroma():
                return self.offset == other.offset
            case Pitch():
                return self.offset == other.offset
            case _:
                return False

    def __neg__(self) -> int:
        return -self.offset

    def spell(self, prefer_flat: Optional[bool] = None) -> str:
        """Return chroma name using the preferred spelling."""
        use_flat = Spelling.prefer_flat if prefer_flat is None else prefer_flat
        mapping = CHROMA_OF if use_flat else CHROMA_OF_SHARP
        return mapping[self.offset]

    @property
    def enharmonic(self) -> str:
        """Return the opposite spelling."""
        return self.spell(prefer_flat=not Spelling.prefer_flat)

    def transpose(self, value: Union[int, str, Interval]) -> Chroma:
        """Transpose chroma upwards."""
        return Chroma(self.offset + Interval(value).distance)

    def transpose_down(self, value: Union[int, str, Interval]) -> Chroma:
        """Transpose chroma downwards."""
        return Chroma(self.offset - Interval(value).distance)

    def distance_to(self, other: Union[int, str, "Chroma", "Pitch"]) -> Interval:
        """Return the interval from this chroma to the other (modulo 12)."""
        from .pitch import Pitch

        match other:
            case Pitch():
                other_offset = other.offset
            case _:
                other_offset = Chroma(other).offset
        return Interval((other_offset - self.offset) % 12)

    def __rshift__(self, value: Union[int, str, Interval]) -> Chroma:
        """Transpose chroma upwards."""
        return self.transpose(value)

    def __lshift__(self, value: Union[int, str, Interval]) -> Chroma:
        """Transpose chroma downwards."""
        return self.transpose_down(value)


# shorthand
C = Chroma
