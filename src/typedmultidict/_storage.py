"""Indexed, insertion-ordered storage of key/value pairs behind the mapping protocol."""

from __future__ import annotations

import copyreg
import reprlib
from collections import deque
from collections.abc import Hashable, Iterator, Mapping, MutableMapping
from typing import Any, ClassVar, TypeVar

from ._state import restore, state_of

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

_CHANGED = "multi-dict changed during iteration"
# Rebuilds with cls.__new__(cls); pickle encodes it as the compact NEWOBJ opcode.
_NEWOBJ: Any = getattr(copyreg, "__newobj__")  # noqa: B009
# Holes left by removals are swept out once they outnumber the live pairs (and this floor).
_SWEEP_FLOOR = 8


class _Entry:
    __slots__ = ("key", "pos", "token", "value")

    def __init__(self, token: Hashable, key: Any, value: Any, pos: int) -> None:
        self.token = token
        self.key = key
        self.value = value
        self.pos = pos


class _Storage(MutableMapping[K, V]):
    # Pairs live in one ordered list where a removed pair leaves a hole (None) until a sweep;
    # the index maps each key token to its entries in order. Every removal takes the first
    # or the last entries of a key, so each operation costs time in proportion to the pairs
    # it reads or removes. No __slots__: 0.1.0 instances took extra attributes and weak
    # references, and still do.

    _folds_case: ClassVar[bool] = False

    def _setup(self) -> None:
        self._entries: list[_Entry | None] = []
        self._index: dict[Hashable, deque[_Entry]] = {}
        self._holes = 0
        # Never reset to a value a live iterator could have seen.
        self._version: int = getattr(self, "_version", 0) + 1

    def _token(self, key: K) -> Hashable:
        """The identity a key is stored under; raises for keys this mapping refuses."""
        return key

    def _probe(self, key: object) -> Hashable:
        """The identity to look a key up by; a refused key matches nothing."""
        return key

    def _live(self) -> Iterator[_Entry]:
        return (entry for entry in self._entries if entry is not None)

    def _count(self) -> int:
        return len(self._entries) - self._holes

    def _append(self, pairs: list[tuple[Hashable, K, V]]) -> None:
        added: list[_Entry] = []
        start = len(self._entries)
        try:
            for token, key, value in pairs:
                entry = _Entry(token, key, value, start + len(added))
                # A key whose __hash__ or __eq__ raises fails here; undo what came before.
                self._index.setdefault(token, deque()).append(entry)
                added.append(entry)
        except BaseException:
            for entry in reversed(added):
                self._index[entry.token].pop()
                if not self._index[entry.token]:
                    del self._index[entry.token]
            raise
        self._entries.extend(added)
        self._version += 1

    def _hole(self, entry: _Entry) -> None:
        self._entries[entry.pos] = None
        self._holes += 1

    def _changed(self) -> None:
        self._version += 1
        if self._holes > _SWEEP_FLOOR and self._holes * 2 > len(self._entries):
            live = list(self._live())
            for pos, entry in enumerate(live):
                entry.pos = pos
            self._entries = live  # type: ignore[assignment]
            self._holes = 0

    def _trim(self, token: Hashable, bucket: deque[_Entry], keep: int) -> None:
        """Remove the entries of one key beyond its first ``keep``."""
        while len(bucket) > keep:
            self._hole(bucket.pop())
        if not bucket:
            del self._index[token]

    def _iterate(self, version: int) -> Iterator[_Entry]:
        # Checked before each step, so a change made between iter() and next() is caught.
        for entry in self._entries:
            if self._version != version:
                raise RuntimeError(_CHANGED)
            if entry is not None:
                yield entry
        if self._version != version:
            raise RuntimeError(_CHANGED)

    def __getitem__(self, key: K) -> V:
        bucket = self._index.get(self._probe(key))
        if bucket is None:
            raise KeyError(key)
        value: V = bucket[0].value
        return value

    def __setitem__(self, key: K, value: V) -> None:
        token = self._token(key)
        bucket = self._index.get(token)
        if bucket is None:
            self._append([(token, key, value)])
            return
        first = bucket[0]
        first.key = key
        first.value = value
        self._trim(token, bucket, 1)
        self._changed()

    def __delitem__(self, key: K) -> None:
        token = self._probe(key)
        bucket = self._index.get(token)
        if bucket is None:
            raise KeyError(key)
        self._trim(token, bucket, 0)
        self._changed()

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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _Storage):
            fold = self._folds_case or other._folds_case
            return _compared(self, fold) == _compared(other, fold)
        if isinstance(other, Mapping):
            if not self._count() == len(self._index) == len(other):
                return False
            return {e.key: e.value for e in self._live()} == dict(other.items())
        return NotImplemented

    __hash__ = None  # type: ignore[assignment]

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        pairs = [(entry.key, entry.value) for entry in self._live()]
        return f"{type(self).__name__}({pairs!r})"

    def __reduce__(self) -> tuple[Any, ...]:
        # The pairs travel as state, not as arguments, so an object that contains itself is
        # memoised before its pairs are copied. Built with __new__: no __init__ is called.
        return (_NEWOBJ, (type(self),), state_of(self))

    def __setstate__(self, state: Any) -> None:
        restore(self, state)


def _compared(storage: _Storage[Any, Any], fold: bool) -> list[tuple[Any, Any]]:
    if not fold:
        return [(entry.token, entry.value) for entry in storage._live()]
    return [
        (str.lower(entry.key) if isinstance(entry.key, str) else entry.key, entry.value)
        for entry in storage._live()
    ]
