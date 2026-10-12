"""Ordered mapping where a single key can hold several values."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator, Mapping, MutableMapping
from typing import TypeVar, Union

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

MultiDictInput = Union["MultiDict[K, V]", Mapping[K, V], Iterable[tuple[K, V]]]


class _Missing:
    pass


_MISSING = _Missing()


class MultiDict(MutableMapping[K, V]):
    """A typed, insertion-ordered multi-value mapping.

    Mapping operations act on the first value of each key, so the type behaves like a
    normal mapping. The multi-value surface (``add``, ``getall``, ``allitems``) exposes
    every stored pair in insertion order.
    """

    def __init__(self, initial: MultiDictInput[K, V] | None = None) -> None:
        self._items: list[tuple[K, V]] = []
        if initial is not None:
            self.extend(initial)

    def _norm(self, key: K) -> Hashable:
        return key

    def add(self, key: K, value: V) -> None:
        """Append another value for ``key`` without replacing existing ones."""
        self._items.append((key, value))

    def extend(self, other: MultiDictInput[K, V]) -> None:
        """Add every pair from another mapping, multi-dict or iterable of pairs."""
        for key, value in self._pairs(other):
            self._items.append((key, value))

    def getone(self, key: K) -> V:
        """Return the first value for ``key`` or raise ``KeyError``."""
        return self[key]

    def getall(self, key: K) -> list[V]:
        """Return every value for ``key`` in insertion order, empty if absent."""
        token = self._norm(key)
        return [value for stored, value in self._items if self._norm(stored) == token]

    def popall(self, key: K, default: list[V] | _Missing = _MISSING) -> list[V]:
        """Remove and return every value for ``key``; raise ``KeyError`` if absent."""
        values = self.getall(key)
        if not values:
            if isinstance(default, _Missing):
                raise KeyError(key)
            return default
        token = self._norm(key)
        self._items = [pair for pair in self._items if self._norm(pair[0]) != token]
        return values

    def allitems(self) -> Iterator[tuple[K, V]]:
        """Iterate over every ``(key, value)`` pair in insertion order."""
        yield from self._items

    def __getitem__(self, key: K) -> V:
        token = self._norm(key)
        for stored, value in self._items:
            if self._norm(stored) == token:
                return value
        raise KeyError(key)

    def __setitem__(self, key: K, value: V) -> None:
        token = self._norm(key)
        kept: list[tuple[K, V]] = []
        replaced = False
        for stored, current in self._items:
            if self._norm(stored) != token:
                kept.append((stored, current))
            elif not replaced:
                kept.append((key, value))
                replaced = True
        if not replaced:
            kept.append((key, value))
        self._items = kept

    def __delitem__(self, key: K) -> None:
        token = self._norm(key)
        kept = [pair for pair in self._items if self._norm(pair[0]) != token]
        if len(kept) == len(self._items):
            raise KeyError(key)
        self._items = kept

    def __iter__(self) -> Iterator[K]:
        seen: set[Hashable] = set()
        for key, _ in self._items:
            token = self._norm(key)
            if token not in seen:
                seen.add(token)
                yield key

    def __len__(self) -> int:
        return len({self._norm(key) for key, _ in self._items})

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MultiDict):
            return NotImplemented
        left = [(self._norm(k), v) for k, v in self._items]
        right = [(other._norm(k), v) for k, v in other._items]
        return left == right

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._items!r})"

    def _pairs(self, other: MultiDictInput[K, V]) -> Iterator[tuple[K, V]]:
        if isinstance(other, MultiDict):
            yield from other._items
        elif isinstance(other, Mapping):
            for key in other:
                yield key, other[key]
        else:
            yield from other
