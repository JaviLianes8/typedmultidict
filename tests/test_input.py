"""Bulk input is read in full and validated before the mapping changes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict


class _KeysAndGetItem:
    # Not a Mapping subclass: only keys() and __getitem__, the shape dict.update accepts.
    def keys(self) -> list[str]:
        return ["x", "y"]

    def __getitem__(self, key: str) -> int:
        return ord(key)


def _pairs_then_failure() -> Iterator[Any]:
    yield ("a", 1)
    yield ("b", 2, 3)


def test_extend_with_itself_doubles_the_pairs() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1), ("b", 2)])
    md.extend(md)
    assert list(md.allitems()) == [("a", 1), ("b", 2), ("a", 1), ("b", 2)]


def test_update_and_merge_with_itself_change_nothing() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1), ("a", 2)])
    md.update(md)
    md.merge(md)
    assert list(md.allitems()) == [("a", 1), ("a", 2)]


def test_a_wrong_length_element_is_reported_with_its_position() -> None:
    md: MultiDict[str, int] = MultiDict([("z", 0)])
    with pytest.raises(ValueError, match=r"element #1 has length 3; 2 is required"):
        md.extend(_pairs_then_failure())
    assert list(md.allitems()) == [("z", 0)]


@pytest.mark.parametrize("method", ["extend", "merge", "update"])
def test_a_non_pair_element_raises_type_error_and_changes_nothing(method: str) -> None:
    md: MultiDict[str, int] = MultiDict([("z", 0)])
    with pytest.raises(TypeError, match=r"element #1 is not a \(key, value\) pair: int"):
        getattr(md, method)([("a", 1), 5])
    assert list(md.allitems()) == [("z", 0)]


def test_any_two_item_iterable_is_a_pair() -> None:
    loose: Any = ["ab", ["c", "d"]]
    md: MultiDict[str, str] = MultiDict(loose)
    assert list(md.allitems()) == [("a", "b"), ("c", "d")]


def test_objects_with_keys_are_read_as_mappings() -> None:
    md: MultiDict[str, int] = MultiDict(_KeysAndGetItem())
    assert list(md.allitems()) == [("x", 120), ("y", 121)]


def test_a_multidict_source_gives_every_pair() -> None:
    source: MultiDict[str, int] = MultiDict([("a", 1), ("a", 2)])
    assert list(MultiDict(source).allitems()) == [("a", 1), ("a", 2)]


def test_unhashable_keys_are_refused_without_changes() -> None:
    md: MultiDict[Any, int] = MultiDict()
    with pytest.raises(TypeError):
        md.extend([("a", 1), ([], 2)])
    assert len(md) == 0
    with pytest.raises(TypeError):
        md.add([], 1)
    with pytest.raises(TypeError):
        _ = [] in md


def test_case_insensitive_bulk_input_refuses_non_strings_atomically() -> None:
    headers: CIMultiDict[int] = CIMultiDict([("A", 0)])
    with pytest.raises(TypeError, match="CIMultiDict keys must be str, not int"):
        headers.extend([("b", 1), (2, 2)])  # type: ignore[list-item]
    assert list(headers.allitems()) == [("A", 0)]


def test_none_and_empty_inputs_build_an_empty_mapping() -> None:
    assert len(MultiDict()) == 0
    assert len(MultiDict(None)) == 0
    assert len(MultiDict({})) == 0
    assert len(MultiDict(initial=[("a", 1)])) == 1
