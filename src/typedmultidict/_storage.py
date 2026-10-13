"""Indexed, insertion-ordered storage of key/value pairs behind the mapping protocol."""

from __future__ import annotations

import copyreg
import reprlib
from collections.abc import Hashable, Iterator, Mapping, MutableMapping
from typing import Any, ClassVar, TypeVar

from ._state import restore, state_of

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

_CHANGED = "multi-dict changed during iteration"
# Rebuilds with cls.__new__(cls); pickle encodes it as the compact NEWOBJ opcode.
_NEWOBJ: Any = getattr(copyreg, "__newobj__")  # noqa: B009


class _Entry:
    __slots__ = ("key", "token", "value")

    def __init__(self, token: Hashable, key: Any, value: Any) -> None:
        self.token = token
        self.key = key
        self.value = value


class _Storage(MutableMapping[K, V]):
    # Pairs live in one ordered list; the index maps each key token to its entries in order,
    # so lookups never scan the list. Only removals pay a linear pass. No __slots__: 0.1.0
    # instances took extra attributes and weak references, and still do.

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
        added: list[_Entry] = []
        try:
            for token, key, value in pairs:
                entry = _Entry(token, key, value)
                # A key whose __hash__ or __eq__ raises fails here; undo what came before.
                self._index.setdefault(token, []).append(entry)
                added.append(entry)
        except BaseException:
            for entry in reversed(added):
                self._index[entry.token].pop()
                if not self._index[entry.token]:
                    del self._index[entry.token]
            raise
        self._entries.extend(added)
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
        # Checked before each step, so a change made between iter() and next() is caught.
        for entry in self._entries:
            if self._version != version:
                raise RuntimeError(_CHANGED)
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
        # Not a generator itself, so the version is taken when iter() is called.
        return self._first_keys(self._iterate(self._version))

    def _first_keys(self, entries: Iterator[_Entry]) -> Iterator[K]:
        seen: set[Hashable] = set()
        for entry in entries:
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

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        pairs = [(entry.key, entry.value) for entry in self._entries]
        return f"{type(self).__name__}({pairs!r})"

    def __reduce__(self) -> tuple[Any, ...]:
        # The pairs travel as state, not as arguments, so an object that contains itself is
        # memoised before its pairs are copied. Built with __new__: no __init__ is called.
        return (_NEWOBJ, (type(self),), state_of(self))

    def __setstate__(self, state: Any) -> None:
        restore(self, state)


def _compared(entries: list[_Entry], fold: bool) -> list[tuple[Any, Any]]:
    if not fold:
        return [(entry.token, entry.value) for entry in entries]
    return [
        (str.lower(entry.key) if isinstance(entry.key, str) else entry.key, entry.value)
        for entry in entries
    ]
