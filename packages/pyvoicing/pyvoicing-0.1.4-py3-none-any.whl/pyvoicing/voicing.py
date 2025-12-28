from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .chroma import Chroma
from .pitch import Pitch

if TYPE_CHECKING:
    from .interval import Interval


class Voicing:
    """Represents a musical voicing (collection of pitches possibly with a root)."""

    def __init__(
        self,
        pitches: Union[list[Union[int, str, Chroma, Pitch]], str] = [],
        root: Union[int, str, Chroma, Pitch, Voicing, None] = None,
    ):
        if isinstance(pitches, str):
            pitches = pitches.split(" ")
        self.pitches = [Pitch(_) for _ in pitches]
        if root is None and isinstance(pitches, Voicing):
            self.root = pitches.root
        else:
            self.root = root

    @property
    def root(self) -> Chroma:
        return self._root

    @root.setter
    def root(self, value: Union[int, str, Chroma, Pitch, None]) -> None:
        self._root = None if value is None else Chroma(value)

    @property
    def int_list(self):
        return [_.value for _ in self]

    @property
    def csv(self) -> str:
        return ",".join(str(_.value) for _ in self)

    @csv.setter
    def csv(self, csv: str, sep=",") -> None:
        self.pitches = [Pitch(int(_)) for _ in csv.split(sep)]

    @classmethod
    def from_csv(cls, csv: str):
        v = cls()
        v.csv = csv
        return v

    def __str__(self) -> str:
        return f'{self.root}{self.quality()}[{" ".join([str(_) for _ in self])}]'

    def __repr__(self) -> str:
        if self.root is None:
            return f"Voicing('{' '.join(str(_) for _ in self)}')"
        return f"Voicing('{' '.join(str(_) for _ in self)}', '{self.root}')"

    def __hash__(self) -> int:
        return hash(str(self))

    def __len__(self) -> int:
        """Get the number of pitches in the voicing."""
        return len(self.pitches)

    def __iter__(self):
        """Iterate through the pitches in the voicing."""
        return iter(self.pitches)

    def __eq__(self, other: Any) -> bool:
        """Compare if two voicings are equivalent (taking into account transposition)."""
        if not isinstance(other, Voicing) or len(self) != len(other):
            return False
        if len(self) == 0:
            return True
        # Transpose to the same root and compare pitches
        interval = self[0].distance_to(other[0])
        return (self >> interval).pitches == other.pitches

    def __gt__(self, other: Voicing) -> bool:
        """Check if this voicing is a superset of the other."""
        for pitch in other:
            if pitch not in self:
                return False
        return len(self) > len(other)

    def __ge__(self, other: Voicing) -> bool:
        """Check if this voicing is a superset of or equal to the other."""
        return self > other or self == other

    def __mod__(self, value: Union[int, str, "Interval"]) -> list[Pitch]:
        """Find pitches that form the given interval with higher pitches."""
        return self.find_interval(value)

    def find_interval(self, value: Union[int, str, "Interval"]) -> list[Pitch]:
        """Find pitches that form the given interval with higher pitches."""
        from .interval import Interval

        target = Interval(value).distance

        lowers = []
        for i in range(len(self) - 1):
            for j in range(i + 1, len(self)):
                if self[i].distance_to(self[j]).distance == target:
                    lowers.append(Pitch(self[i]))
        return lowers

    def add(self, value: Union[int, str, Pitch, list[Pitch], Voicing]) -> Voicing:
        """Return a new voicing with pitch(es) added."""
        ret = Voicing(self)
        match value:
            case int() | str() | Pitch():
                ret.pitches.append(Pitch(value))
            case list() | Voicing():
                for pitch in value:
                    ret.pitches.append(Pitch(pitch))
            case _:
                raise TypeError(
                    "expected value of type int|str|Pitch|list[Pitch]|Voicing"
                )
        ret.pitches.sort()
        return ret

    def remove(self, value: Union[str, Pitch, list[Pitch], Voicing]) -> Voicing:
        """Return a new voicing with pitch(es) removed."""
        ret = Voicing(self)
        match value:
            case str():
                p = Pitch(value)
                if p in self:
                    ret.pitches.remove(p)
            case Pitch():
                if value in self:
                    ret.pitches.remove(value)
            case list():
                for v in value:
                    p = Pitch(v)
                    if p in self:
                        ret.pitches.remove(p)
            case Voicing():
                for pitch in value:
                    if pitch in self:
                        ret.pitches.remove(pitch)
            case _:
                raise TypeError("expected value of type str|Pitch|list[Pitch]|Voicing")
        return ret

    def __add__(self, value: Union[int, str, Pitch, list[Pitch], Voicing]) -> Voicing:
        """Add pitch(es) to the voicing."""
        return self.add(value)

    def __sub__(self, value: Union[str, Pitch, list[Pitch], Voicing]) -> Voicing:
        """Remove pitch(es) from the voicing."""
        return self.remove(value)

    def __mul__(self, n: int) -> list[Voicing]:
        """Return a list of copies."""
        return [Voicing(self) for i in range(n)]

    def __rshift__(self, value: Union[int, str, "Interval"]) -> Voicing:
        """Transpose the voicing upwards."""
        return self.transpose(value)

