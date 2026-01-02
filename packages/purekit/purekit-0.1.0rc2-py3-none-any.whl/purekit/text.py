__all__ = ("char_diff", "concat", "findall", "headline", "numstr", "remove_punctuation")

import itertools
import math
import re
from collections.abc import Iterable, Iterator

import purekit as pk


def char_diff(string1: str, string2: str, /) -> str:
    """Return a three-line string highlighting character differences with '|'."""
    markers = "".join(
        "|" if a != b else " "
        for a, b in itertools.zip_longest(string1, string2, fillvalue="")
    )
    if "|" not in markers:
        markers = ""
    return "\n".join((string1, markers, string2))


def concat(strings: Iterable[str | None], sep: str = " ") -> str:
    """Return concatenated string excluding None values."""
    return sep.join(
        item if isinstance(item, str) else str(item)
        for item in pk.seq.flatten(strings)
        if item is not None
    )


def findall(
    strings: Iterable[str],
    pattern: str | re.Pattern,
    flags: int = re.IGNORECASE,
) -> Iterator[list[str]]:
    """Return an iterator of lists with regex matches for each string."""
    regex = pattern if isinstance(pattern, re.Pattern) else re.compile(pattern, flags)
    for next_string in strings:
        yield regex.findall(next_string)


def grep(
    strings: Iterable[str],
    pattern: str | re.Pattern,
    flags: int = re.IGNORECASE,
) -> Iterator[str]:
    """Return an iterator of strings that match the regex."""
    regex = pattern if isinstance(pattern, re.Pattern) else re.compile(pattern, flags)
    for next_string in strings:
        if regex.search(next_string):
            yield next_string


def headline(title: str, width: int = 79, pad_char: str = "-", min_pad: int = 3) -> str:
    """Return a centered headline string."""
    inner_title = f" {title} "
    if width < len(inner_title):
        width = len(inner_title) + 2 * min_pad
    return inner_title.center(width, pad_char)


def numstr(value: int | float, /) -> str:
    """Return the number string with underscores for thousands grouping."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"unsupported type {type(value).__name__!r}")

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return str(value)

    sign = "-" if value < 0 else ""
    value = abs(value)

    integer = int(value)
    frac = value - integer
    integer_str = f"{integer:_}"

    if frac == 0:
        return f"{sign}{integer_str}"

    # limit fractional digits, avoid scientific notation, strip trailing zeros
    frac_str = f"{frac:g}".rstrip("0").lstrip("0")
    return f"{sign}{integer_str}{frac_str}"


def remove_punctuation(input_string: str, /) -> str:
    """Return the input string with all punctuation characters removed."""
    from string import punctuation

    return input_string.translate(str.maketrans("", "", punctuation))
