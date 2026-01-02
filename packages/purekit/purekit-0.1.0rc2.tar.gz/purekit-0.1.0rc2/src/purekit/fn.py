__all__ = ("identity", "pipe")

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

T = TypeVar("T")


def identity(value: T, /) -> T:
    """Return value unchanged."""
    return value


def pipe(value: T, functions: Iterable[Callable[[Any], Any]]) -> Any:
    """Return the result of applying a sequence of functions to the initial value."""
    result: Any = value
    for function in functions:
        result = function(result)
    return result
