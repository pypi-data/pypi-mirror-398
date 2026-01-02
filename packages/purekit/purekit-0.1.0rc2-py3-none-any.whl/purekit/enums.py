__all__ = ("EnumMixin",)

from enum import Enum
from typing import Any, TypeVar

import purekit as pk

T = TypeVar("T", bound=Enum)


class EnumMixin(Enum):
    @classmethod
    def all(cls: type[T]) -> tuple[T, ...]:
        """Return a tuple of all members of the enum class."""
        return tuple(mbr for mbr in cls)

    @classmethod
    def names(cls) -> tuple[str, ...]:
        """Return a tuple of all member names."""
        return tuple(mbr.name for mbr in cls)

    @classmethod
    def values(cls) -> tuple[Any, ...]:
        """Return a tuple of all member values."""
        return tuple(mbr.value for mbr in cls)

    @classmethod
    def get_by_name(cls: type[T], name: str) -> T:
        """Return an enum member by its name."""
        try:
            return cls[name]
        except KeyError as exc:
            raise pk.exceptions.InvalidChoiceError(name, cls.names()) from exc

    @classmethod
    def get_by_value(cls: type[T], value: Any) -> T:
        """Return an enum member by its value."""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"no {cls.__name__} member found for value {value!r}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name} (value: {self.value})"
