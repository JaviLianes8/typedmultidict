"""Indexed, insertion-ordered storage of key/value pairs behind the mapping protocol."""

from __future__ import annotations

from collections.abc import Hashable, Iterator, Mapping, MutableMapping
from typing import Any, ClassVar, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

_CHANGED = "multi-dict changed during iteration"


class _Entry:
    __slots__ = ("key", "token", "value")

    def __init__(self, token: Hashable, key: Any, value: Any) -> None:
        self.token = token
        self.key = key
        self.value = value


class _Storage(MutableMapping[K, V]):
    # Pairs live in one ordered list; the index maps each key token to its entries in order,
    # so lookups never scan the list. Only removals pay a linear pass.
    __slots__ = ("_entries", "_index", "_version")

    _folds_case: ClassVar[bool] = False

    def _setup(self) -> None:
        self._entries: list[_Entry] = []
        self._index: dict[Hashable, list[_Entry]] = {}
        self._version = 0

    def _token(self, key: K) -> Hashable:
        """The identity a key is stored under; raises for keys this mapping refuses."""
        return key

    def _probe(self, key: object) -> Hashable:
        """The identity to look a key up by; a refused key matches nothing."""
        return key

    def _append(self, pairs: list[tuple[Hashable, K, V]]) -> None:
        for token, _, _ in pairs:
            hash(token)  # an unhashable key must fail before anything is stored
        for token, key, value in pairs:
            entry = _Entry(token, key, value)
            self._entries.append(entry)
            self._index.setdefault(token, []).append(entry)
        self._version += 1

    def _drop(self, doomed: list[_Entry]) -> None:
        if not doomed:
            return
        gone = {id(entry) for entry in doomed}
        self._entries = [entry for entry in self._entries if id(entry) not in gone]
        for token in {entry.token for entry in doomed}:
            kept = [entry for entry in self._index[token] if id(entry) not in gone]
            if kept:
                self._index[token] = kept
            else:
                del self._index[token]
        self._version += 1

    def _iterate(self, version: int) -> Iterator[_Entry]:
        for entry in self._entries:
            yield entry
            if self._version != version:
                raise RuntimeError(_CHANGED)

    def __getitem__(self, key: K) -> V:
        entries = self._index.get(self._probe(key))
        if entries is None:
            raise KeyError(key)
        value: V = entries[0].value
        return value

    def __setitem__(self, key: K, value: V) -> None:
        token = self._token(key)
        entries = self._index.get(token)
        if entries is None:
            self._append([(token, key, value)])
            return
        first = entries[0]
        first.key = key
        first.value = value
        self._drop(entries[1:])
        self._version += 1

    def __delitem__(self, key: K) -> None:
        entries = self._index.get(self._probe(key))
        if entries is None:
            raise KeyError(key)
        self._drop(list(entries))

    def __contains__(self, key: object) -> bool:
        return self._probe(key) in self._index

    def __iter__(self) -> Iterator[K]:
        seen: set[Hashable] = set()
        for entry in self._iterate(self._version):
            if entry.token not in seen:
                seen.add(entry.token)
                yield entry.key

    def __len__(self) -> int:
        return len(self._index)

    def clear(self) -> None:
        self._entries = []
        self._index = {}
        self._version += 1

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _Storage):
            fold = self._folds_case or other._folds_case
            return _compared(self._entries, fold) == _compared(other._entries, fold)
        if isinstance(other, Mapping):
            if not len(self._entries) == len(self._index) == len(other):
                return False
            return {e.key: e.value for e in self._entries} == dict(other.items())
        return NotImplemented

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        pairs = [(entry.key, entry.value) for entry in self._entries]
        return f"{type(self).__name__}({pairs!r})"

    def __reduce__(self) -> tuple[Any, ...]:
        pairs = [(entry.key, entry.value) for entry in self._entries]
        attrs = getattr(self, "__dict__", None) or None
        slots = {name: getattr(self, name) for name in _extra_slots(self) if hasattr(self, name)}
        state = (attrs, slots) if slots else attrs
        return (_rebuild, (type(self), pairs), state)


def _compared(entries: list[_Entry], fold: bool) -> list[tuple[Any, Any]]:
    if not fold:
        return [(entry.token, entry.value) for entry in entries]
    return [
        (str.lower(entry.key) if isinstance(entry.key, str) else entry.key, entry.value)
        for entry in entries
    ]


def _extra_slots(obj: object) -> list[str]:
    # Slots a subclass adds on top of the storage; ours are rebuilt from the pairs.
    names: list[str] = []
    for klass in type(obj).__mro__:
        if klass is _Storage:
            break
        declared = klass.__dict__.get("__slots__", ())
        names.extend([declared] if isinstance(declared, str) else declared)
    return [name for name in names if name not in ("__dict__", "__weakref__")]


def _rebuild(cls: type[_Storage[Any, Any]], pairs: list[tuple[Any, Any]]) -> _Storage[Any, Any]:
    # Restores without calling a subclass __init__, whose signature may differ.
    obj = cls.__new__(cls)
    obj._setup()
    obj._append([(obj._token(key), key, value) for key, value in pairs])
    return obj
