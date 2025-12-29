from collections.abc import Callable
from itertools import chain, pairwise, repeat, takewhile, tee
from typing import TYPE_CHECKING

from more_itertools import before_and_after, split_when, transpose

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence


type Predicate[T] = Callable[[T], bool]


def filter_non_empty[T](items: Iterable[T]) -> Iterator[T]:
    return filter(lambda item: item, items)


def pairwise_circular[T](it: Iterable[T]) -> Iterator[tuple[T, T]]:
    a, b = tee(it)
    return zip(a, chain(b, (next(b),)), strict=True)


def tripletwise_circular[T](it: Iterable[T]) -> Iterator[tuple[T, T, T]]:
    a, b, c = tee(it, 3)
    return zip(a, chain(b, (next(b),)), chain(c, (next(c), next(c))), strict=True)


def repeat_transform[T](
    value: T,
    *,
    transform: Callable[[T], T],
    times: int = None,
    while_condition: Predicate[T] = None,
) -> Iterator[T]:
    if while_condition:
        yield from takewhile(
            while_condition, repeat_transform(value, transform=transform, times=times)
        )
    else:
        for _ in repeat(None) if times is None else repeat(None, times):
            value = transform(value)
            yield value


def first_when[T](it: Iterable[T], predicate: Predicate[T]) -> tuple[int, T]:
    for step, item in enumerate(it, 1):
        if predicate(item):
            return step, item
    raise StopIteration


def first_duplicate[T](it: Iterable[T]) -> tuple[int, T]:
    for i, (item1, item2) in enumerate(pairwise(it), 1):
        if item1 == item2:
            return i, item1
    raise StopIteration


def polarized[T](
    items: Iterable[T], predicate: Predicate[T]
) -> tuple[list[T], list[T]]:
    left: list[T] = []
    right: list[T] = []
    for item in items:
        (left if predicate(item) else right).append(item)
    return left, right


def equalized[T](
    items: Iterable[Sequence[T]], default_value: T, max_length: int = None
) -> Iterator[list[T]]:
    if max_length is None:
        max_length = max(len(item) for item in items)
    for item in items:
        yield [*item, *([default_value] * max(0, max_length - len(item)))]


def split_when_changed[T](
    items: Iterable[T], predicate: Predicate[T]
) -> Iterator[list[T]]:
    return split_when(items, lambda x, y: not predicate(x) and predicate(y))


def split_items[T](items: Iterable[T], *, delimiter: T = None) -> Iterator[list[T]]:
    """
    Split any iterable (not just string).

    >>> list(split_items([]))
    [[]]
    >>> list(split_items([1]))
    [[1]]
    >>> list(split_items([None]))
    [[], []]
    >>> list(split_items([1, 2, None]))
    [[1, 2], []]
    >>> list(split_items([None, 1, 2]))
    [[], [1, 2]]
    >>> list(split_items([1, None, 2]))
    [[1], [2]]
    >>> list(split_items([None, 1, None, 2, 3, None]))
    [[], [1], [2, 3], []]
    >>> list(split_items([1, None, None, 2, 3]))
    [[1], [], [2, 3]]
    >>> list(split_items([1, None, 2, 3, None, None, 4, 5, 6, None, None, None]))
    [[1], [2, 3], [], [4, 5, 6], [], [], []]
    >>> list(
    ...     split_items(
    ...         [1, 2, 3, 1, 1, 2, 2, 3, 3, 1, 1, 1, 2, 2, 2, 3, 3, 3], delimiter=3
    ...     )
    ... )
    [[1, 2], [1, 1, 2, 2], [], [1, 1, 1, 2, 2, 2], [], [], []]
    """
    it = iter(items)
    while True:
        segment, it = before_and_after(lambda i: i != delimiter, it)
        yield list(segment)
        try:
            next(it)
        except StopIteration:
            break


def rotated_cw[T](rows: Iterable[Iterable[T]]) -> Iterator[tuple[T, ...]]:
    return reversed(list(transpose(rows)))


def rotated_ccw[T](rows: Iterable[Iterable[T]]) -> Iterator[tuple[T, ...]]:
    return transpose(reversed(list(rows)))


# strings


def equalized_lines(
    lines: Iterable[str], *, fill_char: str = " ", max_length: int = None
) -> Iterator[str]:
    for line in equalized(lines, fill_char, max_length=max_length):
        yield "".join(line)


def transposed_lines(lines: Iterable[str]) -> Iterator[str]:
    for col in transpose(lines):
        yield "".join(col)


def split_at(s: str, pos: int) -> tuple[str, str]:
    return s[:pos], s[pos:]


def split_conditional[T](
    collection: list[T], condition: Callable[[T], bool]
) -> tuple[list[T], list[T]]:
    left = [item for item in collection if condition(item)]
    right = [item for item in collection if item not in left]
    return left, right
