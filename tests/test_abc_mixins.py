"""The documented mapping methods behave like the collections.abc mixins they replace.

``get``, ``pop``, ``setdefault``, ``keys``, ``items``, ``values`` and ``clear`` are
written out on the class (to document them), so each is checked against the standard
library's own mixin, run on an identical copy, over random operations.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from typedmultidict import CIMultiDict, MultiDict

KEYS = st.sampled_from(["a", "A", "b", "B", "c"])
PAIRS = st.lists(st.tuples(KEYS, st.integers(0, 3)), max_size=8)
CALLS = st.lists(
    st.one_of(
        st.tuples(st.just("get"), KEYS),
        st.tuples(st.just("get"), KEYS, st.integers(5, 6)),
        st.tuples(st.just("pop"), KEYS, st.integers(5, 6)),
        st.tuples(st.just("pop"), KEYS),
        st.tuples(st.just("setdefault"), KEYS),
        st.tuples(st.just("setdefault"), KEYS, st.integers(5, 6)),
        st.tuples(st.sampled_from(["keys", "items", "values", "clear"])),
    ),
    max_size=10,
)
MIXINS: dict[str, Any] = {
    "get": Mapping.get,
    "pop": MutableMapping.pop,
    "setdefault": MutableMapping.setdefault,
    "keys": lambda md: list(Mapping.keys(md)),
    "items": lambda md: list(Mapping.items(md)),
    "values": lambda md: list(Mapping.values(md)),
    "clear": MutableMapping.clear,
}


def _call(fn: Any, md: Any, args: tuple[Any, ...]) -> Any:
    try:
        result = fn(md, *args)
    except KeyError:
        return KeyError
    return list(result) if not isinstance(result, (int, type(None))) else result


@settings(max_examples=300, deadline=None)
@given(cls=st.sampled_from([MultiDict, CIMultiDict]), initial=PAIRS, calls=CALLS)
def test_overrides_match_the_mixins(cls: Any, initial: Any, calls: Any) -> None:
    ours, theirs = cls(initial), cls(initial)
    for name, *args in calls:
        mine = _call(getattr(type(ours), name), ours, tuple(args))
        assert mine == _call(MIXINS[name], theirs, tuple(args)), (name, args)
        assert list(ours.allitems()) == list(theirs.allitems())


def test_the_classes_are_registered_mutable_mappings() -> None:
    assert isinstance(MultiDict(), MutableMapping)
    assert isinstance(CIMultiDict(), MutableMapping)
