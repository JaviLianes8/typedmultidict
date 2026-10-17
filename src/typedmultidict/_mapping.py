"""The single-value mapping surface: each key once, with its first value."""

from __future__ import annotations

from collections.abc import Hashable, ItemsView, KeysView, ValuesView
from typing import Any, TypeVar, overload

from ._storage import _Storage

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
T = TypeVar("T")


class _Missing:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<missing>"


# Tells "no default given" apart from every value a caller could pass, None included.
_MISSING: Any = _Missing()


class _Mapping(_Storage[K, V]):
    @overload
    def get(self, key: K) -> V | None: ...
    @overload
    def get(self, key: K, default: V) -> V: ...
    @overload
    def get(self, key: K, default: T) -> V | T: ...

    def get(self, key: K, default: Any = None) -> Any:
        """The first value of ``key``, or ``default`` when the key is absent.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("a", 2)])
        >>> md.get("a"), md.get("b"), md.get("b", 0)
        (1, None, 0)
        """
        bucket = self._index.get(self._probe(key))
        return default if bucket is None else bucket[0].value

    def keys(self) -> KeysView[K]:
        """A live, set-like view of the keys, each once, in the order of its first pair.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> list(md.keys()), md.keys() == {"a", "b"}
        (['a', 'b'], True)
        """
        return KeysView(self)

    def items(self) -> ItemsView[K, V]:
        """A live view of ``(key, first value)`` for each key; ``allitems()`` sees every pair.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> list(md.items()), ("a", 3) in md.items()
        ([('a', 1), ('b', 2)], False)
        """
        return ItemsView(self)

    def values(self) -> ValuesView[V]:
        """A live view of the first value of each key; ``allvalues()`` sees every value.

        >>> from typedmultidict import MultiDict
        >>> list(MultiDict([("a", 1), ("b", 2), ("a", 3)]).values())
        [1, 2]
        """
        return ValuesView(self)

    @overload
    def pop(self, key: K) -> V: ...
    @overload
    def pop(self, key: K, default: V) -> V: ...
    @overload
    def pop(self, key: K, default: T) -> V | T: ...

    def pop(self, key: K, default: Any = _MISSING) -> Any:
        """Remove every value of ``key`` and return the first, else ``default`` or ``KeyError``.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
        >>> md.pop("a"), md, md.pop("a", None)
        (1, MultiDict([('b', 2)]), None)
        """
        token = self._probe(key)
        bucket = self._index.get(token)
        if bucket is None:
            if default is _MISSING:
                raise KeyError(key)
            return default
        first = bucket[0].value
        self._trim(token, bucket, 0)
        self._changed()
        return first

    @overload
    def setdefault(self: _Mapping[K, T | None], key: K, default: None = None) -> T | None: ...
    @overload
    def setdefault(self, key: K, default: V) -> V: ...

    def setdefault(self, key: K, default: Any = None) -> Any:
        """The first value of ``key``; when absent, add ``(key, default)`` and return ``default``.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("a", 2)])
        >>> md.setdefault("a", 9), md.setdefault("b", 9), md
        (1, 9, MultiDict([('a', 1), ('a', 2), ('b', 9)]))
        """
        bucket = self._index.get(self._probe(key))
        if bucket is not None:
            return bucket[0].value
        self._append([(self._token(key), key, default)])
        return default

    def clear(self) -> None:
        """Remove every pair.

        >>> from typedmultidict import MultiDict
        >>> md = MultiDict([("a", 1), ("a", 2)])
        >>> md.clear()
        >>> md, len(md)
        (MultiDict([]), 0)
        """
        self._setup()
