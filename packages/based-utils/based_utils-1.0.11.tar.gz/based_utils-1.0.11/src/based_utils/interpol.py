from functools import cached_property
from math import log, pi

FULL_CIRCLE = pi * 2


type _Bounds = tuple[float, float]


def trim(n: float, lower: float = 0, upper: float = 1) -> float:
    return min(max(lower, n), upper)


def trim_cyclic(n: float, period: float = 1) -> float:
    return n % period


class _MappingBounds:
    def __init__(self, start: float = 0, end: float = 1) -> None:
        self._start = start
        self._end = end

    @cached_property
    def _span(self) -> float:
        return self._end - self._start

    def value_at(self, f: float) -> float:
        return self._start + self._span * f

    def position_of(self, n: float) -> float:
        try:
            return (n - self._start) / self._span
        except ZeroDivisionError:
            return 0.0


class LinearMapping(_MappingBounds):
    def position_of(self, n: float, *, inside: bool = False) -> float:
        f = super().position_of(n)
        return trim(f, 0.0, 1.0) if inside else f


class LogarithmicMapping(LinearMapping):
    def __init__(self, start: float = 0, end: float = 1, base: float = 10) -> None:
        super().__init__(log(start, base), log(end, base))
        self._base = base

    def value_at(self, f: float) -> float:
        return self._base ** super().value_at(f)

    def position_of(self, n: float, *, inside: bool = False) -> float:
        return super().position_of(log(n, self._base), inside=inside)


class CyclicMapping(_MappingBounds):
    def __init__(self, start: float = 0, end: float = 1, period: float = 1) -> None:
        self._period = period
        start, end = self._trim(start), self._trim(end)

        # To ensure interpolation over the smallest angle,
        # phase shift {start} over whole periods, such that the
        # (absolute) difference between {start} <-> {end} <= 1/2 {period}.
        #
        #                          v------ period ------v
        #    -1                    0                    1                    2
        #     |                    |                    |     start < end:   |
        # Old:|                    |   B ~~~~~~~~~> E   |                    |
        # New:|                    |                E <~|~~ B' = B + period  |
        #     |    start > end:    |                    |                    |
        # Old:|                    |   E <~~~~~~~~~ B   |                    |
        # New:|  B - period =  B'~~|~> E                |                    |

        if abs(end - start) > period / 2:
            start += period if start < end else -period

        super().__init__(start, end)

    def _trim(self, n: float) -> float:
        return n % self._period

    def value_at(self, f: float) -> float:
        return self._trim(super().value_at(f))

    def position_of(self, n: float) -> float:
        return super().position_of(self._trim(n))


def mapped(f: float, bounds: _Bounds) -> float:
    return LinearMapping(*bounds).value_at(f)


def unmapped(n: float, bounds: _Bounds, *, inside: bool = False) -> float:
    return LinearMapping(*bounds).position_of(n, inside=inside)


def mapped_log(f: float, bounds: _Bounds, *, base: float = 10) -> float:
    return LogarithmicMapping(*bounds, base).value_at(f)


def unmapped_log(
    n: float, bounds: _Bounds, *, base: float = 10, inside: bool = False
) -> float:
    return LogarithmicMapping(*bounds, base).position_of(n, inside=inside)


def mapped_cyclic(f: float, bounds: _Bounds, *, period: float = 1) -> float:
    return CyclicMapping(*bounds, period).value_at(f)


def mapped_angle(f: float, bounds: _Bounds) -> float:
    """Shorthand for mapped_cyclic() for an angle (in radians) as period."""
    return mapped_cyclic(f, bounds, period=FULL_CIRCLE)


def unmapped_cyclic(n: float, bounds: _Bounds, *, period: float = FULL_CIRCLE) -> float:
    return CyclicMapping(*bounds, period).position_of(n)


def unmapped_angle(n: float, bounds: _Bounds) -> float:
    """Shorthand for unmapped_cyclic() for an angle (in radians) as period."""
    return unmapped_cyclic(n, bounds, period=FULL_CIRCLE)


class NumberMapping:
    def __init__(self, from_bounds: _MappingBounds, to_bounds: _MappingBounds) -> None:
        self._from_bounds = from_bounds
        self._to_bounds = to_bounds

    def map(self, n: float) -> float:
        return self._to_bounds.value_at(self._from_bounds.position_of(n))


def map_number(
    n: float, from_bounds: _MappingBounds, to_bounds: _MappingBounds
) -> float:
    return NumberMapping(from_bounds, to_bounds).map(n)
