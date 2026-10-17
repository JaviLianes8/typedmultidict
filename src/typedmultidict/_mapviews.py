"""The standard mapping views, made to notice a change made before their first item."""

from __future__ import annotations

from collections.abc import Hashable, ItemsView, Iterator, KeysView, Mapping, ValuesView
from typing import TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

# The collections.abc views iterate with generators, which only start (and only look at the
# multi-dict) on the first next(). These take the multi-dict's iterator at iter() time, so a
# write between iter() and next() raises RuntimeError, as it does for dict views.


class _Keys(KeysView[K]):
    _mapping: Mapping[K, object]

    def __iter__(self) -> Iterator[K]:
        return iter(self._mapping)


class _Items(ItemsView[K, V]):
    _mapping: Mapping[K, V]

    def __iter__(self) -> Iterator[tuple[K, V]]:
        mapping = self._mapping
        return ((key, mapping[key]) for key in iter(mapping))


class _Values(ValuesView[V]):
    _mapping: Mapping[object, V]

    def __iter__(self) -> Iterator[V]:
        mapping = self._mapping
        return (mapping[key] for key in iter(mapping))


# Shown by repr() like the standard views they extend.
for _view in (_Keys, _Items, _Values):
    _view.__name__ = _view.__qualname__ = _view.__name__.lstrip("_") + "View"
del _view
