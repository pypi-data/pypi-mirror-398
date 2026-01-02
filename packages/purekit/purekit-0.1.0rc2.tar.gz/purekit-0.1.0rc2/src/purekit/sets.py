__all__ = (
    "TwoSetSummary",
    "summarize",
    "dice",
    "jaccard",
    "overlap",
    "union",
    "intersect",
)

import itertools
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class TwoSetSummary(Generic[T]):
    """Immutable summary of two sets."""

    # input sets
    set1: frozenset[T]
    set2: frozenset[T]

    # derived sets
    union: frozenset[T]
    intersection: frozenset[T]
    set1_minus_set2: frozenset[T]
    set2_minus_set1: frozenset[T]
    sym_diff: frozenset[T]

    # similarity scores
    jaccard_score: float
    overlap_score: float
    dice_score: float

    # boolean predicates
    is_equal: bool
    is_disjoint: bool
    is_subset: bool
    is_strict_subset: bool


def summarize(set1: Iterable[T], set2: Iterable[T], /) -> TwoSetSummary[T]:
    """Return a summary of two given sets."""
    s1 = _freeze(set1)
    s2 = _freeze(set2)

    return TwoSetSummary(
        set1=s1,
        set2=s2,
        union=s1 | s2,
        intersection=s1 & s2,
        set1_minus_set2=s1 - s2,
        set2_minus_set1=s2 - s1,
        sym_diff=s1 ^ s2,
        jaccard_score=jaccard(s1, s2),
        overlap_score=overlap(s1, s2),
        dice_score=dice(s1, s2),
        is_equal=s1 == s2,
        is_disjoint=s1.isdisjoint(s2),
        is_subset=s1 <= s2,
        is_strict_subset=s1 < s2,
    )


def jaccard(set1: Iterable[T], set2: Iterable[T], /) -> float:
    """Return the Jaccard similarity score between two sets."""
    s1 = _freeze(set1)
    s2 = _freeze(set2)

    set1_size = len(s1)
    set2_size = len(s2)
    if set1_size == set2_size == 0:
        return 1.0

    inter_size = len(s1 & s2)
    union_size = set1_size + set2_size - inter_size
    if union_size == 0:
        return 0.0

    return inter_size / union_size


def overlap(set1: Iterable[T], set2: Iterable[T], /) -> float:
    """Return the overlap similarity score between two sets."""
    s1 = _freeze(set1)
    s2 = _freeze(set2)

    set1_size = len(s1)
    set2_size = len(s2)
    if set1_size == set2_size == 0:
        return 1.0

    smaller_size = min(set1_size, set2_size)
    if smaller_size == 0:
        return 0.0

    inter_size = len(s1 & s2)
    return inter_size / smaller_size


def dice(set1: Iterable[T], set2: Iterable[T], /) -> float:
    """Return the Dice similarity score between two sets."""
    s1 = _freeze(set1)
    s2 = _freeze(set2)

    set1_size = len(s1)
    set2_size = len(s2)
    if set1_size == set2_size == 0:
        return 1.0

    total_size = set1_size + set2_size
    if total_size == 0:
        return 0.0

    inter_size = len(s1 & s2)
    return (2 * inter_size) / total_size


def _freeze(items: Iterable[T], /) -> frozenset[T]:
    """Return a frozenset converted from any iterable."""
    return items if isinstance(items, frozenset) else frozenset(items)


def union(sets: Iterable[set[T]]) -> set[T]:
    """Return the union of all sets in the iterable."""
    return set(itertools.chain.from_iterable(sets))


def intersect(sets: Iterable[set[T]]) -> set[T]:
    """Return the intersection of all sets in the iterable."""
    iterator = iter(sets)
    try:
        result = set(next(iterator))
    except StopIteration:
        return set()

    for other in iterator:
        result.intersection_update(other)
        if not result:
            break

    return result
