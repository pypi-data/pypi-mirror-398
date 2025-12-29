from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

type NoteName = Literal[
    "a",
    "a-sharp",
    "b-flat",
    "b",
    "c",
    "c-sharp",
    "d-flat",
    "d",
    "d-sharp",
    "e-flat",
    "e",
    "f",
    "f-sharp",
    "g-flat",
    "g",
    "g-sharp",
    "a-flat",
]

_NOTES: Mapping[NoteName, int] = {
    "a": 0,
    "a-sharp": 1,
    "b-flat": 1,
    "b": 2,
    "c": -9,
    "c-sharp": -8,
    "d-flat": -8,
    "d": -7,
    "d-sharp": -6,
    "e-flat": -6,
    "e": -5,
    "f": -4,
    "f-sharp": -3,
    "g-flat": -3,
    "g": -2,
    "g-sharp": -1,
    "a-flat": -1,
}

A0 = 27.5


@dataclass(frozen=True)
class Note:
    note: NoteName
    octave: int

    @cached_property
    def frequency(self) -> float:
        return A0 * 2 ** (self.octave + _NOTES[self.note] / 12)


# Piano staff ranges:
#          𝄢           𝄞
# |  |  |  |  |  .  |  |  |  |  |
# G2          A3 C4 E4          F5

INSTRUMENT_RANGES = {
    "piano": (Note("a", 0), Note("c", 7)),
    "guitar": (Note("e", 2), Note("e", 6)),  # E2 A2 D3 G3 B3 E4
    "guitar-baritone": (Note("b", 1), Note("b", 5)),  # B1 E2 A2 D3 F#3 B3
    "bass-guitar-4-strings": (Note("e", 1), Note("g", 4)),  # E1 A1 D2 G2
    "bass-guitar-5-strings": (Note("b", 0), Note("g", 4)),  # B0 E1 A1 D2 G2
    "cello": (Note("c", 2), Note("d", 6)),  # C2 G2 D3 A3
}
"""
>>> for i, (n1, n2) in INSTRUMENT_RANGES.items():
...     print(f"{n1.frequency:.2f} - {n2.frequency:.2f} <-- {i}")
...
27.50 - 2093.00 <-- piano
82.41 - 1318.51 <-- guitar
61.74 - 987.77 <-- guitar-baritone
41.20 - 392.00 <-- bass-guitar-4-strings
30.87 - 392.00 <-- bass-guitar-5-strings
65.41 - 1174.66 <-- cello
"""
