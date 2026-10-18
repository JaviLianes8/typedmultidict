"""Exact edges: key errors as given, the type-name cut, identity-first membership, folding."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import pytest

from typedmultidict import CIMultiDict, MultiDict

Call = Callable[[Any, object], object]

_MISSING_KEY_CALLS: list[Call] = [
    lambda md, key: md[key],
    lambda md, key: md.__delitem__(key),
    lambda md, key: md.pop(key),
    lambda md, key: md.getone(key),
    lambda md, key: md.popone(key),
    lambda md, key: md.popall(key),
]


@pytest.mark.parametrize("key", ["X-Missing", 7])
@pytest.mark.parametrize("call", _MISSING_KEY_CALLS)
def test_a_case_insensitive_key_error_carries_the_key_as_given(call: Call, key: object) -> None:
    md = CIMultiDict([("a", 1)])
    with pytest.raises(KeyError) as caught:
        call(md, key)
    assert caught.value.args == (key,)
    assert list(md.allitems()) == [("a", 1)]


def _not_a_pair_message(item: object) -> str:
    with pytest.raises(TypeError) as caught:
        MultiDict(cast(Any, [item]))
    return str(caught.value)


def test_a_type_name_of_forty_characters_is_shown_whole() -> None:
    name = "N" * 39 + "Z"
    message = _not_a_pair_message(type(name, (), {})())
    assert message == f"element #0 is not a (key, value) pair: {name}"


def test_a_longer_type_name_is_cut_to_forty_characters() -> None:
    message = _not_a_pair_message(type("N" * 37 + "ABCD", (), {})())
    assert message == "element #0 is not a (key, value) pair: " + "N" * 37 + "..."


def test_the_name_of_a_case_insensitive_subclass_is_cut_too() -> None:
    long_class: Any = type("C" * 45, (CIMultiDict,), {})
    with pytest.raises(TypeError) as caught:
        long_class().add(1, "v")
    assert str(caught.value) == "C" * 37 + "... keys must be str, not int"


class _LoudName(str):
    def __str__(self) -> str:
        raise RuntimeError("str() must not run on a type name")


def test_a_type_name_that_is_a_str_subclass_is_shown_as_plain_text() -> None:
    class Meta(type):
        @property
        def __name__(cls) -> Any:  # type: ignore[override]
            return _LoudName("Quiet")

    odd: Any = Meta("Odd", (), {})()
    assert _not_a_pair_message(odd) == "element #0 is not a (key, value) pair: Quiet"


class _NoLen(list[Any]):
    def __len__(self) -> int:
        raise RuntimeError("len() must not run on a list subclass")


def test_a_list_subclass_is_measured_by_reading_never_by_its_len() -> None:
    with pytest.raises(ValueError, match=r"^element #0 has length 3 or more; 2 is required$"):
        MultiDict(cast(Any, [_NoLen([1, 2, 3, 4])]))
    with pytest.raises(ValueError, match=r"^element #0 has length 1; 2 is required$"):
        MultiDict(cast(Any, [_NoLen(["a"])]))
    assert MultiDict(cast(Any, [_NoLen(["a", 1])])).getall("a") == [1]


def test_view_membership_checks_identity_before_equality_like_list() -> None:
    nan = float("nan")
    md = MultiDict([("a", nan), ("b", 2.0)])
    assert ("a", nan) in md.allitems() and nan in md.allvalues()
    assert ("a", nan) in md.items() and nan in md.values() and nan in [nan]
    assert ("a", float("nan")) not in md.allitems()
    assert float("nan") not in md.allvalues()


class _OwnLower(str):
    def lower(self) -> str:  # never consulted: folding is str.lower
        return "zzz"


def test_mixed_equality_folds_with_str_lower_whatever_a_key_subclass_says() -> None:
    plain = MultiDict([(_OwnLower("A"), 1)])
    assert plain == CIMultiDict([("a", 1)]) and CIMultiDict([("a", 1)]) == plain
    assert plain != CIMultiDict([("zzz", 1)])


def test_mixed_equality_with_keys_that_are_not_strings_is_false_without_error() -> None:
    plain: MultiDict[object, str] = MultiDict([(1, "x")])
    assert plain != CIMultiDict([("1", "x")]) and CIMultiDict([("1", "x")]) != plain
    assert (plain == CIMultiDict[str]()) is False
    assert MultiDict([(1, "x"), ("A", "y")]) != CIMultiDict([("a", "y")])
