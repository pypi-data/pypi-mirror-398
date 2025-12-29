import cmath
import math
from secrets import randbelow
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def randf(exclusive_upper_bound: float = 1, precision: int = 8) -> float:
    """
    Return a random float in the range [0, n).

    :param exclusive_upper_bound: n
    :param precision: Number of digits to round to
    :return: randomly generated floating point number
    """
    epb = 10 ** (math.ceil(math.log10(exclusive_upper_bound)) + precision)
    return randbelow(epb) * exclusive_upper_bound / epb


def solve_quadratic(a: float, b: float, c: float) -> tuple[float, float]:
    """
    Find x where ax^2 + bx + c = 0.

    >>> solve_quadratic(20.6, -10.3, 8.7)
    (0.25, 0.25)
    >>> solve_quadratic(2.5, 25.0, 20.0)
    (-9.12310562561766, -0.8768943743823392)
    """
    r = cmath.sqrt(b**2 - 4 * a * c).real

    def root(f: int) -> float:
        return (-b + r * f) / (2 * a)

    left, right = sorted([root(-1), root(1)])
    return left, right


def mods(x: int, y: int, shift: int = 0) -> int:
    return (x - shift) % y + shift


def compare(v1: int, v2: int) -> int:
    return (v1 < v2) - (v1 > v2)


def fractions(n: int, *, inclusive: bool = False) -> Iterator[float]:
    """
    Generate a range of n fractions from 0 to 1.

    :param n: amount of numbers generated
    :param inclusive: do we want to include 0 and 1 or not?
    :return: generated numbers

    >>> " ".join(f"{n:.3f}" for n in fractions(0))
    ''
    >>> " ".join(f"{n:.3f}" for n in fractions(0, inclusive=True))
    '0.000 1.000'
    >>> " ".join(f"{n:.3f}" for n in fractions(1))
    '0.500'
    >>> " ".join(f"{n:.3f}" for n in fractions(1, inclusive=True))
    '0.000 0.500 1.000'
    >>> " ".join(f"{n:.3f}" for n in fractions(7))
    '0.125 0.250 0.375 0.500 0.625 0.750 0.875'
    >>> " ".join(f"{n:.3f}" for n in fractions(7, inclusive=True))
    '0.000 0.125 0.250 0.375 0.500 0.625 0.750 0.875 1.000'
    """
    if inclusive:
        yield 0
    end = n + 1
    for i in range(1, end):
        yield i / end
    if inclusive:
        yield 1
