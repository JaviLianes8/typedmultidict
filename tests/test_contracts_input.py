"""Bulk input: the dict.update rule for mappings, foreign errors kept, spellings kept on copy."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest

from typedmultidict import CIMultiDict, MultiDict


class _KeysAndPairs:
    # keys() and __getitem__ win over __iter__, exactly as in dict.update.
    def keys(self) -> list[str]:
        return ["a"]

    def __getitem__(self, key: str) -> int:
        return 1

    def __iter__(self) -> Iterator[tuple[str, int]]:
        return iter([("z", 9)])


class _KeysWithoutGetItem:
    def keys(self) -> list[str]:
        return ["a"]

    def __iter__(self) -> Iterator[tuple[str, int]]:
        return iter([("a", 1)])


def test_an_object_with_keys_is_read_as_a_mapping_like_dict_update() -> None:
    source: Any = _KeysAndPairs()
    assert list(MultiDict(source).allitems()) == [("a", 1)] == list(dict(source).items())


def test_keys_without_getitem_fail_as_in_dict_update_and_change_nothing() -> None:
    source: Any = _KeysWithoutGetItem()
    with pytest.raises(TypeError):
        dict(source)
    md = MultiDict([("b", 2)])
    for write in (md.extend, md.merge, md.update):
        with pytest.raises(TypeError):
            write(source)
    assert list(md.allitems()) == [("b", 2)]


class _Broken(Exception):
    pass


class _ExplodingElement:
    def __iter__(self) -> Iterator[object]:
        raise _Broken("element could not be read")


class _ExplodingAfterOne:
    def __iter__(self) -> Iterator[object]:
        yield "k"
        raise _Broken("second item could not be read")


@pytest.mark.parametrize("element", [_ExplodingElement(), _ExplodingAfterOne()])
def test_an_element_whose_reading_fails_keeps_its_own_error(element: object) -> None:
    md = MultiDict([("a", 1)])
    with pytest.raises(_Broken):
        md.extend(cast(Any, [("b", 2), element]))
    assert list(md.allitems()) == [("a", 1)]


def test_a_case_insensitive_source_gives_each_pair_in_its_own_spelling() -> None:
    source = CIMultiDict([("Set-Cookie", "a"), ("set-cookie", "b"), ("X-Id", "c")])
    pairs = [("Set-Cookie", "a"), ("set-cookie", "b"), ("X-Id", "c")]
    assert list(MultiDict(source).allitems()) == pairs
    assert list(CIMultiDict(source).allitems()) == pairs
    target: MultiDict[str, str] = MultiDict()
    target.extend(source)
    assert list(target.allitems()) == pairs
    merged: MultiDict[str, str] = MultiDict([("Other", "o")])
    merged.merge(source)
    assert list(merged.allitems()) == [("Other", "o"), *pairs]
    updated = CIMultiDict([("SET-COOKIE", "old")])
    updated.update(source)
    assert list(updated.allitems()) == pairs
