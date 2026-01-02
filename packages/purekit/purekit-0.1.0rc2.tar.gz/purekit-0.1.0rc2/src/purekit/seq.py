__all__ = ("flatten",)

from collections import deque
from collections.abc import Iterable, Iterator
from typing import Any


def flatten(
    items: Iterable[Any],
    max_depth: int | None = None,
    atomic_types: type | tuple[type, ...] | None = None,
) -> Iterator[Any]:
    """Return an iterator that flattens arbitrarily-nested iterables."""
    # normalize atomic types (treat these as indivisible)
    if atomic_types is None:
        atomic_types_tuple: tuple[type, ...] = (str, bytes, bytearray)
    elif isinstance(atomic_types, type):
        atomic_types_tuple = (atomic_types,)
    else:
        # allow any iterable/tuple of types
        atomic_types_tuple = tuple(atomic_types)

    if max_depth is not None and max_depth < 0:
        raise ValueError(f"invalid {max_depth=!r}; expected >= 0 or None")

    stack = deque([(iter(items), 0)])
    while stack:
        iterator, depth = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            continue

        if (
            (max_depth is None or depth < max_depth)
            and isinstance(item, Iterable)
            and not isinstance(item, atomic_types_tuple)
        ):
            stack.append((iter(item), depth + 1))
        else:
            yield item
