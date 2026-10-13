# typedmultidict

Pure-Python typed ordered multi-value dictionary with a case-insensitive variant.

## Install

```
pip install typedmultidict
```

## Usage

A `MultiDict[K, V]` is a normal mapping over the first value of each key, plus methods
that see every value. Pairs keep their insertion order across keys.

```python
from typedmultidict import MultiDict

params: MultiDict[str, str] = MultiDict([("tag", "python"), ("page", "2")])
params.add("tag", "typing")

print(params["tag"])  # python
print(params.getall("tag"))  # ['python', 'typing']
print(len(params), len(params.allitems()))  # 2 3
print(list(params.allitems()))  # [('tag', 'python'), ('page', '2'), ('tag', 'typing')]
print(dict(params))  # {'tag': 'python', 'page': '2'}
print(params.to_dict())  # {'tag': ['python', 'typing'], 'page': ['2']}
```

Assigning replaces every value of a key in the position of its first one; removing can
take the first value, every value, or the last pair added:

```python
from typedmultidict import MultiDict

md = MultiDict([("a", 1), ("b", 2), ("a", 3), ("a", 4)])
md["a"] = 9
print(md)  # MultiDict([('a', 9), ('b', 2)])

md.extend([("a", 5), ("c", 6)])
print(md.popone("a"), md.getall("a"))  # 9 [5]
print(md.popall("a"), "a" in md)  # [5] False
print(md.popitem(), md)  # ('c', 6) MultiDict([('b', 2)])
print(md.getone("missing", "default"))  # default
```

`extend` appends, `merge` only adds keys that are not present yet, and `update` replaces
the values of each incoming key in place (extra new values go to the end, extra old
values are dropped):

```python
from typedmultidict import MultiDict

md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
md.merge([("a", 0), ("c", 4)])
print(md)  # MultiDict([('a', 1), ('b', 2), ('a', 3), ('c', 4)])
md.update([("a", 7), ("a", 8), ("a", 9)], b=0)
print(md)  # MultiDict([('a', 7), ('b', 0), ('a', 8), ('c', 4), ('a', 9)])
```

`CIMultiDict[V]` has `str` keys compared case-insensitively. Every pair keeps the spelling
it was added with, and keys are listed in the spelling of their first pair:

```python
from typedmultidict import CIMultiDict

headers: CIMultiDict[str] = CIMultiDict()
headers.add("Set-Cookie", "a=1")
headers.add("set-cookie", "b=2")
headers.add("Content-Type", "text/html")

print(headers["SET-COOKIE"])  # a=1
print(headers.getall("set-cookie"))  # ['a=1', 'b=2']
print(list(headers))  # ['Set-Cookie', 'Content-Type']
print(5 in headers)  # False
```

Views from `allitems()` and `allvalues()` follow the mapping. Changing the mapping while
iterating over it, or over any of its views, raises `RuntimeError`, as `dict` does:

```python
from typedmultidict import MultiDict

md = MultiDict([("a", 1)])
pairs = md.allitems()
md.add("a", 2)
print(len(pairs), ("a", 2) in pairs)  # 2 True
try:
    for key in md:
        md.add("b", 3)
except RuntimeError as error:
    print(error)  # multi-dict changed during iteration
```

Equality, copies and pickles:

```python
import pickle

from typedmultidict import CIMultiDict, MultiDict

print(MultiDict([("a", 1), ("b", 2)]) == MultiDict([("b", 2), ("a", 1)]))  # False
print(MultiDict([("a", 1), ("b", 2)]) == {"b": 2, "a": 1})  # True
print(MultiDict([("a", 1), ("a", 2)]) == {"a": 1})  # False
print(CIMultiDict([("A", 1)]) == MultiDict([("a", 1)]))  # True

headers = CIMultiDict([("X-Id", "1")])
print(pickle.loads(pickle.dumps(headers)))  # CIMultiDict([('X-Id', '1')])
print(headers.copy() == headers, headers.copy() is headers)  # True False
```

## API

| Name | What it does |
| --- | --- |
| `MultiDict[K, V](initial=None)` | Ordered multi-value mapping. `initial` is a mapping, a multi-dict (every pair is copied) or an iterable of pairs. `K` must be hashable. |
| `CIMultiDict[V](initial=None)` | `MultiDict[str, V]` whose keys compare with `str.lower`. A non-`str` key raises `TypeError` when added and is absent when looked up. |
| `md[key]`, `get`, `in`, `keys`, `items`, `values`, `len()`, iteration | The `Mapping` view: first value of each key, keys once each. |
| `md[key] = value` | Replaces every value of `key` with one, in the place of the first. |
| `del md[key]`, `pop(key[, default])` | Remove every value of `key` (`pop` returns the first). |
| `setdefault(key[, default])` | First value of `key`, or adds `default`. |
| `add(key, value)` | Appends one more pair. |
| `extend(other)` | Appends every pair of `other`. |
| `merge(other)` | Appends the pairs whose key is not present yet. |
| `update(other=(), /, **kwargs)` | Replaces the values of each incoming key in place. |
| `getone(key[, default])` | First value, else `default`, else `KeyError`. |
| `getall(key)` | New list of every value of `key`, empty if absent. |
| `popone(key[, default])` | Removes and returns the first value only. |
| `popall(key[, default])` | Removes and returns every value as a list. |
| `popitem()` | Removes and returns the last pair added (`KeyError` when empty). |
| `allitems()`, `allvalues()` | Live views of every pair or value; `len()` counts pairs. |
| `to_dict()` | New `dict` from each key to a new list of its values. |
| `copy()`, `clear()` | Shallow copy of the same class; remove everything. |

Bulk input (`initial`, `extend`, `merge`, `update`) is read and checked in full first: an
element that is not a pair raises `TypeError`, one of the wrong length raises
`ValueError`, both with its position, and the mapping is left unchanged. Lookups cost the
same whatever the size; removals are linear in the number of pairs.

### Compared with `multidict` and Werkzeug

The method names and their behaviour follow the `multidict` package, with two
differences that keep the type a consistent `Mapping`: `len()` counts keys (use
`len(md.allitems())` for pairs), and `keys`, `items` and `values` show the first value of
each key, as Werkzeug's `MultiDict` does. `getall` returns an empty list for a missing
key instead of raising, and `pop` removes every value of the key.

Like `dict`, a multi-dict is not safe to change from several threads at once without a
lock. Equality between a plain and a case-insensitive multi-dict folds case, so it is not
transitive across the two kinds.

## Why

HTTP headers and query strings routinely carry repeated keys, so a mapping that keeps every
value is a common need. The existing options each fall short for a plain, typed project:

- `multidict` (the aiohttp one) is a C extension; its pure-Python fallback runs many times
  slower and still needs a build step for the fast path.
- `orderedmultidict` depends on `six` and ships no type hints.
- The `MultiDict` types in `werkzeug` and `starlette` come bundled with a whole framework.

`typedmultidict` is a single, standalone, fully typed implementation with `py.typed`, zero
runtime dependencies and no compilation. Reach for it when you want multi-value semantics
and `mypy --strict` support without pulling in a framework or a native wheel.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
