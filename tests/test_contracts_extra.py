"""Contracts a mutation round showed were not pinned elsewhere."""

from __future__ import annotations

import tracemalloc

import pytest

from typedmultidict import CIMultiDict, MultiDict


def test_holes_left_by_removals_are_swept_so_memory_stays_flat() -> None:
    md: CIMultiDict[int] = CIMultiDict([("Via", 0)])
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        for i in range(200_000):
            md.add("via", i)
            md.popone("VIA")
        grown = tracemalloc.get_traced_memory()[0] - before
    finally:
        tracemalloc.stop()
    assert len(md.allitems()) == 1 and md.getall("via") == [199_999]
    assert grown < 100_000, grown


def test_an_iterator_still_fails_after_clear_and_refill() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    keys = iter(md)
    md.clear()
    md.add("x", 1)
    md.add("y", 2)
    with pytest.raises(RuntimeError, match="changed during iteration"):
        next(keys)


def test_an_iterator_still_fails_after_init_runs_again() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    pairs = iter(md.allitems())
    md.__init__([("b", 2)])  # type: ignore[misc]
    with pytest.raises(RuntimeError, match="changed during iteration"):
        next(pairs)


def test_repeated_equal_values_still_differ_from_a_plain_mapping() -> None:
    assert MultiDict([("a", 1), ("a", 1)]) != {"a": 1}
    assert CIMultiDict([("A", 1), ("a", 1)]) != {"a": 1}
    assert MultiDict([("a", 1)]) == {"a": 1}
