"""Differential tests: where the names overlap, behaviour matches multidict and Werkzeug.

Both packages are optional test-only oracles; the tests skip when they are not installed.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from typedmultidict import CIMultiDict, MultiDict

KEYS = st.sampled_from(["a", "A", "b", "B", "content-type", "Content-Type"])
PAIRS = st.lists(st.tuples(KEYS, st.integers(0, 3)), max_size=6)
OPS = st.lists(
    st.one_of(
        st.tuples(st.sampled_from(["add", "setitem", "setdefault"]), KEYS, st.integers(0, 3)),
        st.tuples(st.sampled_from(["delitem", "popone", "popall", "getone"]), KEYS),
        st.tuples(st.sampled_from(["extend", "merge", "update"]), PAIRS),
        st.tuples(st.sampled_from(["popitem", "clear"])),
    ),
    max_size=12,
)


def _apply(md: Any, op: tuple[Any, ...]) -> Any:
    name, *args = op
    try:
        if name == "setitem":
            md[args[0]] = args[1]
            return None
        if name == "delitem":
            del md[args[0]]
            return None
        return getattr(md, name)(*args)
    except KeyError:
        return KeyError


def _run(ours: Any, theirs: Any, initial: list[tuple[str, int]], ops: list[Any]) -> None:
    mine, other = ours(initial), theirs(initial)
    for op in ops:
        assert _apply(mine, op) == _apply(other, op), op
        assert list(mine.allitems()) == list(other.items()), op
        assert list(mine) == list(other.keys()), op
        for key in ("a", "B", "content-type"):
            assert mine.getall(key) == other.getall(key, []), (op, key)
            assert (key in mine) == (key in other), (op, key)


@settings(max_examples=300, deadline=None)
@given(initial=PAIRS, ops=OPS)
def test_matches_multidict(initial: list[tuple[str, int]], ops: list[Any]) -> None:
    multidict = pytest.importorskip("multidict")
    _run(MultiDict, multidict.MultiDict, initial, ops)


@settings(max_examples=300, deadline=None)
@given(initial=PAIRS, ops=OPS)
def test_case_insensitive_matches_multidict(initial: list[tuple[str, int]], ops: list[Any]) -> None:
    multidict = pytest.importorskip("multidict")
    _run(CIMultiDict, multidict.CIMultiDict, initial, ops)


@settings(max_examples=200, deadline=None)
@given(initial=PAIRS, extra=PAIRS)
def test_mapping_view_matches_werkzeug(
    initial: list[tuple[str, int]], extra: list[tuple[str, int]]
) -> None:
    datastructures = pytest.importorskip("werkzeug.datastructures")
    mine: MultiDict[str, int] = MultiDict(initial)
    theirs = datastructures.MultiDict(initial)
    for key, value in extra:
        mine.add(key, value)
        theirs.add(key, value)
    assert len(mine) == len(theirs)
    assert dict(mine.items()) == theirs.to_dict()
    assert mine.to_dict() == theirs.to_dict(flat=False)
    for key in ("a", "A", "b", "missing"):
        assert mine.getall(key) == theirs.getlist(key)
        assert mine.get(key) == theirs.get(key)


def test_equality_with_plain_dicts_matches_multidict() -> None:
    multidict = pytest.importorskip("multidict")
    cases = [[("a", 1)], [("a", 1), ("a", 2)], [("a", 1), ("b", 2)], []]
    for pairs in cases:
        for other in ({"a": 1}, {"b": 2, "a": 1}, {}):
            assert (MultiDict(pairs) == other) == (multidict.MultiDict(pairs) == other)
