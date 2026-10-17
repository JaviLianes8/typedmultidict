"""Reading and removing every value of a key, not only the first."""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any, TypeVar, overload

from ._mapping import _MISSING, _Mapping
from ._views import AllItemsView, AllValuesView

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
T = TypeVar("T")


class _MultiValues(_Mapping[K, V]):
    @overload
    def getone(self, key: K) -> V: ...
    @overload
    def getone(self, key: K, default: T) -> V | T: ...

    def getone(self, key: K, default: Any = _MISSING) -> Any:
        """The first value of ``key``, else ``default``, else raise ``KeyError``.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("a", 2)])
        >>> md.getone("a"), md.getone("b", None)
        (1, None)
        """
        bucket = self._index.get(self._probe(key))
        if bucket is not None:
            return bucket[0].value
        if default is _MISSING:
            raise KeyError(key)
        return default

    @overload
    def getall(self, key: K) -> list[V]: ...
    @overload
    def getall(self, key: K, default: T) -> list[V] | T: ...

    def getall(self, key: K, default: Any = _MISSING) -> Any:
        """A new list of every value of ``key`` in order; for an absent key, ``default``
        when given, else an empty list.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> md.getall("a"), md.getall("c"), md.getall("c", None)
        ([1, 3], [], None)
        """
        bucket = self._index.get(self._probe(key))
        if bucket is None:
            return [] if default is _MISSING else default
        return [entry.value for entry in bucket]

    @overload
    def popone(self, key: K) -> V: ...
    @overload
    def popone(self, key: K, default: T) -> V | T: ...

    def popone(self, key: K, default: Any = _MISSING) -> Any:
        """Remove and return the first value of ``key``; later values stay.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> md.popone("a"), md, md.popone("c", None)
        (1, MultiDict([('b', 2), ('a', 3)]), None)
        """
        token = self._probe(key)
        bucket = self._index.get(token)
        if bucket is None:
            if default is _MISSING:
                raise KeyError(key)
            return default
        first = bucket.popleft()
        self._hole(first)
        if not bucket:
            del self._index[token]
        self._changed()
        return first.value

    @overload
    def popall(self, key: K) -> list[V]: ...
    @overload
    def popall(self, key: K, default: T) -> list[V] | T: ...

    def popall(self, key: K, default: Any = _MISSING) -> Any:
        """Remove and return every value of ``key`` as a list, else ``default`` or ``KeyError``.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> md.popall("a"), md, md.popall("a", [])
        ([1, 3], MultiDict([('b', 2)]), [])
        """
        token = self._probe(key)
        bucket = self._index.get(token)
        if bucket is None:
            if default is _MISSING:
                raise KeyError(key)
            return default
        values = [entry.value for entry in bucket]
        self._trim(token, bucket, 0)
        self._changed()
        return values

    def popitem(self) -> tuple[K, V]:
        """Remove and return the last pair added; other values of its key stay.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> md.popitem(), md
        (('a', 3), MultiDict([('a', 1), ('b', 2)]))
        """
        if not self._index:
            raise KeyError("popitem(): multi-dict is empty")
        last = self._entries.pop()
        while last is None:  # holes at the end go with it
            self._holes -= 1
            last = self._entries.pop()
        bucket = self._index[last.token]
        bucket.pop()
        if not bucket:
            del self._index[last.token]
        self._changed()
        return last.key, last.value

    def allitems(self) -> AllItemsView[K, V]:
        """A live view of every ``(key, value)`` pair in insertion order.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2)])
        >>> pairs = md.allitems()
        >>> md.add("a", 3)
        >>> list(pairs), len(pairs)
        ([('a', 1), ('b', 2), ('a', 3)], 3)
        """
        return AllItemsView(self)

    def allvalues(self) -> AllValuesView[V]:
        """A live view of every value in insertion order.

        >>> from typedmultidict import MultiDict
        >>> list(MultiDict([("a", 1), ("b", 2), ("a", 3)]).allvalues())
        [1, 2, 3]
        """
        return AllValuesView(self)

    def to_dict(self) -> dict[K, list[V]]:
        """A new ``dict`` from each key (spelled as in its first pair) to a new list of its values.

        >>> from typedmultidict import MultiDict
        >>> MultiDict([("a", 1), ("b", 2), ("a", 3)]).to_dict()
        {'a': [1, 3], 'b': [2]}
        """
        result: dict[K, list[V]] = {}
        lists: dict[Hashable, list[V]] = {}
        for entry in self._live():
            values = lists.get(entry.token)
            if values is None:
                values = lists[entry.token] = result[entry.key] = []
            values.append(entry.value)
        return result
