"""Equality, hashing, pickling and copying rules."""

from __future__ import annotations

import copy
import pickle
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict


class _Tagged(MultiDict[str, int]):
    __slots__ = ("label",)

    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label


class _WithDict(MultiDict[str, int]):
    pass


def _pickled(obj: Any) -> Any:
    return pickle.loads(pickle.dumps(obj))


def test_equality_is_order_sensitive_between_multidicts() -> None:
    assert MultiDict([("a", 1), ("b", 2)]) != MultiDict([("b", 2), ("a", 1)])
    assert MultiDict([("a", 1), ("a", 2)]) == MultiDict([("a", 1), ("a", 2)])


def test_case_insensitive_comparison_applies_if_either_side_folds() -> None:
    assert CIMultiDict([("A", 1)]) == MultiDict([("a", 1)])
    assert MultiDict([("A", 1)]) == CIMultiDict([("a", 1)])
    assert CIMultiDict([("A", 1)]) == CIMultiDict([("a", 1)])
    assert MultiDict([("A", 1)]) != MultiDict([("a", 1)])


def test_comparison_with_a_plain_mapping_needs_single_values() -> None:
    assert MultiDict([("a", 1), ("b", 2)]) == {"b": 2, "a": 1}
    assert MultiDict([("a", 1), ("a", 2)]) != {"a": 1}
    assert MultiDict([("a", 1)]) != {"a": 1, "b": 2}
    assert CIMultiDict([("A", 1), ("a", 1)]) != {"A": 1, "a": 1}
    assert CIMultiDict([("A", 1)]) != {"a": 1}


def test_comparison_with_other_types_is_not_equal() -> None:
    assert MultiDict([("a", 1)]) != [("a", 1)]
    assert MultiDict().__eq__(5) is NotImplemented


def test_multidicts_are_unhashable() -> None:
    with pytest.raises(TypeError):
        hash(MultiDict())


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_round_trips_at_every_protocol(protocol: int) -> None:
    for md in (MultiDict([("a", 1), ("b", 2), ("a", 3)]), CIMultiDict([("X", 1), ("x", 2)])):
        twin = pickle.loads(pickle.dumps(md, protocol))
        assert type(twin) is type(md)
        assert list(twin.allitems()) == list(md.allitems())
        key = next(iter(md))
        twin.add(key, 0)
        assert twin.getall(key)[-1] == 0
        assert md.getall(key)[-1] != 0


def test_pickles_store_plain_pairs() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1), ("a", 2)])
    rebuild, args, state = md.__reduce__()
    assert args == (MultiDict, [("a", 1), ("a", 2)])
    assert state is None
    assert rebuild(*args) == md


def test_subclass_state_survives_copy_and_pickle() -> None:
    tagged = _Tagged("t")
    tagged.add("a", 1)
    plain = _WithDict([("b", 2)])
    plain.note = "n"  # type: ignore[attr-defined]
    for clone in (copy.copy, copy.deepcopy, _pickled):
        twin: Any = clone(tagged)
        assert (type(twin), twin.label, list(twin.allitems())) == (_Tagged, "t", [("a", 1)])
        other: Any = clone(plain)
        assert (type(other), other.note, list(other.allitems())) == (_WithDict, "n", [("b", 2)])
    assert tagged.copy().label == "t"


def test_deepcopy_copies_values_and_copy_shares_them() -> None:
    md: MultiDict[str, list[int]] = MultiDict([("a", [1])])
    assert copy.copy(md)["a"] is md["a"]
    deep = copy.deepcopy(md)
    assert deep == md
    assert deep["a"] is not md["a"]


def test_a_copy_does_not_follow_the_original() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    for twin in (md.copy(), copy.copy(md), copy.deepcopy(md)):
        md.add("a", 2)
        assert twin.getall("a") == [1]
        md.popall("a")
        md.add("a", 1)
