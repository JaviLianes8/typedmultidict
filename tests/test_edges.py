"""Edge cases that a mutation run showed were not pinned by any other test."""

from __future__ import annotations

import copyreg
import pickle
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict


class _Sub(MultiDict[str, int]):
    pass


class _Boom:
    # Unequal to everything and raises when compared, so adding it fails mid-way.
    def __hash__(self) -> int:
        return hash("a")

    def __eq__(self, other: object) -> bool:
        raise ValueError("eq boom")


class _Legacy:
    def __init__(self, attrs: dict[str, Any]) -> None:
        self.attrs = attrs

    def __reduce__(self) -> tuple[Any, ...]:
        return (getattr(copyreg, "_reconstructor"), (MultiDict, object, None), self.attrs)  # noqa: B009


def test_shrinking_after_the_last_item_still_raises() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    with pytest.raises(RuntimeError, match="changed during iteration"):
        for _ in md:
            md.popitem()


def test_replacing_a_single_value_during_iteration_raises() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1), ("b", 2)])
    with pytest.raises(RuntimeError, match="changed during iteration"):
        for key in md:
            md[key] = 0


def test_a_plain_subclass_folds_case_against_a_case_insensitive_one() -> None:
    assert _Sub([("A", 1)]) == CIMultiDict([("a", 1)])
    assert CIMultiDict([("a", 1)]) == _Sub([("A", 1)])


def test_a_failed_update_keeps_the_values_it_would_have_dropped() -> None:
    md: MultiDict[Any, int] = MultiDict([("a", 1), ("a", 2)])
    with pytest.raises(ValueError, match="eq boom"):
        md.update([("a", 9), (_Boom(), 0)])
    assert list(md.allitems()) == [("a", 1), ("a", 2)]


def test_lookups_fold_the_probe_with_lower_too() -> None:
    headers: CIMultiDict[int] = CIMultiDict([("Straße", 1)])
    assert headers["STRAßE"] == 1


def test_a_one_item_element_is_reported_with_its_length() -> None:
    with pytest.raises(ValueError, match=r"element #0 has length 1; 2 is required"):
        loose: Any = ["a"]
        MultiDict(loose)


def test_a_legacy_pickle_does_not_keep_its_old_list() -> None:
    md: Any = pickle.loads(pickle.dumps(_Legacy({"_items": [("a", 1)]})))
    assert "_items" not in vars(md)
    assert list(md.allitems()) == [("a", 1)]
