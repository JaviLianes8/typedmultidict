"""Ordered mapping where a single key can hold several values."""

from __future__ import annotations

import copy as _copy
from collections.abc import Hashable, Iterator
from typing import TYPE_CHECKING, Any, TypeVar, overload

from ._guard import exclusive
from ._pairs import MultiDictInput, read_pairs
from ._storage import _Entry, _Storage
from ._values import _MultiValues

if TYPE_CHECKING:
    from collections.abc import Iterable

    from _typeshed import SupportsKeysAndGetItem

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
Self = TypeVar("Self", bound="MultiDict[Any, Any]")


class MultiDict(_MultiValues[K, V]):
    """A typed, insertion-ordered multi-value mapping.

    Mapping operations act on the first value of each key, so the type behaves like a
    normal mapping (``len()`` counts keys). The multi-value surface (``add``, ``getall``,
    ``allitems`` and friends) sees every stored pair in insertion order. ``initial`` is a
    multi-dict (every pair is copied), a mapping or header object (read through ``items()``,
    else ``keys()``) or an iterable of ``(key, value)`` pairs.

    >>> from typedmultidict import MultiDict
    >>> md = MultiDict([("tag", "a"), ("page", "2"), ("tag", "b")])
    >>> md["tag"], md.getall("tag"), len(md), "page" in md
    ('a', ['a', 'b'], 2, True)
    >>> md["tag"] = "c"
    >>> del md["page"]
    >>> md, list(md), md == {"tag": "c"}
    (MultiDict([('tag', 'c')]), ['tag'], True)
    """

    def __init__(self, initial: MultiDictInput[K, V] | None = None) -> None:
        self._reset()
        if initial is not None:
            self.extend(initial)  # through extend, so a subclass hook sees the input

    @exclusive
    def _reset(self) -> None:
        self._setup()

    def _collect(self, source: object, extra: dict[str, Any]) -> list[tuple[Hashable, K, V]]:
        pairs = read_pairs(source, _Storage)
        pairs.extend(extra.items())
        return [(self._token(key), key, value) for key, value in pairs]

    @exclusive
    def add(self, key: K, value: V) -> None:
        """Append another value for ``key`` without replacing existing ones.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1)])
        >>> md.add("a", 2)
        >>> md
        MultiDict([('a', 1), ('a', 2)])
        """
        self._append([(self._token(key), key, value)])

    @exclusive
    def extend(self, other: MultiDictInput[K, V]) -> None:
        """Append every pair of a mapping, multi-dict or iterable of pairs.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1)])
        >>> md.extend([("a", 2), ("b", 3)])
        >>> md
        MultiDict([('a', 1), ('a', 2), ('b', 3)])
        """
        self._append(self._collect(other, {}))

    @exclusive
    def merge(self, other: MultiDictInput[K, V]) -> None:
        """Append the pairs whose key is not present yet; keys already here are skipped.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1)])
        >>> md.merge([("a", 2), ("b", 3), ("b", 4)])
        >>> md
        MultiDict([('a', 1), ('b', 3), ('b', 4)])
        """
        incoming = self._collect(other, {})
        self._append([item for item in incoming if item[0] not in self._index])

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

    @exclusive
    def update(self, other: Any = (), /, **kwargs: Any) -> None:
        """Replace the values of every incoming key, reusing the old positions in order.

        Extra new values go to the end, extra old values are removed, and keys that do
        not appear in ``other`` (or as keyword arguments) are left alone.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> md.update([("a", 7), ("a", 8), ("a", 9)], b=0)
        >>> md
        MultiDict([('a', 7), ('b', 0), ('a', 8), ('a', 9)])
        """
        # Plan first: every hash and key comparison happens before anything changes.
        used: dict[Hashable, int] = {}
        cursors: dict[Hashable, Iterator[_Entry]] = {}
        reused: list[tuple[_Entry, K, V]] = []
        fresh: list[tuple[Hashable, K, V]] = []
        for token, key, value in self._collect(other, kwargs):
            used[token] = used.get(token, 0) + 1
            cursor = cursors.get(token)
            if cursor is None:
                cursor = cursors[token] = iter(self._index.get(token, ()))
            entry = next(cursor, None)
            if entry is None:
                fresh.append((token, key, value))
            else:
                reused.append((entry, key, value))
        stale = [
            (token, bucket, n)
            for token, n in used.items()
            if (bucket := self._index.get(token)) is not None and len(bucket) > n
        ]
        self._append(fresh)  # undoes itself if it fails; nothing after it can fail
        for entry, key, value in reused:
            entry.key = key
            entry.value = value
        for token, bucket, n in stale:
            self._trim(token, bucket, n)
        self._changed()

    def copy(self: Self) -> Self:
        """A shallow copy of the same type; values are shared, not copied.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", [1])])
        >>> twin = md.copy()
        >>> twin == md, twin is md, twin["a"] is md["a"]
        (True, False, True)
        """
        return _copy.copy(self)
