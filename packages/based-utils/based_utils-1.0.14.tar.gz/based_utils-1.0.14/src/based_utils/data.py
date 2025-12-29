from collections import deque
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping


def ignore[T](v: T) -> T:
    return v


@overload
def try_convert[T, R](cls: Callable[[T], R], val: T, *, default: R) -> R: ...


@overload
def try_convert[T, R](
    cls: Callable[[T], R], val: T, *, default: None = None
) -> R | None: ...


def try_convert[T, R](cls: Callable[[T], R], val: T, *, default: R = None) -> R | None:
    try:
        return cls(val)
    except ValueError:
        return default


def consume(iterator: Iterator) -> None:
    """
    Consume an iterator entirely.

    We will achieve this by feeding the entire iterator into a zero-length deque.
    Redefined here to avoid needing more_itertools for just this function.
    """
    deque(iterator, maxlen=0)


def compose_number(numbers: Iterable[int]) -> int:
    return int("".join(str(n) for n in numbers))


def bits_to_int(items: Iterable[object]) -> int:
    """
    Convert boolean/int array -> number.

    >>> bits_to_int([True, False, 0, 1, "", 23, "je moeder"])
    75
    """
    return int("".join(f"{bool(i):b}" for i in items), 2)


def int_to_bits(i: int, *, zero_pad_to_length: int = 0) -> list[bool]:
    """
    Convert number -> boolean array.

    >>> int_to_bits(75)
    [True, False, False, True, False, True, True]
    >>> int_to_bits(75, zero_pad_to_length=10)
    [False, False, False, True, False, False, True, False, True, True]
    """
    s = f"{i:b}"
    if zero_pad_to_length:
        s = s.zfill(zero_pad_to_length)
    return [c == "1" for c in s]


def invert_dict[K, V](d: Mapping[K, V]) -> dict[V, K]:
    return {v: k for k, v in d.items()}


def grouped_by_key[K, V](pairs: Iterable[tuple[K, V]]) -> dict[K, list[V]]:
    """
    Group items by key(item).

    >>> grouped_by_key(
    ...     [
    ...         ("Alice", 3),
    ...         ("Bob", 6),
    ...         ("Charles", 4),
    ...         ("Alice", 8),
    ...         ("Charles", 5),
    ...         ("Bob", 2),
    ...         ("Charles", 7),
    ...         ("Alice", 9),
    ...         ("Charles", 1),
    ...     ]
    ... )
    {'Alice': [3, 8, 9], 'Bob': [6, 2], 'Charles': [4, 5, 7, 1]}
    """
    result: dict[K, list[V]] = {}
    for k, v in pairs:
        result.setdefault(k, []).append(v)
    return result


def filled_empty[T](rows: Iterable[Iterable[T]], value: T) -> Iterator[list[T]]:
    rows_seq = [list(row) for row in rows]
    max_width = max(len(row) for row in rows_seq)
    for row in rows_seq:
        yield [*row, *([value] * (max_width - len(row)))]


def _resample_dim(length: int, cropped: int, sample_ratio: float) -> Iterator[int]:
    for i in range(cropped - 1):
        yield round(i * sample_ratio)
    yield length - 1


def resample(
    size: tuple[int, int], crop_size: tuple[int, int]
) -> tuple[list[int], list[int]]:
    (w, h), (w_max, h_max) = size, crop_size
    crop_size = w_cropped, h_cropped = min(w, w_max), min(h, h_max - 1)
    if crop_size == size:
        return list(range(w - 1)), list(range(h - 1))

    sr_w, sr_h = [((n - 1) / (c - 1)) for n, c in zip(size, crop_size, strict=True)]
    xs, ys = _resample_dim(w, w_cropped, sr_w), _resample_dim(h, h_cropped, sr_h)
    return list(xs), list(ys)
