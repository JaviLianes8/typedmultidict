"""The standard mapping views, made to notice a change made before their first item."""

from __future__ import annotations

import collections.abc as abc
from collections.abc import Hashable, Iterator, Mapping
from typing import Any, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

# The collections.abc views iterate with generators, which only start (and only look at the
# multi-dict) on the first next(). These take the multi-dict's iterator at iter() time, so a
# write between iter() and next() raises RuntimeError, as it does for dict views. They keep
# the standard names, so repr() reads the same, and pickle at every protocol.


class KeysView(abc.KeysView[K]):
    _mapping: Mapping[K, object]

    def __iter__(self) -> Iterator[K]:
        return iter(self._mapping)

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self), (self._mapping,))


class ItemsView(abc.ItemsView[K, V]):
    _mapping: Mapping[K, V]

    def __iter__(self) -> Iterator[tuple[K, V]]:
        mapping = self._mapping
        return ((key, mapping[key]) for key in iter(mapping))

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self), (self._mapping,))


class ValuesView(abc.ValuesView[V]):
    _mapping: Mapping[object, V]

    def __iter__(self) -> Iterator[V]:
        mapping = self._mapping
        return (mapping[key] for key in iter(mapping))

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self), (self._mapping,))
