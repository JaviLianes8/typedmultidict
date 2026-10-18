"""Copies and pickles keep case folding, every shape of subclass slot and a portable view form."""

from __future__ import annotations

import copy
import copyreg
import pickle
from collections.abc import Callable
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict

Clone = Callable[[Any], Any]


def _pickler(protocol: int) -> Clone:
    return lambda obj: pickle.loads(pickle.dumps(obj, protocol))


CLONES: list[Clone] = [copy.copy, copy.deepcopy]
CLONES += [_pickler(protocol) for protocol in range(pickle.HIGHEST_PROTOCOL + 1)]


class _Legacy:
    # The stream 0.1.0 wrote: the class rebuilt without __init__, then its instance dictionary.
    def __init__(self, cls: type, attrs: dict[str, Any]) -> None:
        self.cls, self.attrs = cls, attrs

    def __reduce__(self) -> tuple[Any, ...]:
        return (getattr(copyreg, "_reconstructor"), (self.cls, object, None), self.attrs)  # noqa: B009


class _OneSlot(MultiDict[str, int]):
    __slots__ = "tag"  # a single string declares one slot, not one per character


class _Lazy(MultiDict[str, int]):
    __slots__ = ("cache", "label")


class _Guarded(MultiDict[str, int]):
    __slots__ = ("tag",)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "tag":
            raise AttributeError("tag is read-only")
        super().__setattr__(name, value)


class _Underscored(MultiDict[str, int]):
    __slots__ = ("_note",)  # one leading underscore: not name-mangled


class _Base(MultiDict[str, int]):
    __slots__ = ("label",)


class _Child(_Base):
    __slots__ = ("extra",)


@pytest.mark.parametrize("clone", CLONES)
def test_a_case_insensitive_copy_still_folds_case(clone: Clone) -> None:
    twin = clone(CIMultiDict([("X-Tag", 1), ("x-tag", 2), ("Other", 3)]))
    assert len(twin) == 2 and list(twin) == ["X-Tag", "Other"]
    assert twin.getall("X-TAG") == [1, 2] and twin["other"] == 3 and "OTHER" in twin
    twin.add("x-TAG", 4)
    assert twin.getall("x-tag") == [1, 2, 4]
    del twin["X-tag"]
    assert list(twin.allitems()) == [("Other", 3)]


def test_a_case_insensitive_pickle_from_version_0_1_0_folds_case() -> None:
    md = pickle.loads(pickle.dumps(_Legacy(CIMultiDict, {"_items": [("A", 1), ("a", 2)]})))
    assert len(md) == 1 and md.getall("a") == [1, 2] and list(md) == ["A"]


def test_a_pickle_from_version_0_1_0_without_pairs_loads_empty() -> None:
    # A 0.1.0 subclass that never ran MultiDict.__init__ pickled only its own attributes.
    md = pickle.loads(pickle.dumps(_Legacy(MultiDict, {"note": "n"})))
    assert type(md) is MultiDict and len(md) == 0 and list(md.allitems()) == []
    assert vars(md)["note"] == "n"
    md.add("a", 1)
    assert md.getall("a") == [1]


@pytest.mark.parametrize("clone", CLONES)
def test_a_slot_declared_by_a_single_string_survives(clone: Clone) -> None:
    md = _OneSlot([("a", 1)])
    md.tag = "t"  # type: ignore[attr-defined]
    twin = clone(md)
    assert twin.tag == "t" and list(twin.allitems()) == [("a", 1)]


@pytest.mark.parametrize("clone", CLONES)
def test_an_unset_slot_stays_unset(clone: Clone) -> None:
    md = _Lazy([("a", 1)])
    md.label = "l"  # type: ignore[attr-defined]
    twin = clone(md)
    assert twin.label == "l" and not hasattr(twin, "cache")
    assert list(twin.allitems()) == [("a", 1)]


@pytest.mark.parametrize("clone", CLONES)
def test_slots_come_back_without_the_subclass_setattr(clone: Clone) -> None:
    # Like the instance dictionary, slots are restored directly, never through a hook.
    md = _Guarded([("a", 1)])
    object.__setattr__(md, "tag", "t")
    twin = clone(md)
    assert twin.tag == "t" and list(twin.allitems()) == [("a", 1)]


@pytest.mark.parametrize("clone", CLONES)
def test_single_underscore_and_inherited_slots_survive(clone: Clone) -> None:
    md = _Underscored([("a", 1)])
    md._note = "n"  # type: ignore[attr-defined]
    assert clone(md)._note == "n"
    child = _Child([("a", 1)])
    child.label, child.extra = "l", "e"  # type: ignore[attr-defined]
    twin = clone(child)
    assert (twin.label, twin.extra, list(twin.allitems())) == ("l", "e", [("a", 1)])


@pytest.mark.parametrize("clone", CLONES)
def test_private_instance_attributes_survive(clone: Clone) -> None:
    md = MultiDict([("a", 1)])
    md._cache = {"k": 1}  # type: ignore[attr-defined]
    twin = clone(md)
    assert twin._cache == {"k": 1} and list(twin.allitems()) == [("a", 1)]


def test_a_pickle_from_version_0_1_0_keeps_private_attributes() -> None:
    md = pickle.loads(pickle.dumps(_Legacy(MultiDict, {"_items": [("a", 1)], "_cache": 5})))
    assert vars(md)["_cache"] == 5 and list(md.allitems()) == [("a", 1)]


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_every_view_pickles_as_its_class_called_with_its_multi_dict(protocol: int) -> None:
    # The same stream on every Python version, so a view pickled by one loads on another.
    md = MultiDict([("a", 1)])
    for view in (md.keys(), md.items(), md.values(), md.allitems(), md.allvalues()):
        reduced = view.__reduce_ex__(protocol)
        assert isinstance(reduced, tuple)
        rebuild, args = reduced[:2]
        assert rebuild is type(view) and len(args) == 1 and args[0] is md
