"""The constructor, extend and merge take keyword pairs and a positional-only source."""

from __future__ import annotations

from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict


@pytest.mark.parametrize("cls", [MultiDict, CIMultiDict])
def test_the_constructor_takes_keyword_pairs_after_the_source(cls: Any) -> None:
    assert list(cls(a=1).allitems()) == [("a", 1)]
    assert list(cls([("a", 1)], b=2, a=3).allitems()) == [("a", 1), ("b", 2), ("a", 3)]
    assert list(cls(None, b=2).allitems()) == [("b", 2)]
    assert list(cls({"x": 0}, y=1).allitems()) == [("x", 0), ("y", 1)]


def test_initial_is_positional_only_like_the_dict_argument() -> None:
    # As with dict(initial=...) and multidict, the name becomes a key.
    md = MultiDict(initial=[("a", 1)])
    assert list(md.allitems()) == [("initial", [("a", 1)])]


def test_case_insensitive_keyword_pairs_fold() -> None:
    headers = CIMultiDict([("Accept", "a")], ACCEPT="b")
    assert headers.getall("accept") == ["a", "b"] and len(headers) == 1


def test_extend_takes_keyword_pairs_and_an_optional_source() -> None:
    md = MultiDict([("a", 1)])
    md.extend()
    assert list(md.allitems()) == [("a", 1)]
    md.extend([("a", 2)], b=3, a=4)
    md.extend(c=5)
    assert list(md.allitems()) == [("a", 1), ("a", 2), ("b", 3), ("a", 4), ("c", 5)]


def test_merge_takes_keyword_pairs_and_skips_keys_already_present() -> None:
    md = MultiDict([("a", 1)])
    md.merge()
    md.merge(a=9, b=2)
    md.merge([("c", 3)], c=4, b=8)
    assert list(md.allitems()) == [("a", 1), ("b", 2), ("c", 3), ("c", 4)]


def test_keyword_pairs_are_checked_with_the_source_before_anything_changes() -> None:
    headers = CIMultiDict([("a", 1)])
    for call in (headers.extend, headers.merge):
        with pytest.raises(ValueError, match="element #1"):
            call([("b", 2), ("c",)], d=4)  # type: ignore[list-item]
    assert list(headers.allitems()) == [("a", 1)]


def test_the_source_of_extend_and_merge_cannot_be_named() -> None:
    md: MultiDict[str, Any] = MultiDict()
    md.extend(other=1)
    md.merge(other=2)
    assert list(md.allitems()) == [("other", 1)]
    with pytest.raises(TypeError):
        md.extend([("a", 1)], [("b", 2)])  # type: ignore[call-overload]


def test_a_subclass_constructor_hook_sees_the_keyword_pairs() -> None:
    seen: list[Any] = []

    class Hooked(MultiDict[str, int]):
        def extend(self, other: Any = (), /, **kwargs: Any) -> None:
            seen.append((other, kwargs))
            super().extend(other, **kwargs)

    md = Hooked(a=1)
    assert seen == [((), {"a": 1})] and md["a"] == 1


@pytest.mark.parametrize("cls", [MultiDict, CIMultiDict])
def test_a_keyword_pair_may_be_named_self(cls: Any) -> None:
    assert list(cls(self=1).allitems()) == [("self", 1)]
    for name in ("extend", "merge", "update"):
        md = cls()
        getattr(md, name)(self=1)
        assert list(md.allitems()) == [("self", 1)], name


def test_a_keyword_pair_repeating_a_positional_pair_is_kept() -> None:
    assert list(MultiDict([("a", 1)], a=1).allitems()) == [("a", 1), ("a", 1)]
    md = MultiDict([("a", 0)])
    md.extend([("a", 1)], a=1)
    assert list(md.allitems()) == [("a", 0), ("a", 1), ("a", 1)]
    md = MultiDict()
    md.merge([("a", 1)], a=1)
    assert list(md.allitems()) == [("a", 1), ("a", 1)]
    md = MultiDict([("a", 0)])
    md.update([("a", 1)], a=1)
    assert list(md.allitems()) == [("a", 1), ("a", 1)]
