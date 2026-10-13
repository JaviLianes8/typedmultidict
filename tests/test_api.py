"""The multi-value methods: defaults, partial removal, merging and updating in place."""

from __future__ import annotations

import pytest

from typedmultidict import MultiDict


def _abc() -> MultiDict[str, int]:
    return MultiDict([("a", 1), ("b", 2), ("a", 3)])


def test_getone_returns_the_default_when_absent() -> None:
    md = _abc()
    assert md.getone("a", 0) == 1
    assert md.getone("missing", None) is None
    with pytest.raises(KeyError):
        md.getone("missing")


def test_getall_returns_a_new_list_each_time() -> None:
    md = _abc()
    values = md.getall("a")
    values.append(99)
    assert md.getall("a") == [1, 3]


def test_popone_removes_only_the_first_value() -> None:
    md = _abc()
    assert md.popone("a") == 1
    assert list(md.allitems()) == [("b", 2), ("a", 3)]
    assert list(md) == ["b", "a"]


def test_popone_default_and_missing_key() -> None:
    md = _abc()
    assert md.popone("missing", "x") == "x"
    with pytest.raises(KeyError):
        md.popone("missing")
    assert len(md.allitems()) == 3


def test_popall_default_may_be_any_type() -> None:
    md = _abc()
    assert md.popall("missing", None) is None
    assert md.popall("a") == [1, 3]
    assert "a" not in md


def test_pop_follows_the_mapping_contract() -> None:
    md = _abc()
    assert md.pop("a") == 1
    assert "a" not in md
    assert md.pop("a", 7) == 7
    with pytest.raises(KeyError):
        md.pop("a")


def test_popitem_removes_the_last_pair_only() -> None:
    md = _abc()
    assert md.popitem() == ("a", 3)
    assert md.getall("a") == [1]
    assert md.popitem() == ("b", 2)
    assert md.popitem() == ("a", 1)
    with pytest.raises(KeyError):
        md.popitem()


def test_merge_skips_keys_that_were_present() -> None:
    md = _abc()
    md.merge([("a", 9), ("c", 5), ("c", 6)])
    assert list(md.allitems()) == [("a", 1), ("b", 2), ("a", 3), ("c", 5), ("c", 6)]


def test_update_reuses_positions_and_appends_extras() -> None:
    md = _abc()
    md.update([("a", 7), ("c", 5), ("a", 8), ("a", 9)])
    assert list(md.allitems()) == [("a", 7), ("b", 2), ("a", 8), ("c", 5), ("a", 9)]


def test_update_drops_old_values_beyond_the_new_ones() -> None:
    md = _abc()
    md.update({"a": 7})
    assert list(md.allitems()) == [("a", 7), ("b", 2)]


def test_update_accepts_keyword_arguments() -> None:
    md = _abc()
    md.update(b=4, z=0)
    md.update([("a", 5)], c=6)
    assert list(md.allitems()) == [("a", 5), ("b", 4), ("z", 0), ("c", 6)]


def test_setitem_on_a_key_keeps_its_first_position() -> None:
    md: MultiDict[str, int] = MultiDict([("b", 0), ("a", 1), ("b", 2)])
    md["b"] = 9
    assert list(md.allitems()) == [("b", 9), ("a", 1)]


def test_setdefault_returns_the_first_value_or_adds() -> None:
    md = _abc()
    assert md.setdefault("a", 0) == 1
    assert md.setdefault("z", 0) == 0
    assert md.getall("z") == [0]


def test_clear_empties_everything() -> None:
    md = _abc()
    md.clear()
    assert len(md) == 0
    assert list(md.allitems()) == []
    md.add("a", 1)
    assert md.getall("a") == [1]


def test_to_dict_groups_values_under_the_key_order() -> None:
    md = _abc()
    md.popone("a")
    result = md.to_dict()
    assert result == {"b": [2], "a": [3]}
    assert list(result) == ["b", "a"]
    result["a"].append(0)
    assert md.getall("a") == [3]


def test_copy_is_shallow_and_independent() -> None:
    value = [1]
    md: MultiDict[str, list[int]] = MultiDict([("a", value)])
    twin = md.copy()
    twin.add("a", [2])
    assert md.getall("a") == [[1]]
    assert twin["a"] is value


def test_views_are_live_and_sized() -> None:
    md = _abc()
    items, values = md.allitems(), md.allvalues()
    md.add("c", 4)
    assert len(items) == len(values) == 4
    assert ("a", 3) in items
    assert ("a", 2) not in items
    short: object = ("c",)
    bare: object = "a"
    assert short not in items
    assert bare not in items
    assert 4 in values
    assert 5 not in values
    assert repr(items) == "AllItemsView([('a', 1), ('b', 2), ('a', 3), ('c', 4)])"
    assert repr(values) == "AllValuesView([1, 2, 3, 4])"


def test_mapping_views_see_first_values() -> None:
    md = _abc()
    assert list(md.keys()) == ["a", "b"]
    assert list(md.values()) == [1, 2]
    assert ("a", 3) not in md.items()
    assert ("a", 1) in md.items()


def test_repr_round_trips() -> None:
    md = _abc()
    assert repr(md) == "MultiDict([('a', 1), ('b', 2), ('a', 3)])"
    assert eval(repr(md), {"MultiDict": MultiDict}) == md
