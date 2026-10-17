"""A strictly typed outside program: checked with mypy --strict against the installed wheel."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView

from typedmultidict import AllItemsView, AllValuesView, CIMultiDict, MultiDict


def summary(headers: CIMultiDict[str]) -> dict[str, list[str]]:
    return headers.to_dict()


md: MultiDict[str, int] = MultiDict([("a", 1)])
md.add("a", 2)
md.extend({"b": 3})
md.update([("c", 4)], d=5)
md.merge([("e", 6)])
first: int = md["a"]
maybe: int | None = md.get("x")
fallback: int | str = md.getone("x", "none")
values: list[int] = md.getall("a")
values_or_none: list[int] | None = md.getall("x", None)
popped: int = md.popone("a")
every: list[int] = md.popall("b")
pair: tuple[str, int] = md.popitem()
pairs: AllItemsView[str, int] = md.allitems()
all_values: AllValuesView[int] = md.allvalues()
keys: KeysView[str] = md.keys()
items: ItemsView[str, int] = md.items()
firsts: ValuesView[int] = md.values()
twin: MultiDict[str, int] = md.copy()
default: int = md.setdefault("z", 0)
gone: int | None = md.pop("z", None)
headers: CIMultiDict[str] = CIMultiDict({"Accept": "x"})
assert summary(headers) == {"Accept": ["x"]}
assert (first, maybe, fallback, values_or_none, popped, every) == (1, None, "none", None, 1, [3])
assert pair == ("e", 6) and len(pairs) == len(all_values) == 3 and twin == md
assert list(keys) == ["a", "c", "d"] and default == 0 and gone == 0
assert len(items) == len(firsts) == len(md) and values == [1, 2]
print("typed ok")
