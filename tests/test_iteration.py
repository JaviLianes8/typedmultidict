"""Changing the mapping while iterating it fails loudly instead of skipping entries."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict

Mutation = Callable[[MultiDict[str, int]], Any]

MUTATIONS: list[Mutation] = [
    lambda md: md.add("z", 0),
    lambda md: md.__setitem__("a", 9),
    lambda md: md.__setitem__("new", 9),
    lambda md: md.__delitem__("b"),
    lambda md: md.popone("a"),
    lambda md: md.popall("a"),
    lambda md: md.popitem(),
    lambda md: md.extend([("a", 0)]),
    lambda md: md.merge([("q", 0)]),
    lambda md: md.update([("a", 0)]),
    lambda md: md.clear(),
]

VIEWS: list[Callable[[MultiDict[str, int]], Iterable[Any]]] = [
    lambda md: md,
    lambda md: md.keys(),
    lambda md: md.items(),
    lambda md: md.values(),
    lambda md: md.allitems(),
    lambda md: md.allvalues(),
]


@pytest.mark.parametrize("mutate", MUTATIONS)
@pytest.mark.parametrize("view", VIEWS)
def test_mutation_during_iteration_raises(
    view: Callable[[MultiDict[str, int]], Iterable[Any]], mutate: Mutation
) -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1), ("b", 2), ("a", 3)])
    with pytest.raises(RuntimeError, match="changed during iteration"):
        for _ in view(md):
            mutate(md)


def test_mutation_after_the_last_item_still_raises() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    with pytest.raises(RuntimeError):
        for _ in md.allitems():
            md.add("b", 2)


def test_reads_during_iteration_are_fine() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1), ("b", 2)])
    seen = [(key, md.getall(key), key in md, md.get(key)) for key in md]
    assert seen == [("a", [1], True, 1), ("b", [2], True, 2)]


def test_a_fresh_iterator_after_a_change_works() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    items = md.allitems()
    md.add("b", 2)
    assert list(items) == [("a", 1), ("b", 2)]


def test_keys_are_listed_once_in_their_first_spelling() -> None:
    headers: CIMultiDict[str] = CIMultiDict([("X-Foo", "1"), ("b", "2"), ("x-foo", "3")])
    assert list(headers) == ["X-Foo", "b"]
    assert list(headers.keys()) == ["X-Foo", "b"]
    assert list(headers.items()) == [("X-Foo", "1"), ("b", "2")]
