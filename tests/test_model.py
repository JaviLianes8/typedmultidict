"""Random operation sequences agree with a plain list-of-pairs model, for both classes."""

from __future__ import annotations

from typing import Any

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

from typedmultidict import CIMultiDict, MultiDict

VALUES = st.integers(0, 4)
# Every casing collision matters to the case-insensitive class and none to the plain one.
KEYS = st.sampled_from(["a", "A", "b", "B", "c"])


class _Machine(RuleBasedStateMachine):
    kind: Any = MultiDict

    def __init__(self) -> None:
        super().__init__()
        self.md: Any = self.kind()
        self.pairs: list[tuple[Any, int]] = []

    def norm(self, key: Any) -> Any:
        return key.lower() if self.kind is CIMultiDict else key

    def where(self, key: Any) -> list[int]:
        return [i for i, (k, _) in enumerate(self.pairs) if self.norm(k) == self.norm(key)]

    def drop(self, positions: list[int]) -> None:
        self.pairs = [p for i, p in enumerate(self.pairs) if i not in set(positions)]

    @rule(key=KEYS, value=VALUES)
    def add(self, key: Any, value: int) -> None:
        self.md.add(key, value)
        self.pairs.append((key, value))

    @rule(key=KEYS, value=VALUES)
    def setitem(self, key: Any, value: int) -> None:
        self.md[key] = value
        found = self.where(key)
        if found:
            self.pairs[found[0]] = (key, value)
            self.drop(found[1:])
        else:
            self.pairs.append((key, value))

    @rule(key=KEYS)
    def delitem(self, key: Any) -> None:
        found = self.where(key)
        try:
            del self.md[key]
        except KeyError:
            assert not found
        else:
            assert found
            self.drop(found)

    @rule(data=st.data())
    def extend(self, data: st.DataObject) -> None:
        new = data.draw(st.lists(st.tuples(KEYS, VALUES), max_size=4))
        self.md.extend(new)
        self.pairs.extend(new)

    @rule(data=st.data())
    def merge(self, data: st.DataObject) -> None:
        new = data.draw(st.lists(st.tuples(KEYS, VALUES), max_size=4))
        present = {self.norm(k) for k, _ in self.pairs}
        self.md.merge(new)
        self.pairs.extend(p for p in new if self.norm(p[0]) not in present)

    @rule(data=st.data())
    def update(self, data: st.DataObject) -> None:
        new = data.draw(st.lists(st.tuples(KEYS, VALUES), max_size=4))
        self.md.update(new)
        slots: dict[Any, list[int]] = {}
        extra = []
        for key, value in new:
            used = slots.setdefault(self.norm(key), [])
            found = self.where(key)
            if len(used) < len(found):
                self.pairs[found[len(used)]] = (key, value)
            else:
                extra.append((key, value))
            used.append(0)
        leftover = [i for t, u in slots.items() for i in self.where_token(t)[len(u) :]]
        self.drop(leftover)
        self.pairs.extend(extra)

    def where_token(self, token: Any) -> list[int]:
        return [i for i, (k, _) in enumerate(self.pairs) if self.norm(k) == token]

    @rule(key=KEYS)
    def popone(self, key: Any) -> None:
        found = self.where(key)
        got = self.md.popone(key, None)
        assert got == (self.pairs[found[0]][1] if found else None)
        self.drop(found[:1])

    @rule(key=KEYS)
    def popall(self, key: Any) -> None:
        found = self.where(key)
        assert self.md.popall(key, []) == [self.pairs[i][1] for i in found]
        self.drop(found)

    @rule(key=KEYS)
    def pop(self, key: Any) -> None:
        found = self.where(key)
        assert self.md.pop(key, None) == (self.pairs[found[0]][1] if found else None)
        self.drop(found)

    @rule(key=KEYS, value=VALUES)
    def setdefault(self, key: Any, value: int) -> None:
        found = self.where(key)
        got = self.md.setdefault(key, value)
        if found:
            assert got == self.pairs[found[0]][1]
        else:
            assert got == value
            self.pairs.append((key, value))

    @precondition(lambda self: bool(self.pairs))
    @rule()
    def popitem(self) -> None:
        assert self.md.popitem() == self.pairs.pop()

    @rule()
    def clear(self) -> None:
        self.md.clear()
        self.pairs = []

    @rule()
    def copy_round_trip(self) -> None:
        twin = self.md.copy()
        assert twin == self.md and twin is not self.md

    @invariant()
    def agrees_with_the_model(self) -> None:
        firsts: dict[Any, tuple[Any, int]] = {}
        for key, value in self.pairs:
            firsts.setdefault(self.norm(key), (key, value))
        assert list(self.md.allitems()) == self.pairs
        assert list(self.md.allvalues()) == [v for _, v in self.pairs]
        assert len(self.md.allitems()) == len(self.pairs)
        assert list(self.md.items()) == list(firsts.values())
        assert list(self.md) == [k for k, _ in firsts.values()]
        assert len(self.md) == len(firsts)
        grouped = {k: [v for kk, v in self.pairs if self.norm(kk) == self.norm(k)] for k in self.md}
        assert self.md.to_dict() == grouped
        assert self.md == self.kind(self.pairs)


class PlainMachine(_Machine):
    kind = MultiDict


class CaseInsensitiveMachine(_Machine):
    kind = CIMultiDict


PlainMachine.TestCase.settings = settings(max_examples=150, stateful_step_count=30, deadline=None)
CaseInsensitiveMachine.TestCase.settings = PlainMachine.TestCase.settings
TestPlain = PlainMachine.TestCase
TestCaseInsensitive = CaseInsensitiveMachine.TestCase
