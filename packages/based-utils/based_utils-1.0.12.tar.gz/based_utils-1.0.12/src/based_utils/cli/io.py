import re
import sys
from functools import cache
from itertools import zip_longest
from os import get_terminal_size
from typing import TYPE_CHECKING, Self, SupportsIndex
from unicodedata import east_asian_width

from based_utils.data import filled_empty

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from os import terminal_size


type Lines = Iterable[str]


_ANSI_ESCAPE = "\x1b"


def ansi_escape(s: str) -> str:
    return f"{_ANSI_ESCAPE}[{s}"


def ansi_style(*values: int) -> str:
    return ansi_escape(f"{';'.join(str(v) for v in values)}m")


_ANSI_STYLE_REGEX = re.compile(rf"{_ANSI_ESCAPE}\[\d+(;\d+)*m")


type StringStyler = Callable[[str], str]


def strip_ansi_style(s: str) -> str:
    return _ANSI_STYLE_REGEX.sub("", s)


def apply_ansi_style(*values: int) -> StringStyler:
    def wrapper(s: str) -> str:
        return f"{ansi_style(*values)}{s}{ansi_style(0)}"

    return wrapper


@cache
def term_size() -> terminal_size:
    return get_terminal_size()


_LINE_UP = ansi_escape("A")
_LINE_CLEAR = ansi_escape("2K")


def clear_lines(amount: int) -> None:
    for _ in range(amount):
        sys.stdout.write(_LINE_UP + _LINE_CLEAR)


def write_lines(lines: Iterable, *, crop_to_term: bool = False) -> int:
    block = [str(line) for line in lines]
    height = len(block)
    if crop_to_term:
        # Could be nice to crop to width as well, but it seems
        # to me vertical cropping is a bit quirky now anyway.
        _max_width, max_height = get_terminal_size()
        height = min(max_height - 1, height)
    for line in block[-height:]:
        sys.stdout.write(f"{line}\n")
    return height


def visual_string_width(s: str) -> int:
    """
    Width a string would take in terminal output.

    >>> s, e = "Hello!", "🫠"
    >>> visual_string_width(s)
    6
    >>> visual_string_width(e)
    2
    >>> visual_string_width(f"{s} {e}")
    9
    """
    return sum(2 if east_asian_width(c) == "W" else 1 for c in strip_ansi_style(s))


class TerminalStr(str):
    _raw_strings: list[str]
    __slots__ = ("_raw_strings",)

    def __new__(cls, *values: object) -> Self:
        vs = [v if isinstance(v, str) else str(v) for v in values]
        instance = super().__new__(cls, "".join(vs))
        instance._raw_strings = vs
        return instance

    def __len__(self) -> int:
        return sum(visual_string_width(v) for v in self._raw_strings)

    @property
    def _raw_len(self) -> int:
        return sum(len(v) for v in self._raw_strings)

    @property
    def _len_diff(self) -> int:
        return len(self) - self._raw_len

    def ljust(self, width: SupportsIndex, fillchar: str = " ") -> TerminalStr:
        return TerminalStr(
            *[v.ljust(int(width) - self._len_diff, fillchar) for v in self._raw_strings]
        )

    def rjust(self, width: SupportsIndex, fillchar: str = " ") -> TerminalStr:
        return TerminalStr(
            *[v.rjust(int(width) - self._len_diff, fillchar) for v in self._raw_strings]
        )

    def center(self, width: SupportsIndex, fillchar: str = " ") -> TerminalStr:
        return TerminalStr(
            *[
                v.center(int(width) - self._len_diff, fillchar)
                for v in self._raw_strings
            ]
        )


class Table:
    def __init__(
        self,
        min_columns_widths: Iterable[int] = None,
        column_splits: Iterable[int] = None,
        style_table: Callable[[str], str] = None,
    ) -> None:
        self._min_columns_widths = min_columns_widths or []
        self._column_splits = column_splits or []
        self._style_table_cb = style_table

    def __call__(self, *table_rows: Iterable[object]) -> Iterator[str]:
        first, *rest = [tr for tr in table_rows if tr]
        trs: list[Iterable[object]] = [[], first, [], *rest, []]
        tr_strings: list[list[str]] = [[TerminalStr(v) for v in tr] for tr in trs]
        rows: list[list[str]] = list(filled_empty(tr_strings, ""))
        for r, row in enumerate(rows):
            yield "".join(self._row(row, r, len(rows) - 1, self._column_widths(rows)))

    def _style_table(self, table_element: str) -> str:
        if self._style_table_cb:
            return self._style_table_cb(table_element)
        return table_element

    def _column_widths(self, rows: list[list[str]]) -> Iterator[int]:
        max_cw = [max(len(s) for s in col) for col in zip(*rows, strict=True)]
        for cw, min_w in zip_longest(max_cw, self._min_columns_widths, fillvalue=0):
            yield max(cw, min_w)

    def _row(
        self,
        row: list[str],
        current_row: int,
        last_row: int,
        column_widths: Iterable[int],
    ) -> Iterator[str]:
        is_first = current_row == 0
        is_second = current_row == 2
        is_last = current_row == last_row
        is_table = is_first or is_second or is_last

        def left() -> str:
            return self._style_table(
                "╔" if is_first else "╠" if is_second else "╚" if is_last else "║"
            )

        def right() -> str:
            return self._style_table(
                "╗" if is_first else "╣" if is_second else "╝" if is_last else "║"
            )

        def center() -> str:
            return self._style_table(
                "╦" if is_first else "╬" if is_second else "╩" if is_last else "║"
            )

        yield left()

        for c, (s, w) in enumerate(zip(row, column_widths, strict=True), 1):
            line = ""
            line += self._style_table("═") * (w + 2) if is_table else f" {s.ljust(w)} "
            line += (
                f"{right()}  {left()}"
                if c in self._column_splits
                else right()
                if c == len(row)
                else center()
            )
            yield line
