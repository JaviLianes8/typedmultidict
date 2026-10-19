"""How the references read bulk input, run live: the guide's rows on items() and keys().

Third-party references skip when they are not installed.
"""

from __future__ import annotations

import http.client
import io
from collections.abc import Iterator
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict

RAW = b"Set-Cookie: a=1\r\nX-Id: 7\r\nset-cookie: b=2\r\n\r\n"
FIELDS = [("Set-Cookie", "a=1"), ("X-Id", "7"), ("set-cookie", "b=2")]


class _KeysAndPairs:
    # keys() with [] say ("a", 1); iterating says ("z", 9).
    def keys(self) -> list[str]:
        return ["a"]

    def __getitem__(self, key: str) -> int:
        return 1

    def __iter__(self) -> Iterator[tuple[str, int]]:
        return iter([("z", 9)])


def _c_multidict() -> Any:
    multidict = pytest.importorskip("multidict")
    pure = pytest.importorskip("multidict._multidict_py")
    if multidict.CIMultiDict is pure.CIMultiDict:
        pytest.skip("the multidict C extension is not in use here")
    return multidict


def test_multidict_c_reads_a_header_object_through_items_as_we_do() -> None:
    multidict = _c_multidict()
    message = http.client.parse_headers(io.BytesIO(RAW))
    assert list(multidict.CIMultiDict(message).items()) == FIELDS
    assert list(CIMultiDict(message).allitems()) == FIELDS


def test_multidict_c_never_reads_keys_where_we_read_them_like_dict_update() -> None:
    multidict = _c_multidict()
    source: Any = _KeysAndPairs()
    assert list(multidict.MultiDict(source).items()) == [("z", 9)]
    assert list(MultiDict(source).allitems()) == [("a", 1)] == list(dict(source).items())


def test_pure_multidict_repeats_the_first_value_where_we_keep_every_field() -> None:
    pure = pytest.importorskip("multidict._multidict_py")
    message = http.client.parse_headers(io.BytesIO(RAW))
    theirs = list(pure.CIMultiDict(message).items())
    assert theirs == [("Set-Cookie", "a=1"), ("X-Id", "7"), ("set-cookie", "a=1")]
    assert list(CIMultiDict(message).allitems()) == FIELDS


def test_werkzeug_headers_give_every_field_through_items() -> None:
    datastructures = pytest.importorskip("werkzeug.datastructures")
    headers = datastructures.Headers(FIELDS)
    assert list(CIMultiDict(headers).allitems()) == FIELDS == list(headers.items())


def test_werkzeug_multidict_items_hold_first_values_unless_asked_for_all() -> None:
    datastructures = pytest.importorskip("werkzeug.datastructures")
    source = datastructures.MultiDict([("a", 1), ("a", 2), ("b", 3)])
    assert list(MultiDict(source).allitems()) == [("a", 1), ("b", 3)]
    every = MultiDict(source.items(multi=True))
    assert list(every.allitems()) == [("a", 1), ("a", 2), ("b", 3)]
