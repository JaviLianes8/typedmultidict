from __future__ import annotations

import pytest

from typedmultidict import CIMultiDict, MultiDict


def test_add_keeps_multiple_values_for_one_key() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.add("a", 1)
    md.add("a", 2)
    assert md.getall("a") == [1, 2]


def test_getitem_returns_the_first_value() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.add("a", 1)
    md.add("a", 2)
    assert md["a"] == 1
    assert md.getone("a") == 1
    assert md.get("a") == 1


def test_getall_is_empty_for_a_missing_key() -> None:
    md: MultiDict[str, int] = MultiDict()
    assert md.getall("missing") == []


def test_getitem_raises_for_a_missing_key() -> None:
    md: MultiDict[str, int] = MultiDict()
    with pytest.raises(KeyError):
        md["missing"]


def test_insertion_order_is_preserved() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.add("b", 1)
    md.add("a", 2)
    md.add("b", 3)
    assert list(md.allitems()) == [("b", 1), ("a", 2), ("b", 3)]
    assert list(md) == ["b", "a"]


def test_delete_removes_every_value_for_the_key() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.add("a", 1)
    md.add("a", 2)
    md.add("b", 3)
    del md["a"]
    assert "a" not in md
    assert list(md.allitems()) == [("b", 3)]


def test_delete_raises_for_a_missing_key() -> None:
    md: MultiDict[str, int] = MultiDict()
    with pytest.raises(KeyError):
        del md["missing"]


def test_setitem_replaces_all_values_in_place() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.add("a", 1)
    md.add("b", 2)
    md.add("a", 3)
    md["a"] = 9
    assert md.getall("a") == [9]
    assert list(md.allitems()) == [("a", 9), ("b", 2)]


def test_len_counts_keys_while_allitems_counts_pairs() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.add("a", 1)
    md.add("a", 2)
    md.add("b", 3)
    assert len(md) == 2
    assert len(list(md.allitems())) == 3


def test_popall_removes_and_returns_every_value() -> None:
    md: MultiDict[str, int] = MultiDict()
    md.add("a", 1)
    md.add("a", 2)
    md.add("b", 3)
    assert md.popall("a") == [1, 2]
    assert list(md.allitems()) == [("b", 3)]


def test_popall_default_when_absent() -> None:
    md: MultiDict[str, int] = MultiDict()
    assert md.popall("missing", []) == []
    with pytest.raises(KeyError):
        md.popall("missing")


def test_extend_adds_pairs_from_various_sources() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    md.extend({"b": 2})
    other: MultiDict[str, int] = MultiDict()
    other.add("a", 3)
    md.extend(other)
    assert list(md.allitems()) == [("a", 1), ("b", 2), ("a", 3)]


def test_equality_is_order_sensitive_over_all_pairs() -> None:
    first: MultiDict[str, int] = MultiDict([("a", 1), ("a", 2)])
    second: MultiDict[str, int] = MultiDict([("a", 1), ("a", 2)])
    third: MultiDict[str, int] = MultiDict([("a", 2), ("a", 1)])
    assert first == second
    assert first != third


def test_ci_lookup_ignores_case() -> None:
    headers: CIMultiDict[str] = CIMultiDict()
    headers.add("Content-Type", "text/html")
    headers.add("CONTENT-TYPE", "text/plain")
    assert headers["content-type"] == "text/html"
    assert headers.getall("Content-Type") == ["text/html", "text/plain"]
    assert len(headers) == 1


def test_ci_preserves_original_key_casing() -> None:
    headers: CIMultiDict[str] = CIMultiDict()
    headers.add("X-Custom-Header", "value")
    assert list(headers) == ["X-Custom-Header"]
    assert list(headers.allitems()) == [("X-Custom-Header", "value")]


def test_ci_setitem_replaces_across_casings() -> None:
    headers: CIMultiDict[str] = CIMultiDict()
    headers.add("Accept", "text/html")
    headers.add("accept", "application/json")
    headers["ACCEPT"] = "text/plain"
    assert headers.getall("accept") == ["text/plain"]


def test_generic_typing_round_trips_values() -> None:
    md: MultiDict[int, list[str]] = MultiDict()
    md.add(1, ["x"])
    md.add(1, ["y", "z"])
    value: list[str] = md[1]
    assert value == ["x"]
    assert md.getall(1) == [["x"], ["y", "z"]]
