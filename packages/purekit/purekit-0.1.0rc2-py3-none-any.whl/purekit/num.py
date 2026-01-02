__all__ = (
    "collatz",
    "dlog",
    "fibonacci",
    "is_divisible",
    "is_even",
    "is_odd",
    "pad",
    "sign",
    "signif",
)

import math
from collections.abc import Iterator

import purekit as pk


def collatz(n: int, /) -> Iterator[int]:
    """Return the Collatz sequence."""
    if not isinstance(n, int):
        raise TypeError(f"unsupported type {type(n).__name__!r}; expected int")
    if n < 1:
        raise ValueError(f"invalid value {n!r}; expected >= 1")

    while True:
        yield n
        if n == 1:
            break
        n = n // 2 if is_even(n) else 3 * n + 1


def dlog(number: int | float, /, kind: str = "log") -> int | float:
    """Return scaled value whose integer part equals the original main digit count."""
    choices = ("log", "int", "linear")
    if kind not in choices:
        raise pk.exceptions.InvalidChoiceError(kind, choices)

    x = abs(number)
    fx = 1 + math.log10(x) if x >= 0.1 else 0.0

    match kind:
        case "log":
            return fx

        case "int":
            return math.floor(fx)

        case "linear":
            n = math.floor(fx)
            y0, y1 = n, n + 1
            x0, x1 = 10 ** (n - 1), 10**n
            return (y0 * (x1 - x) + y1 * (x - x0)) / (x1 - x0) if x >= 0.1 else 0.0


def fibonacci(a: int = 0, b: int = 1, /) -> Iterator[int]:
    """Return the Fibonacci sequence."""
    yield a
    yield b
    while True:
        c = a + b
        yield c
        a, b = b, c


def is_divisible(number: int, by: int) -> bool:
    """Return True if number is evenly divisible by the specified integer."""
    return number % by == 0


def is_even(number: int | float, /) -> bool:
    """Return True if number is even."""
    return number % 2 == 0


def is_odd(number: int | float, /) -> bool:
    """Return True if number is odd."""
    return number % 2 != 0


def pad(lower: float, upper: float, fraction: float = 0.05) -> tuple[float, float]:
    """Return the interval (lower, upper) expanded by the given fractional margin."""
    lo = float(lower)
    hi = float(upper)
    if lo > hi:
        lo, hi = hi, lo

    span = hi - lo
    if span == 0.0:
        return lo, hi

    margin = fraction * span
    return lo - margin, hi + margin


def sign(number: int | float, /) -> float:
    """Return the sign of a number."""
    if math.isnan(number):
        return number

    if number == 0:
        return 0.0

    return math.copysign(1, number)


def signif(number: int | float, num_digits: int) -> int | float:
    """Return the input number rounded to the specified number of significant digits."""
    if not math.isfinite(number) or number == 0:
        return number

    if not isinstance(num_digits, int):
        raise TypeError(
            f"unsupported type for num_digits {type(num_digits).__name__!r}"
        )

    if num_digits < 1:
        raise ValueError(f"invalid {num_digits=!r}; expected >= 1")

    magnitude = math.floor(math.log10(abs(number)))
    n_digits = num_digits - magnitude - 1
    return round(number, n_digits)