#    def __truediv__(self, value: Union[int, str, 'Interval', Chroma]) -> Voicing:
#        """Transpose the voicing downwards."""
#        from .interval import Interval
#        ret = Voicing(self)
#        ret.root -= value
#        for i in range(len(ret)):
#            ret[i] /= value
#        return ret

    def __lshift__(self, value: Union[int, str, "Interval", Chroma]) -> Voicing:
        """Transpose the voicing downwards."""
        return self.transpose_down(value)

    def transpose(self, value: Union[int, str, "Interval"]) -> Voicing:
        """Transpose the voicing upwards."""
        return Voicing(
            [pitch.transpose(value) for pitch in self],
            None if self.root is None else self.root.transpose(value),
        )

    def transpose_down(self, value: Union[int, str, "Interval", Chroma]) -> Voicing:
        """Transpose the voicing downwards."""
        from .interval import Interval

        interval = value if isinstance(value, Interval) else Interval(value)
        return Voicing(
            [pitch.transpose_down(interval) for pitch in self],
            None if self.root is None else self.root.transpose_down(interval),
        )

    def __floordiv__(self, target: Union[int, Pitch]) -> Voicing:
        """Transpose the voicing to a specific target pitch/value."""
        return self.to_root(target)

    def to_root(self, target: Union[int, Pitch]) -> Voicing:
        """Transpose the voicing so the root lands on the target pitch/value."""
        if len(self) == 0:
            return Voicing(self)
        if self.root is None:
            return Voicing(self)
        interval = self.root.distance_to(self[0].chroma)
        root = self[0] << interval
        return self >> root.distance_to(target)

    def matrix(self) -> list[list[int]]:
        """Compute the interval matrix between all pitches in the voicing.

        Returns:
            A 2D array where each cell represents the interval between two pitches
        """
        if len(self) <= 1:
            return []
        interval_matrix = []
        for i in range(len(self) - 1):
            interval_matrix.append([])
            for j in range(len(self)):
                if j > i:
                    interval = self[i].distance_to(self[j]).distance
                else:
                    interval = 0
                interval_matrix[i].append(interval)
        return interval_matrix

    def index(self, key: Union[int, str, Pitch, Chroma]) -> int:
        if isinstance(key, str):
            if any(_.isdigit() for _ in key):
                # Look for a pitch name with octave like "C4"
                names = [str(pitch) for pitch in self]
                return names.index(key) if key in names else -1
            # Look for a chroma name
            key = Chroma(key)

        try:
            return self.pitches.index(key)
        except ValueError:
            return -1

    def __getitem__(self, key: Union[int, str, Pitch, Chroma]) -> Optional[Pitch]:
        """Get a pitch by index, name, or object.

        Args:
            key: The index or pitch to retrieve

        Returns:
            The pitch at the given index or None if not found
        """
        if isinstance(key, int):
            return self.pitches[key]
        idx = self.index(key)
        return self.pitches[idx] if idx >= 0 else None

    def __delitem__(self, key: Union[int, str, Pitch, Chroma]) -> None:
        """Remove a pitch from the voicing.

        Args:
            key: The index or pitch to remove
        """
        if isinstance(key, int):
            del self.pitches[key]
        else:
            idx = self.index(key)
            if idx >= 0:
                del self.pitches[idx]

    def __setitem__(
        self, key: Union[int, str, Pitch, Chroma], value: Union[int, Pitch]
    ) -> None:
        """Set a pitch at the given index or replace a pitch.

        Args:
            key: The index or pitch to replace
            value: The new pitch
        """
        if isinstance(key, int):
            self.pitches[key] = Pitch(value)
        else:
            idx = self.index(key)
            if idx >= 0:
                self.pitches[idx] = Pitch(value)

    @property
    def abc(self) -> list[str]:
        return [_.abc for _ in self]

    def spell(self, prefer_flat: Optional[bool] = None) -> list[str]:
        """Return pitch spellings using the preferred spelling."""
        return [pitch.spell(prefer_flat=prefer_flat) for pitch in self]

#    def voice(self, pitch: Pitch):
#        """Closest voice to the given pitch"""
#        if len(self) == 0:
#            return None
#        distance_from_pitch = lambda i: abs(self.pitches[i]-pitch)
#        return min(range(len(self)), key=distance_from_pitch)

    @property
    def drop2(self):
        assert len(self) == 4
        return Voicing((self[2]<<12, self[0], self[1], self[3]), self.root)

    @property
    def drop3(self):
        assert len(self) == 4
        return Voicing((self[1]<<12, self[0], self[2], self[3]), self.root)

    @property
    def drop24(self):
        assert len(self) == 4
        return Voicing((self[0]<<12, self[2]<<12, self[1], self[3]), self.root)

    def __invert__(self) -> list[int]:
        """Return MIDI values for all pitches in the voicing."""
        return [_.value for _ in self]

    @property
    def tones(self) -> list[str]:
        """Analyze chord tones relative to the root."""
        if len(self) == 0 or self.root is None:
            return []
        offsets = [_.offset for _ in (self << self.root.offset)]
        has = lambda *values: any(_ in offsets for _ in values)
        tones = [
            {
                0: "1",
                1: "b9",
                2: "9" if has(3, 4) else "sus2",
                3: "#9" if has(4) else "min3",
                4: "maj3",
                5: "11" if has(3, 4) else "sus4",
                6: "#11" if has(4, 7) else "b5",
                7: "5",
                8: "b13" if has(3, 7, 10) else "#5",
                9: "13" if has(10, 11) else "6",
                10: "min7" if has(3) else "dom7",
                11: "maj7",
            }[_]
            for _ in offsets
        ]
        if "b5" in tones and "6" in tones:
            tones = ["dim7" if _ == "6" else _ for _ in tones]
        return tones

    def quality(self) -> str:
        return ""
#        if self.root is None or len(self) < 2:
#            return ''
#        tones = ~self
#        base = ''
#        tensions = ''
#        return base + tensions


# shorthand
V = Voicing
