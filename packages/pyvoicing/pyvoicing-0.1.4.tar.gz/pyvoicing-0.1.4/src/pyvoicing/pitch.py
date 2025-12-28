from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .chroma import Chroma
from .constants import (
    ABC_OF,
    ABC_OF_SHARP,
    CHROMA_OF,
    CHROMA_OF_SHARP,
    LILYPOND_OF,
    LILYPOND_OF_SHARP,
    OFFSET_OF,
)
from .rest import Rest
from .spelling import Spelling

if TYPE_CHECKING:
    from .interval import Interval


class Pitch:
    def __init__(self, value: Union[int, str, Chroma, Pitch], octave: int = 4):
        match value:
            case int():
                self.value = value
            case str():
                if any(_ in value for _ in '_=^'):
                    self.abc = value
                    return
                chroma = ''.join(_ for _ in value if _.isalpha() or _ == '#')
                if len(chroma) < len(value):
                    octave = int(value[len(chroma) :])
                self.value = OFFSET_OF[chroma] + (octave + 1) * 12
            case Chroma():
                self.value = value.offset + (octave + 1) * 12
            case Pitch():
                self.value = value.value
            case _:
                raise TypeError("expected value of type int|str|Chroma|Pitch")

    def __str__(self) -> str:
        return f"{self.name}{self.octave}"

    def __repr__(self) -> str:
        return f"Pitch('{self.name}', {self.octave})"

    def __invert__(self) -> int:
        """Return the MIDI value of the pitch."""
        return self.value

    def __hash__(self) -> int:
        return hash(str(self))

    def __lt__(self, other: Any) -> bool:
        match other:
            case int():
                return self.value < other
            case Pitch():
                return self.value < other.value
            case _:
                return NotImplemented

    def __le__(self, other: Any) -> bool:
        match other:
            case int():
                return self.value <= other
            case Pitch():
                return self.value <= other.value
            case _:
                return NotImplemented

    def __gt__(self, other: Any) -> bool:
        match other:
            case int():
                return self.value > other
            case Pitch():
                return self.value > other.value
            case _:
                return NotImplemented

    def __ge__(self, other: Any) -> bool:
        match other:
            case int():
                return self.value >= other
            case Pitch():
                return self.value >= other.value
            case _:
                return NotImplemented

    def __eq__(self, other: Any) -> bool:
        match other:
            case int():
                return self.value == other
            case str():
                if any(_.isdigit() for _ in other):
                    return str(self) == other
                return self.name == other
            case Chroma():
                return self.offset == other.offset
            case Pitch():
                return self.value == other.value
            case _:
                return False

    def __mul__(self, n: int) -> list[Pitch]:
        """Return a list of copies."""
        return [Pitch(self) for i in range(n)]

    def transpose(self, interval: Union[int, str, "Interval", Chroma]) -> Pitch:
        """Transpose pitch upwards."""
        from .interval import Interval

        return Pitch(self.value + Interval(interval).distance)

    def transpose_down(self, interval: Union[int, str, "Interval", Chroma]) -> Pitch:
        """Transpose pitch downwards."""
        from .interval import Interval

        return Pitch(self.value - Interval(interval).distance)

    def distance_to(self, other: Union[int, str, "Pitch"]) -> "Interval":
        """Return the interval from this pitch to the other."""
        from .interval import Interval

        return Interval(Pitch(other).value - self.value)

    def __rshift__(
        self, interval: Union[int, str, "Interval", Chroma]
    ) -> Pitch:
        """Transpose pitch upwards."""
        return self.transpose(interval)

    #    def __truediv__(self, interval: Union[int, str, 'Interval', Chroma, 'Pitch']) -> Pitch:
    #        """Transpose pitch downwards."""
    #        from .interval import Interval
    #        match interval:
    #            case Pitch():
    #                return Pitch(self.value - interval.value)
    #            case _:
    #                return Pitch(self.value - Interval(interval).distance)

    def __lshift__(
        self, interval: Union[int, str, "Interval", Chroma]
    ) -> Pitch:
        """Transpose pitch downwards."""
        return self.transpose_down(interval)

    @property
    def offset(self) -> int:
        """Get the offset within an octave."""
        return self.value % 12

    @offset.setter
    def offset(self, value: int) -> None:
        """Set the offset while preserving the octave."""
        self.value = (self.octave + 1) * 12 + value

    @property
    def octave(self) -> int:
        """Get the octave of the pitch."""
        return self.value // 12 - 1

    @octave.setter
    def octave(self, value: int) -> None:
        """Set the octave while preserving the offset."""
        self.value = self.offset + (value + 1) * 12

    @property
    def name(self) -> str:
        """Get the pitch name."""
        mapping = CHROMA_OF if Spelling.prefer_flat else CHROMA_OF_SHARP
        return mapping[self.offset]

    @name.setter
    def name(self, value: str) -> None:
        """Set the pitch by name."""
        self.offset = OFFSET_OF[value]

    @property
    def chroma(self) -> Chroma:
        """Get the chroma of this pitch."""
        return Chroma(self)

    @chroma.setter
    def chroma(self, value: Chroma) -> None:
        """Set the chroma while preserving the octave."""
        self.offset = value.offset

    def spell(self, prefer_flat: Optional[bool] = None) -> str:
        """Return pitch name with octave using the preferred spelling."""
        use_flat = Spelling.prefer_flat if prefer_flat is None else prefer_flat
        mapping = CHROMA_OF if use_flat else CHROMA_OF_SHARP
        return f"{mapping[self.offset]}{self.octave}"

    @property
    def enharmonic(self) -> str:
        """Return the opposite spelling with octave."""
        return self.spell(prefer_flat=not Spelling.prefer_flat)

    @property
    def abc(self) -> str:
        """Get the ABC notation of this pitch."""
        return self.abc_for()

    def abc_for(self, prefer_flat: Optional[bool] = None) -> str:
        """Return ABC notation using the preferred spelling."""
        use_flat = Spelling.prefer_flat if prefer_flat is None else prefer_flat
        mapping = ABC_OF if use_flat else ABC_OF_SHARP
        abc = mapping[self.offset]
        if abc == "z":
            return abc
        if (va := self.octave - 4) <= 0:
            return abc + "," * -va
        return abc.lower() + "'" * (va - 1)

    @property
    def lilypond(self) -> str:
        """Return LilyPond notation using the preferred spelling."""
        return self.lilypond_for()

    def lilypond_for(self, prefer_flat: Optional[bool] = None) -> str:
        """Return LilyPond notation using the preferred spelling."""
        use_flat = Spelling.prefer_flat if prefer_flat is None else prefer_flat
        mapping = LILYPOND_OF if use_flat else LILYPOND_OF_SHARP
        name = mapping[self.offset]
        if name == "r":
            return name
        marks = self.octave - 3
        if marks >= 0:
            return name + ("'" * marks)
        return name + ("," * (-marks))

    @abc.setter
    def abc(self, abc: str) -> None:
        """Set the ABC notation of this pitch."""
        if abc == "z":
            self.value = Rest()
            return
        name, suffix = (abc[0], abc[1:]) if abc[0].isalpha() else (abc[:2], abc[2:])
        if va := int(name[-1].islower()):
            name = name.upper()
        va += suffix.count("'") - suffix.count(",")
        self.value = 0
        self.offset = OFFSET_OF[name]
        self.octave = 4 + va

    @property
    def freq(self) -> float:
        """Return frequency in Hz (12-TET, A4=440)."""
        if isinstance(self.value, Rest):
            return 0.0
        return 440.0 * (2 ** ((self.value - 69) / 12))

    @classmethod
    def from_abc(cls, abc: str):
        """Create a new pitch from ABC notation"""
        pitch = cls(0)
        pitch.abc = abc
        return pitch


# shorthand
P = Pitch
