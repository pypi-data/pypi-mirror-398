__all__ = ("PurekitError", "InvalidChoiceError")

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class PurekitError(Exception):
    """Base exception for all errors raised by purekit."""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = self.__class__.__name__
        self.message: str = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


class InvalidChoiceError(PurekitError, ValueError):
    """Raised when a value is not one of the allowed choices."""

    __slots__ = ("value", "choices")

    value: T
    choices: Sequence[T] | None

    def __init__(self, value: T, choices: Sequence[T] | None = None) -> None:
        self.value = value
        self.choices = choices
        msg = f"invalid choice {self.value!r}"
        if self.choices is not None:
            msg += f"; expected a value from {self.choices!r}"
        super().__init__(msg)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(value={self.value!r}, choices={self.choices!r})"
        )
