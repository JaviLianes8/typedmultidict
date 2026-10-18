# typedmultidict

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Pure-Python typed ordered multi-value dictionary with a case-insensitive variant.

A `MultiDict` keeps every `(key, value)` pair of a query string or a header block, in
order, and still behaves as a normal `Mapping` over the first value of each key.
`CIMultiDict` compares keys case-insensitively, as HTTP field names require (RFC 9110,
section 5.1). Zero dependencies, `mypy --strict` clean, and every operation costs time in
proportion to the pairs it touches.

Read the [guide](https://github.com/JaviLianes8/typedmultidict/blob/main/GUIDE.md) for
every rule and the comparison with other implementations, and the
[changelog](https://github.com/JaviLianes8/typedmultidict/blob/main/CHANGELOG.md) for what
changed between releases.

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
iterating over it, or over any of its views, raises `RuntimeError`. As in `multidict`,
every write counts, even replacing a value in place (which `dict` allows):

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
| `MultiDict[K, V](initial=None)` | Ordered multi-value mapping. `initial` is a multi-dict (every pair is copied), a mapping or header object (read through `items()`, else `keys()`) or an iterable of pairs. `K` must be hashable. |
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
| `getall(key[, default])` | New list of every value of `key`; if absent, `default` when given, else an empty list. |
| `popone(key[, default])` | Removes and returns the first value only. |
| `popall(key[, default])` | Removes and returns every value as a list. |
| `popitem()` | Removes and returns the last pair added (`KeyError` when empty). |
| `allitems()`, `allvalues()` | Live views of every pair or value (`AllItemsView`, `AllValuesView`); `len()` counts pairs. |
| `to_dict()` | New `dict` from each key to a new list of its values. |
| `copy()`, `clear()` | Shallow copy of the same class; remove everything. |

Bulk input (`initial`, `extend`, `merge`, `update`) is read and checked in full first: an
element that is not a pair raises `TypeError`, one of the wrong length raises
`ValueError`, both with its position, and the mapping is left unchanged. A source with
`items()` is read through it, so an `http.client` or `email` message keeps every field of
a repeated name. Lookups cost the same whatever the size, and so do `add`, `popone` and
`popitem` on average; other removals cost time in proportion to the pairs they remove.

### Compared with `multidict` and Werkzeug

The method names and their behaviour follow the `multidict` package, except where
that would break the `Mapping` contract: `len()` counts keys (use
`len(md.allitems())` for pairs), and `items` and `values` show the first value of each
key, as Werkzeug's `MultiDict` does. `getall` returns an empty list for a missing key
instead of raising, and `pop` removes every value of the key.

Like `dict`, a multi-dict is not safe to change from several threads at once without a
lock. Equality between a plain and a case-insensitive multi-dict folds case, so it is not
transitive across the two kinds. Any other mapping, a `multidict.MultiDict` included, is
compared as a plain mapping.

## Why

HTTP headers and query strings routinely carry repeated keys, so a mapping that keeps every
value is a common need. The established options each make a trade-off:

- `multidict` (aio-libs) is fast and typed, but `len()`, `items()` and `values()` count
  every pair, so it is not a `Mapping` of keys; `getall` raises for a missing key and `pop`
  removes a single value. Version 7.1.0 ships 169 compiled wheels next to its pure-Python one.
- Werkzeug's `MultiDict` comes with the Werkzeug WSGI library and stores values per key,
  so the order of pairs across keys is lost (`items(multi=True)` groups them by key), and
  its `update` appends.
- `orderedmultidict` depends on `six`; requests' `CaseInsensitiveDict` keeps one value per
  name; `email.message` appends on assignment.

`typedmultidict` is a single, standalone implementation with zero runtime dependencies
and `py.typed`: a true `MutableMapping`, the full multi-value API, pair order kept exactly,
and behaviour checked call by call against all of the above (see the
[guide](https://github.com/JaviLianes8/typedmultidict/blob/main/GUIDE.md)).

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/typedmultidict/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
