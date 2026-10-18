"""Keys and values that run code at awkward moments cannot corrupt a multi-dict."""

from __future__ import annotations

import tracemalloc
from collections.abc import Callable
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict

TARGET: dict[str, Any] = {}


class _Meddler:
    # Equal by number; the comparison numbered `armed` (1 = the next one) runs the write
    # stored in TARGET.
    armed = 0

    def __init__(self, n: int) -> None:
        self.n = n

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other: object) -> bool:
        if _Meddler.armed and isinstance(other, _Meddler):
            _Meddler.armed -= 1
            if not _Meddler.armed:
                TARGET["write"]()
        return isinstance(other, _Meddler) and other.n == self.n


def _consistent(md: MultiDict[Any, Any]) -> None:
    pairs = list(md.allitems())
    assert len(md.allitems()) == len(pairs)
    keys = list(md)
    assert len(md) == len(keys)
    for key in keys:
        assert md.getall(key) == [v for k, v in pairs if k is key or k == key]


WRITES: list[Callable[[MultiDict[Any, Any]], object]] = [
    lambda md: md.add(_Meddler(2), 2),
    lambda md: md.extend([(_Meddler(2), 2)]),
    lambda md: md.update([(_Meddler(1), 9)]),
    lambda md: md.merge([(_Meddler(2), 2)]),
    lambda md: md.__setitem__(_Meddler(1), 9),
    lambda md: md.__delitem__(_Meddler(1)),
    lambda md: md.popone(_Meddler(1)),
    lambda md: md.popall(_Meddler(1)),
    # A reused key, then a fresh one whose indexing is refused: update is all or nothing.
    lambda md: md.update([("x", 5), (_Meddler(2), 2)]),
    # pop and setdefault look the key up first: that lookup is part of the write.
    lambda md: md.pop(_Meddler(1)),
    lambda md: md.pop(_Meddler(2), None),
    lambda md: md.setdefault(_Meddler(1), 9),
    lambda md: md.setdefault(_Meddler(2), 2),
]


@pytest.mark.parametrize("write", WRITES)
@pytest.mark.parametrize("meddle", ["add", "popall", "clear"])
@pytest.mark.parametrize("nth", [1, 2, 3])
def test_a_key_comparison_that_writes_is_refused_and_leaves_no_damage(
    write: Callable[[MultiDict[Any, Any]], object], meddle: str, nth: int
) -> None:
    md: MultiDict[Any, Any] = MultiDict([(_Meddler(1), 1), ("x", 0)])
    calls = {"add": lambda: md.add("y", 1), "popall": lambda: md.popall("x"), "clear": md.clear}
    TARGET["write"] = calls[meddle]
    before = list(md.allitems())
    _Meddler.armed = nth
    try:
        write(md)
    except RuntimeError as error:
        assert "while one of its writes was running" in str(error)
        assert list(md.allitems()) == before
    else:
        assert _Meddler.armed, "the write ran although the comparison wrote"
    _Meddler.armed = 0
    _consistent(md)
    md.add("z", 1)
    md.popone("x")
    _consistent(md)


@pytest.mark.parametrize("meddle", ["add", "popall", "clear"])
@pytest.mark.parametrize("method", ["pop", "setdefault"])
def test_pop_and_setdefault_refuse_a_write_made_while_they_look_the_key_up(
    meddle: str, method: str
) -> None:
    md: MultiDict[Any, Any] = MultiDict([(_Meddler(1), 1), ("x", 0)])
    calls = {"add": lambda: md.add("y", 1), "popall": lambda: md.popall("x"), "clear": md.clear}
    TARGET["write"] = calls[meddle]
    _Meddler.armed = 1
    with pytest.raises(RuntimeError, match="while one of its writes was running"):
        getattr(md, method)(_Meddler(1), 9)
    _Meddler.armed = 0
    assert list(md.allitems()) == [(_Meddler(1), 1), ("x", 0)]
    _consistent(md)


def test_reads_from_a_key_comparison_are_allowed() -> None:
    md: MultiDict[Any, Any] = MultiDict([(_Meddler(1), 1), ("x", 0)])
    TARGET["write"] = lambda: md.getall("x")
    _Meddler.armed = 1
    md.add(_Meddler(2), 2)
    assert len(md) == 3
    _consistent(md)


def test_an_interrupt_inside_a_bulk_write_rolls_it_back() -> None:
    class Stop:
        def __hash__(self) -> int:
            raise KeyboardInterrupt

    md: MultiDict[Any, int] = MultiDict([("a", 1)])
    with pytest.raises(KeyboardInterrupt):
        md.extend([("a", 2), ("b", 3), (Stop(), 4)])
    assert list(md.allitems()) == [("a", 1)] and md.getall("a") == [1] and "b" not in md


def test_a_type_whose_name_raises_is_shown_as_a_question_mark() -> None:
    class Meta(type):
        @property
        def __name__(cls) -> str:  # type: ignore[override]
            raise RuntimeError("no name")

    odd: Any = Meta("Odd", (), {})()
    with pytest.raises(TypeError, match=r"pair: \?$"):
        MultiDict([odd])


def test_deleting_keys_sweeps_holes_so_memory_stays_flat() -> None:
    md: MultiDict[int, int] = MultiDict()
    tracemalloc.start()
    try:
        before = 0
        for cycle in range(1000):
            if cycle == 200:
                before = tracemalloc.get_traced_memory()[0]
            md.extend((i, i) for i in range(50))
            for i in range(50):
                del md[i]
        grown = tracemalloc.get_traced_memory()[0] - before
    finally:
        tracemalloc.stop()
    assert not md and grown < 60_000, grown


def test_items_view_membership_of_a_wrong_sized_tuple_is_false() -> None:
    pairs = MultiDict([("k", 1)]).allitems()
    long: Any = ("k", 1, 2)
    short: Any = ("k",)
    assert long not in pairs and short not in pairs and ("k", 1) in pairs


def test_lookups_fold_with_str_lower_whatever_a_subclass_says() -> None:
    class Shouty(str):
        def lower(self) -> str:
            return "something-else"

    headers: CIMultiDict[int] = CIMultiDict([("Accept", 1)])
    assert headers[Shouty("ACCEPT")] == 1 and Shouty("accept") in headers


def test_views_holding_their_own_multi_dict_print_without_recursion() -> None:
    md: MultiDict[str, Any] = MultiDict()
    md.add("pairs", md.allitems())
    md.add("values", md.allvalues())
    assert "..." in repr(md) and "..." in repr(md.allitems())


@pytest.mark.parametrize("view", ["keys", "items", "values", "allitems", "allvalues"])
def test_a_write_between_iter_and_next_is_caught_by_every_view(view: str) -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    iterator = iter(getattr(md, view)())
    md.add("k", 1)
    with pytest.raises(RuntimeError, match="changed during iteration"):
        next(iterator)
