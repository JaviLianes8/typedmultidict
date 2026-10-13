"""Regression tests for defects found in review: atomicity, iteration, pickling edges."""

from __future__ import annotations

import copy
import copyreg
import pickle
import weakref
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict


class _Fragile:
    # Same hash for every instance, and comparing against a "boom" key raises.
    def __init__(self, n: int, boom: bool = False) -> None:
        self.n, self.boom = n, boom

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other: object) -> bool:
        if self.boom or getattr(other, "boom", False):
            raise ValueError("eq boom")
        return isinstance(other, _Fragile) and other.n == self.n


class _Private(MultiDict[str, int]):
    __slots__ = ("__secret",)

    def hide(self, value: int) -> None:
        self.__secret = value

    def reveal(self) -> int:
        return self.__secret


class _Legacy:
    # Pickles into the same stream 0.1.0 produced at protocols 0 and 1: the class rebuilt
    # without __init__, then its instance dictionary as state.
    def __init__(self, cls: type, attrs: dict[str, Any]) -> None:
        self.cls, self.attrs = cls, attrs

    def __reduce__(self) -> tuple[Any, ...]:
        return (getattr(copyreg, "_reconstructor"), (self.cls, object, None), self.attrs)  # noqa: B009


def _pickled(obj: Any) -> Any:
    return pickle.loads(pickle.dumps(obj))


def test_update_with_an_unhashable_key_changes_nothing() -> None:
    md: MultiDict[Any, int] = MultiDict([("a", 1), ("b", 2)])
    with pytest.raises(TypeError):
        md.update([("a", 9), ([], 1)])
    assert list(md.allitems()) == [("a", 1), ("b", 2)]


@pytest.mark.parametrize("method", ["extend", "update", "merge"])
def test_a_key_whose_eq_raises_rolls_the_whole_input_back(method: str) -> None:
    md: MultiDict[Any, int] = MultiDict([(_Fragile(0), 0)])
    with pytest.raises(ValueError, match="eq boom"):
        getattr(md, method)([("x", 1), (_Fragile(1, boom=True), 2)])
    assert len(md.allitems()) == len(md) == 1
    assert "x" not in md
    assert md.getall("x") == []
    md.add("y", 3)
    assert md.popitem() == ("y", 3)


def test_an_iterator_made_before_a_change_raises() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    for make in (iter, lambda m: iter(m.allitems()), lambda m: iter(m.allvalues())):
        it = make(md)
        md.add("b", 2)
        with pytest.raises(RuntimeError, match="changed during iteration"):
            next(it)


def test_instances_take_attributes_and_weak_references() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.note = "n"  # type: ignore[attr-defined]
    ref = weakref.ref(md)
    assert ref() is md
    assert copy.copy(md).note == "n"  # type: ignore[attr-defined]


def test_a_pickle_written_by_version_0_1_0_still_loads() -> None:
    for cls in (MultiDict, CIMultiDict):
        data = pickle.dumps(_Legacy(cls, {"_items": [("A", 1), ("a", 2)], "note": "n"}))
        md: Any = pickle.loads(data)
        assert type(md) is cls
        assert list(md.allitems()) == [("A", 1), ("a", 2)]
        assert vars(md)["note"] == "n"
        md.add("b", 3)
        assert md.getall("b") == [3]


def test_private_slots_of_subclasses_survive_copy_and_pickle() -> None:
    md = _Private([("a", 1)])
    md.hide(42)
    for clone in (copy.copy, copy.deepcopy, _pickled):
        twin = clone(md)
        assert twin.reveal() == 42
        assert list(twin.allitems()) == [("a", 1)]


def test_a_multidict_that_contains_itself() -> None:
    md: MultiDict[str, Any] = MultiDict([("a", 1)])
    md.add("self", md)
    assert repr(md) == "MultiDict([('a', 1), ('self', ...)])"
    for twin in (copy.deepcopy(md), pickle.loads(pickle.dumps(md))):
        assert twin["self"] is twin
        assert twin["a"] == 1


def test_pickles_name_only_the_public_module() -> None:
    for md in (MultiDict([("a", 1)]), CIMultiDict([("a", 1)])):
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            data = pickle.dumps(md, protocol)
            assert b"typedmultidict" in data
            assert b"typedmultidict." not in data
            assert b"_storage" not in data
            assert b"_multidict" not in data
