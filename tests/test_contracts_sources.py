"""Bulk input with items(): header objects keep every field; keys() alone is read like a dict."""

from __future__ import annotations

import email.message
import http.client
import io
import types
import wsgiref.headers
from collections.abc import Callable, Iterator
from typing import Any, ClassVar, cast

import pytest

from typedmultidict import CIMultiDict, MultiDict

PAIRS = [("Set-Cookie", "a=1"), ("X-Id", "7"), ("set-cookie", "b=2"), ("SET-COOKIE", "c=3")]
RAW = b"".join(f"{name}: {value}\r\n".encode("ascii") for name, value in PAIRS) + b"\r\n"


def _http() -> Any:
    return http.client.parse_headers(io.BytesIO(RAW))


def _email() -> Any:
    message = email.message.Message()
    for name, value in PAIRS:
        message[name] = value
    return message


def _wsgiref() -> Any:
    return wsgiref.headers.Headers(list(PAIRS))


SOURCES: list[Callable[[], Any]] = [_http, _email, _wsgiref]


@pytest.mark.parametrize("make", SOURCES)
def test_a_header_object_gives_every_field_in_order(make: Callable[[], Any]) -> None:
    assert list(make().items()) == PAIRS  # the standard library's own answer
    headers = CIMultiDict(make())
    assert list(headers.allitems()) == PAIRS
    assert headers.getall("set-cookie") == ["a=1", "b=2", "c=3"] and headers["x-id"] == "7"
    assert list(MultiDict(make()).allitems()) == PAIRS


@pytest.mark.parametrize("make", SOURCES)
def test_every_bulk_write_reads_a_header_object_through_items(make: Callable[[], Any]) -> None:
    extended = CIMultiDict([("Other", "o")])
    extended.extend(make())
    assert list(extended.allitems()) == [("Other", "o"), *PAIRS]
    merged = CIMultiDict([("x-id", "kept")])
    merged.merge(make())
    assert list(merged.allitems()) == [("x-id", "kept"), PAIRS[0], PAIRS[2], PAIRS[3]]
    updated = CIMultiDict([("X-ID", "old"), ("Other", "o"), ("set-cookie", "old")])
    updated.update(make())
    assert list(updated.allitems()) == [PAIRS[1], ("Other", "o"), PAIRS[0], *PAIRS[2:]]


class _Disagreeing:
    # items() and keys() with [] describe different pairs: items() is the one read.
    def items(self) -> list[tuple[str, int]]:
        return [("a", 1), ("a", 2)]

    def keys(self) -> list[str]:
        return ["z"]

    def __getitem__(self, key: str) -> int:
        return 0


class _ItemsOnly:
    def items(self) -> Iterator[tuple[str, int]]:
        return iter([("a", 1), ("b", 2)])


class _ItemsAttribute:
    items: ClassVar[tuple[tuple[str, int], ...]] = (("q", 0),)  # not callable: keys() rule

    def keys(self) -> list[str]:
        return ["a"]

    def __getitem__(self, key: str) -> int:
        return 1


class _BadItems:
    def items(self) -> list[object]:
        return [("a", 1), ("b", 2, 3)]


def test_items_wins_over_keys_and_getitem() -> None:
    assert list(MultiDict(cast(Any, _Disagreeing())).allitems()) == [("a", 1), ("a", 2)]


def test_an_object_with_only_items_is_read_through_it() -> None:
    assert list(MultiDict(cast(Any, _ItemsOnly())).allitems()) == [("a", 1), ("b", 2)]


def test_a_non_callable_items_attribute_falls_back_to_keys() -> None:
    assert list(MultiDict(cast(Any, _ItemsAttribute())).allitems()) == [("a", 1)]


def test_what_items_gives_is_checked_like_any_bulk_input() -> None:
    md = MultiDict([("x", 0)])
    with pytest.raises(ValueError, match=r"^element #1 has length 3; 2 is required$"):
        md.extend(cast(Any, _BadItems()))
    assert list(md.allitems()) == [("x", 0)]


def test_a_dict_and_a_read_only_mapping_give_their_pairs_in_order() -> None:
    plain = {"b": 2, "a": 1}
    assert list(MultiDict(plain).allitems()) == [("b", 2), ("a", 1)]
    assert list(MultiDict(types.MappingProxyType(plain)).allitems()) == [("b", 2), ("a", 1)]
