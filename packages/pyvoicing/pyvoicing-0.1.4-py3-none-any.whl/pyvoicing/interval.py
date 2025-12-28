from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .constants import INTERVAL_OF, OFFSET_OF

if TYPE_CHECKING:
    from .chroma import Chroma


class Interval:
    def __init__(
        self, value: Union[int, str, "Interval", "Chroma"], octave: Optional[int] = 0
    ):
        # Avoid circular imports
        from .chroma import Chroma

        match value:
            case int():
                self.distance = value
            case str():
                self.distance = OFFSET_OF[value] + octave * 12
            case Interval():
                self.distance = value.distance
            case Chroma():
                self.distance = value.offset
            case _:
                raise TypeError("expected value of type int|str|Interval|Chroma")

    @property
    def offset(self) -> int:
        """Get the interval offset within an octave."""
        return self.distance % 12

    @offset.setter
    def offset(self, value: int) -> None:
        """Set the interval offset while preserving the octave."""
        self.distance = value + self.octave * 12

    @property
    def octave(self) -> int:
        """Get the octave component of the interval."""
        return self.distance // 12

    @octave.setter
    def octave(self, value: int) -> None:
        """Set the octave while preserving the offset."""
        self.distance = value * 12 + self.offset

    @property
    def interval(self) -> str:
        """Get the interval name assuming the same octave."""
        return INTERVAL_OF[self.offset]

    @interval.setter
    def interval(self, value: str) -> None:
        """Set the interval by name assuming the same octave."""
        self.offset = OFFSET_OF[value]

    def __str__(self) -> str:
        return f"{self.interval}({self.octave})" if self.octave else self.interval

    def __repr__(self) -> str:
        return f"Interval('{self.interval}', octave={self.octave})"

    def __invert__(self) -> int:
        """Return the distance value of the interval."""
        return self.distance

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: Union[int, str, Interval]) -> bool:
        return self.distance == Interval(other).distance

    def __gt__(self, other: Union[int, str, Interval]) -> bool:
        return self.distance > Interval(other).distance

    def __ge__(self, other: Union[int, str, Interval]) -> bool:
        return self > other or self == other

    def __lt__(self, other: Union[int, str, Interval]) -> bool:
        return not (self >= other)

    def __le__(self, other: Union[int, str, Interval]) -> bool:
        return not (self > other)

    def add(self, other: Union[int, str, Interval]) -> Interval:
        """Return the sum of two intervals."""
        return Interval(self.distance + Interval(other).distance)

    def subtract(self, other: Union[int, str, Interval]) -> Interval:
        """Return the difference of two intervals."""
        return Interval(self.distance - Interval(other).distance)


# shorthand
I = Interval
