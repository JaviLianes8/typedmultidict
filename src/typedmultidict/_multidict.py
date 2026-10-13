"""Ordered mapping where a single key can hold several values."""

from __future__ import annotations

import copy as _copy
from collections.abc import Hashable
from typing import TYPE_CHECKING, Any, TypeVar, overload

from ._pairs import MultiDictInput, read_pairs
from ._storage import _Storage
from ._views import AllItemsView, AllValuesView

if TYPE_CHECKING:
    from collections.abc import Iterable

    from _typeshed import SupportsKeysAndGetItem

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
T = TypeVar("T")
Self = TypeVar("Self", bound="MultiDict[Any, Any]")

_MISSING: Any = object()


class MultiDict(_Storage[K, V]):
    """A typed, insertion-ordered multi-value mapping.

    Mapping operations act on the first value of each key, so the type behaves like a
    normal mapping (``len()`` counts keys). The multi-value surface (``add``, ``getall``,
    ``allitems`` and friends) sees every stored pair in insertion order.
    """

    __slots__ = ()

    def __init__(self, initial: MultiDictInput[K, V] | None = None) -> None:
        self._setup()
        if initial is not None:
            self.extend(initial)

    def _collect(self, source: object, extra: dict[str, Any]) -> list[tuple[Hashable, K, V]]:
        pairs = read_pairs(source, _Storage)
        pairs.extend(extra.items())
        return [(self._token(key), key, value) for key, value in pairs]

    def add(self, key: K, value: V) -> None:
        """Append another value for ``key`` without replacing existing ones."""
        self._append([(self._token(key), key, value)])

    def extend(self, other: MultiDictInput[K, V]) -> None:
        """Append every pair of a mapping, multi-dict or iterable of pairs."""
        self._append(self._collect(other, {}))

    def merge(self, other: MultiDictInput[K, V]) -> None:
        """Append the pairs whose key is not present yet; keys already here are skipped."""
        present = set(self._index)
        self._append([item for item in self._collect(other, {}) if item[0] not in present])

    @overload
    def update(self, other: SupportsKeysAndGetItem[K, V], /) -> None: ...
    @overload
    def update(
        self: MultiDict[str, V], other: SupportsKeysAndGetItem[str, V], /, **kwargs: V
    ) -> None: ...
    @overload
    def update(self, other: Iterable[tuple[K, V]], /) -> None: ...
    @overload
    def update(self: MultiDict[str, V], other: Iterable[tuple[str, V]], /, **kwargs: V) -> None: ...
    @overload
    def update(self: MultiDict[str, V], /, **kwargs: V) -> None: ...

    def update(self, other: Any = (), /, **kwargs: Any) -> None:
        """Replace the values of every incoming key, reusing the old positions in order.

        Extra new values go to the end, extra old values are removed, and keys that do
        not appear in ``other`` are left alone.
        """
        incoming = self._collect(other, kwargs)
        used: dict[Hashable, int] = {}
        fresh: list[tuple[Hashable, K, V]] = []
        for token, key, value in incoming:
            slot = used.get(token, 0)
            used[token] = slot + 1
            entries = self._index.get(token, [])
            if slot < len(entries):
                entries[slot].key = key
                entries[slot].value = value
            else:
                fresh.append((token, key, value))
        self._drop([entry for token, n in used.items() for entry in self._index.get(token, [])[n:]])
        self._append(fresh)

    @overload
    def getone(self, key: K) -> V: ...
    @overload
    def getone(self, key: K, default: T) -> V | T: ...

    def getone(self, key: K, default: Any = _MISSING) -> Any:
        """Return the first value for ``key``, else ``default`` or raise ``KeyError``."""
        entries = self._index.get(self._probe(key))
        if entries is not None:
            return entries[0].value
        if default is _MISSING:
            raise KeyError(key)
        return default

    def getall(self, key: K) -> list[V]:
        """Return a new list of every value for ``key`` in order, empty if absent."""
        return [entry.value for entry in self._index.get(self._probe(key), ())]

    @overload
    def popone(self, key: K) -> V: ...
    @overload
    def popone(self, key: K, default: T) -> V | T: ...

    def popone(self, key: K, default: Any = _MISSING) -> Any:
        """Remove and return the first value for ``key``; later values stay."""
        entries = self._index.get(self._probe(key))
        if entries is None:
            if default is _MISSING:
                raise KeyError(key)
            return default
        first = entries[0]
        self._drop([first])
        return first.value

    @overload
    def popall(self, key: K) -> list[V]: ...
    @overload
    def popall(self, key: K, default: T) -> list[V] | T: ...

    def popall(self, key: K, default: Any = _MISSING) -> Any:
        """Remove and return every value for ``key``; raise ``KeyError`` if absent."""
        entries = self._index.get(self._probe(key))
        if entries is None:
            if default is _MISSING:
                raise KeyError(key)
            return default
        self._drop(list(entries))
        return [entry.value for entry in entries]

    def popitem(self) -> tuple[K, V]:
        """Remove and return the last pair added; other values of its key stay."""
        if not self._entries:
            raise KeyError("popitem(): multi-dict is empty")
        last = self._entries.pop()
        entries = self._index[last.token]
        entries.pop()
        if not entries:
            del self._index[last.token]
        self._version += 1
        return last.key, last.value

    def allitems(self) -> AllItemsView[K, V]:
        """A live view of every ``(key, value)`` pair in insertion order."""
        return AllItemsView(self)

    def allvalues(self) -> AllValuesView[V]:
        """A live view of every value in insertion order."""
        return AllValuesView(self)

    def to_dict(self) -> dict[K, list[V]]:
        """A new ``dict`` from each key (first spelling) to a new list of its values."""
        return {key: self.getall(key) for key in self}

    def copy(self: Self) -> Self:
        """A shallow copy of the same type; values are shared, not copied."""
        return _copy.copy(self)
