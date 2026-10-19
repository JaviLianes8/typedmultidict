"""Seeded fuzz: long, removal-heavy operation runs agree with a naive list of pairs.

Long runs leave many holes in the storage and trigger its sweeps, which short property
tests rarely reach. Every seed is fixed, so a failure is replayed by its id.
"""

from __future__ import annotations

import pickle
import random
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict

MISSING = object()


class _Naive:
    def __init__(self, fold: bool) -> None:
        self.fold, self.pairs = fold, []  # type: ignore[var-annotated]

    def norm(self, key: str) -> str:
        return key.lower() if self.fold else key

    def at(self, key: str) -> list[int]:
        return [i for i, (k, _) in enumerate(self.pairs) if self.norm(k) == self.norm(key)]

    def keep(self, doomed: list[int]) -> None:
        self.pairs = [p for i, p in enumerate(self.pairs) if i not in set(doomed)]

    def apply(self, op: str, key: str, value: int, batch: list[tuple[str, int]]) -> Any:
        found = self.at(key)
        if op == "add":
            self.pairs.append((key, value))
        elif op == "set":
            if found:
                self.pairs[found[0]] = (key, value)
                self.keep(found[1:])
            else:
                self.pairs.append((key, value))
        elif op in ("delete", "pop", "popall", "popone"):
            if not found:
                return MISSING
            values = [self.pairs[i][1] for i in found]
            self.keep(found[:1] if op == "popone" else found)
            return values if op == "popall" else values[0]
        elif op == "popitem":
            return self.pairs.pop() if self.pairs else MISSING
        elif op == "update":
            spots = {self.norm(k): self.at(k) for k, _ in batch}
            used = dict.fromkeys(spots, 0)
            fresh = []
            for pair in batch:
                k = self.norm(pair[0])
                if used[k] < len(spots[k]):
                    self.pairs[spots[k][used[k]]] = pair
                else:
                    fresh.append(pair)
                used[k] += 1
            self.keep([i for k, n in used.items() for i in spots[k][n:]])
            self.pairs.extend(fresh)
        elif op == "merge":
            present = {self.norm(k) for k, _ in self.pairs}
            self.pairs.extend(p for p in batch if self.norm(p[0]) not in present)
        elif op == "setdefault":
            if found:
                return self.pairs[found[0]][1]
            self.pairs.append((key, value))
            return value
        elif op == "clear":
            self.pairs = []
        return None


def _ours(md: Any, op: str, key: str, value: int, batch: list[tuple[str, int]]) -> Any:
    calls = {
        "add": lambda: md.add(key, value),
        "set": lambda: md.__setitem__(key, value),
        "delete": lambda: md.pop(key, MISSING),
        "pop": lambda: md.pop(key, MISSING),
        "popall": lambda: md.popall(key, MISSING),
        "popone": lambda: md.popone(key, MISSING),
        "popitem": lambda: md.popitem() if md else MISSING,
        "update": lambda: md.update(batch),
        "merge": lambda: md.merge(batch),
        "setdefault": lambda: md.setdefault(key, value),
        "clear": md.clear,
    }
    return calls[op]()


OPS = ["add"] * 6 + ["set", "delete", "pop", "popall", "popone", "popone", "popitem"] * 2
OPS += ["update", "merge", "setdefault", "clear"]


@pytest.mark.parametrize("seed", range(60))
def test_long_runs_agree_with_a_naive_model(seed: int) -> None:
    rng = random.Random(seed)
    cls = CIMultiDict if seed % 2 else MultiDict
    keys = ["a", "A", "b", "B", "c", "d"][: rng.randrange(2, 7)]
    md: Any = cls()
    model = _Naive(fold=cls is CIMultiDict)
    for step in range(600):
        op, key, value = rng.choice(OPS), rng.choice(keys), rng.randrange(9)
        batch = [(rng.choice(keys), rng.randrange(9)) for _ in range(rng.randrange(4))]
        if op == "clear" and rng.random() < 0.8:
            op = "add"
        assert _ours(md, op, key, value, batch) == model.apply(op, key, value, batch), step
        assert list(md.allitems()) == model.pairs, (seed, step, op)
        assert len(md.allitems()) == len(model.pairs)
        assert len(md) == len({model.norm(k) for k, _ in model.pairs})
        if step % 97 == 0:
            assert pickle.loads(pickle.dumps(md)) == md
            assert list(md.copy().allitems()) == model.pairs
            assert md.to_dict() == {k: md.getall(k) for k in md}
