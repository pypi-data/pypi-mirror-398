from dataclasses import dataclass
from itertools import islice, tee
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterator


class NoCycleFoundError(Exception):
    pass


@dataclass(frozen=True)
class Cycle:
    start: int
    length: int


def _floyd[T](it: Iterator[T]) -> Cycle:
    """
    Floyd's ("tortoise and hare") cycle detection algorithm.

    👉 https://en.wikipedia.org/wiki/Cycle_detection#Floyd's_tortoise_and_hare
    """
    it_t1, it_t2, it_ = tee(it, 3)
    # 🐇 will walk at "double speed" (i.e. skipping every other step).
    it_h = islice(it_, 1, None, 2)

    for tortoise, hare in zip(it_t1, it_h, strict=True):
        # After 🐢 has walked [s] steps, the animals meet again. At this point:
        # 1. 🐇 has walked one full cycle [c] more than 🐢
        # 2. Going twice as fast, 🐇 has walked s x 2 steps, or s more than 🐢
        # Which means s = c --> 🐢 has walked exactly one cycle.
        # --> d + c = 2 x d; (d + c) - d
        if tortoise == hare:
            break

    # At this point, 🐢II leaves from the beginning as well.
    for cycle_start, (tortoise_1, tortoise_2) in enumerate(
        zip(it_t1, it_t2, strict=True)
    ):
        if tortoise_1 != tortoise_2:
            continue
        # They should meet as soon as the cycle starts, since:
        # 🐢I has walked:
        # - one full cycle [c] from beginning [S], or
        # - [d] steps from start of cycle [C]
        # Remaining for 🐢I = steps to C = c - d
        # Remaining for 🐢II = steps from S to C = c - d
        for cycle_length, tortoise_1_ in enumerate(it_t1, 1):
            # At C, 🐢II pauses while 🐢I keeps on walking.
            if tortoise_1_ != tortoise_2:
                continue
            # They meet again after 🐢I has walked another full cycle.
            return Cycle(cycle_start, cycle_length)

    raise NoCycleFoundError


def _brent[T](it: Iterator[T]) -> Cycle:
    """
    Brent's cycle detection algorithm.

    👉 https://en.wikipedia.org/wiki/Cycle_detection#Brent's_algorithm
    """
    it_, it_t2, it_h = tee(it, 3)
    steps_until_snapshot = cycle_length = 1
    snapshot: T | None = None

    for hare in it_h:
        if hare == snapshot:
            break

        if cycle_length == steps_until_snapshot:
            # By making a snapshot every time the number of steps doubles, we
            # can find the cycle length within walking that same length twice
            # (and only have to check one snapshot at a time):
            # 🐇
            # x
            #   🐇🐇
            #   x
            #       🐇🐇🐇🐇
            #       x
            #               🐇🐇🐇🐇🐇🐇🐇🐇
            #               x
            snapshot = hare
            steps_until_snapshot *= 2
            cycle_length = 0
        cycle_length += 1

    # At this point, 🐢I leaves from the beginning [S].
    it_t1 = islice(it_, cycle_length, None)
    # After 🐢I has walked one cycle length, 🐢II leaves from S as well.
    for cycle_start, (tortoise_1, tortoise_2) in enumerate(
        zip(it_t1, it_t2, strict=True)
    ):
        if tortoise_1 != tortoise_2:
            continue
        # They should meet as soon as the cycle starts
        # (for reasoning why: see comments at `_floyd()` algo above).
        return Cycle(cycle_start, cycle_length)

    raise NoCycleFoundError


def detect_cycle[T](
    it: Iterator[T], *, algorithm: Literal["floyd", "brent"] = "brent"
) -> Cycle:
    match algorithm:
        case "floyd":
            return _floyd(it)
        case "brent":
            return _brent(it)
