"""Contracts a mutation round showed were not pinned elsewhere."""

from __future__ import annotations

import tracemalloc
from collections.abc import Callable
from typing import Any

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


class _Logged(MultiDict[str, int]):
    def __init__(self, initial: list[tuple[str, int]]) -> None:
        self.log: list[tuple[str, str]] = []
        super().__init__(initial)

    def __getitem__(self, key: str) -> int:
        self.log.append(("get", key))
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: int) -> None:
        self.log.append(("set", key))
        super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        self.log.append(("del", key))
        super().__delitem__(key)


def test_get_pop_and_setdefault_go_through_the_item_hooks_like_the_mixins() -> None:
    md = _Logged([("a", 1)])
    md.get("a")
    md.get("zz")
    md.pop("a")
    md.setdefault("b", 2)
    md.pop("q", None)
    assert md.log == [
        ("get", "a"), ("get", "zz"), ("get", "a"), ("del", "a"),
        ("get", "b"), ("set", "b"), ("get", "q"),
    ]  # fmt: skip


def test_mixed_equality_folds_with_lower_not_casefold() -> None:
    assert MultiDict([("\u00df", 1)]) != CIMultiDict([("SS", 1)])
    assert CIMultiDict([("SS", 1)]) != MultiDict([("\u00df", 1)])
    assert MultiDict([("\u212a", 1)]) == CIMultiDict([("k", 1)])


def test_the_values_view_sees_every_value_not_only_first_ones() -> None:
    values = MultiDict([("a", 1), ("a", 2)]).allvalues()
    assert 2 in values and 3 not in values


@pytest.mark.parametrize(
    "call",
    [
        lambda md: md["k"],
        lambda md: md.__delitem__("k"),
        lambda md: md.pop("k"),
        lambda md: md.getone("k"),
        lambda md: md.popone("k"),
        lambda md: md.popall("k"),
    ],
)
def test_key_error_carries_the_key_passed(call: Any) -> None:
    with pytest.raises(KeyError) as caught:
        call(MultiDict([("a", 1)]))
    assert caught.value.args == ("k",)


def test_unhashable_keys_raise_type_error_through_get_pop_and_setdefault() -> None:
    md: MultiDict[Any, int] = MultiDict()
    calls: list[Callable[[], object]] = [
        lambda: md.get([]), lambda: md.pop([], 1), lambda: md.setdefault([], 1)
    ]  # fmt: skip
    for call in calls:
        with pytest.raises(TypeError):
            call()
    assert not md


class _Picky(MultiDict[str, int]):
    def __getitem__(self, key: str) -> int:
        if key == "bad":
            raise ValueError("refused")
        return super().__getitem__(key)


def test_only_key_error_from_the_item_hook_means_absent() -> None:
    md = _Picky()
    calls: list[Callable[[], object]] = [
        lambda: md.get("bad"), lambda: md.pop("bad", 1), lambda: md.setdefault("bad", 1)
    ]  # fmt: skip
    for call in calls:
        with pytest.raises(ValueError, match="refused"):
            call()
    assert not md
