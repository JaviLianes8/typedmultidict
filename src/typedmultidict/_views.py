"""Live views over every stored pair or value, not just the first of each key."""

from __future__ import annotations

import reprlib
from collections.abc import Collection, Hashable, Iterator
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from ._storage import _Storage

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class AllItemsView(Collection[tuple[K, V]], Generic[K, V]):
    """A live view of every ``(key, value)`` pair in insertion order; ``len()`` counts pairs.

    Returned by ``allitems()``; it follows later changes to its multi-dict, and changing
    the multi-dict while iterating over the view raises ``RuntimeError``.

    >>> from typedmultidict import CIMultiDict
    >>> headers = CIMultiDict([("Accept", "a"), ("accept", "b")])
    >>> pairs = headers.allitems()
    >>> len(pairs), ("ACCEPT", "b") in pairs, list(pairs)
    (2, True, [('Accept', 'a'), ('accept', 'b')])
    """

    __slots__ = ("_mapping",)

    def __init__(self, mapping: _Storage[K, V]) -> None:
        self._mapping = mapping

    def __len__(self) -> int:
        return self._mapping._count()

    def __iter__(self) -> Iterator[tuple[K, V]]:
        mapping = self._mapping
        return ((entry.key, entry.value) for entry in mapping._iterate(mapping._version))

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        key, value = item
        entries = self._mapping._index.get(self._mapping._probe(key), ())
        return any(entry.value is value or entry.value == value for entry in entries)

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self)!r})"


class AllValuesView(Collection[V], Generic[V]):
    """A live view of every value in insertion order; ``len()`` counts pairs.

    Returned by ``allvalues()``; it follows later changes to its multi-dict, and changing
    the multi-dict while iterating over the view raises ``RuntimeError``.

    >>> from typedmultidict import MultiDict
    >>> md = MultiDict([("a", 1), ("b", 2), ("a", 1)])
    >>> values = md.allvalues()
    >>> len(values), 2 in values, list(values)
    (3, True, [1, 2, 1])
    """

    __slots__ = ("_mapping",)

    def __init__(self, mapping: _Storage[Any, V]) -> None:
        self._mapping = mapping

    def __len__(self) -> int:
        return self._mapping._count()

    def __iter__(self) -> Iterator[V]:
        mapping = self._mapping
        return (entry.value for entry in mapping._iterate(mapping._version))

    def __contains__(self, value: object) -> bool:
        return any(entry.value is value or entry.value == value for entry in self._mapping._live())

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self)!r})"
