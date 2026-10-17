"""Run one scenario through a reference or through typedmultidict, recording every answer."""

from __future__ import annotations

from typing import Any

from oracle_refs import OURS


def _plain(value: Any) -> Any:
    # JSON has no tuples; references return tuples, lists or their own sequence types.
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _first_spellings(pairs: list[list[Any]], fold: bool) -> list[Any]:
    seen: set[Any] = set()
    keys: list[Any] = []
    for key, _ in pairs:
        token = key.lower() if fold else key
        if token not in seen:
            seen.add(token)
            keys.append(key)
    return keys


def snapshot(name: str, obj: Any, fold: bool) -> dict[str, Any]:
    """What the reference shows of its state: pairs in order, keys, and values per key."""
    if name == "werkzeug-multidict":
        grouped = _plain(list(obj.to_dict(flat=False).items()))
        return {"keys": list(obj.keys()), "grouped": grouped}
    if name == "requests":
        return {"pairs": _plain(list(obj.items())), "keys": list(obj)}
    pairs = _plain(list(obj.items()))
    return {"pairs": pairs, "keys": _first_spellings(pairs, fold)}


def ours_snapshot(md: Any) -> dict[str, Any]:
    return {
        "pairs": _plain(list(md.allitems())),
        "keys": list(md),
        "grouped": _plain(list(md.to_dict().items())),
    }


def run_reference(name: str, ref: tuple[bool, list[str], Any, dict[str, Any]],
                  case: dict[str, Any]) -> list[Any]:  # fmt: skip
    fold, _, factory, ops = ref
    obj = factory([tuple(pair) for pair in case["initial"]])
    record: list[Any] = [snapshot(name, obj, fold)]
    for step in case["steps"]:
        op, *args = step
        if op in ("extend", "update", "merge"):
            args = [[tuple(pair) for pair in args[0]]]
        result = _plain(ops[op](obj, *args))
        record.append([result, snapshot(name, obj, fold)])
    return record


def run_ours(cls: Any, case: dict[str, Any]) -> list[Any]:
    md = cls([tuple(pair) for pair in case["initial"]])
    record: list[Any] = [ours_snapshot(md)]
    for step in case["steps"]:
        op, *args = step
        if op in ("extend", "update", "merge"):
            args = [[tuple(pair) for pair in args[0]]]
        record.append([_plain(OURS[op](md, *args)), ours_snapshot(md)])
    return record


def agrees(reference: list[Any], ours: list[Any]) -> bool:
    """True when every answer and every field the reference shows match ours."""

    def same(theirs: dict[str, Any], mine: dict[str, Any]) -> bool:
        return all(mine[field] == value for field, value in theirs.items())

    if not same(reference[0], ours[0]):
        return False
    for (result, state), (my_result, my_state) in zip(reference[1:], ours[1:], strict=False):
        if result != my_result or not same(state, my_state):
            return False
    return len(reference) == len(ours)
