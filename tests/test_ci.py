"""The case-insensitive variant: key folding, key type rules and lookup cost."""

from __future__ import annotations

from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict


class _Shouty(str):
    def lower(self) -> str:
        return "not-the-folded-key"


class _Key:
    # Counts equality checks so the tests can tell a hashed lookup from a scan.
    compared = 0

    def __init__(self, n: int) -> None:
        self.n = n

    def __hash__(self) -> int:
        return self.n

    def __eq__(self, other: object) -> bool:
        _Key.compared += 1
        return isinstance(other, _Key) and other.n == self.n


@pytest.mark.parametrize("key", [5, None, b"a", ("a",)])
def test_non_string_keys_are_refused_on_write(key: Any) -> None:
    headers: CIMultiDict[int] = CIMultiDict()
    for write in (headers.add, headers.__setitem__, headers.setdefault):
        with pytest.raises(TypeError, match="keys must be str"):
            write(key, 1)
    assert len(headers.allitems()) == 0


@pytest.mark.parametrize("key", [5, None, b"a", ("a",), []])
def test_non_string_keys_are_absent_on_read(key: Any) -> None:
    headers: CIMultiDict[int] = CIMultiDict([("a", 1)])
    assert key not in headers
    assert headers.get(key) is None
    assert headers.getall(key) == []
    assert headers.getone(key, 0) == 0
    assert headers.popall(key, None) is None
    with pytest.raises(KeyError):
        headers[key]
    with pytest.raises(KeyError):
        del headers[key]


def test_folding_uses_the_base_string_lower() -> None:
    headers: CIMultiDict[int] = CIMultiDict([(_Shouty("Key"), 1)])
    assert headers["KEY"] == 1
    assert type(next(iter(headers))) is _Shouty


def test_folding_is_lower_not_casefold() -> None:
    headers: CIMultiDict[int] = CIMultiDict([("Straße", 1), ("ÀB", 2)])
    assert "STRASSE" not in headers
    assert headers["àb"] == 2


def test_spelling_of_each_pair_is_kept_and_setitem_takes_the_new_one() -> None:
    headers: CIMultiDict[str] = CIMultiDict([("X-Foo", "1"), ("x-foo", "2")])
    assert list(headers.allitems()) == [("X-Foo", "1"), ("x-foo", "2")]
    headers["X-FOO"] = "3"
    assert list(headers.allitems()) == [("X-FOO", "3")]
    assert ("x-foo", "3") in headers.allitems()


def test_ci_views_and_to_dict_group_by_folded_key() -> None:
    headers: CIMultiDict[str] = CIMultiDict([("A", "1"), ("a", "2"), ("B", "3")])
    assert headers.to_dict() == {"A": ["1", "2"], "B": ["3"]}
    assert len(headers) == 2
    assert headers.popone("a") == "1"
    assert list(headers) == ["a", "B"]


@pytest.mark.parametrize("size", [10, 5000])
def test_lookups_do_not_scan_other_keys(size: int) -> None:
    md: MultiDict[_Key, int] = MultiDict((_Key(n), n) for n in range(size))
    probe = _Key(size // 2)
    _Key.compared = 0
    assert md[probe] == size // 2
    assert md.getall(probe) == [size // 2]
    assert md.getone(probe) == size // 2
    assert probe in md
    assert len(md) == size
    md.add(probe, -1)
    md[probe] = 0
    assert _Key.compared <= 8
