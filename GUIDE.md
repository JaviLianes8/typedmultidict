# typedmultidict guide

This guide describes every behaviour the 1.x series promises. The README has the short
version; the [CHANGELOG](https://github.com/JaviLianes8/typedmultidict/blob/main/CHANGELOG.md)
lists what changed between releases.

## The model

A multi-dict is an ordered list of `(key, value)` pairs in which a key may repeat. Two
views of that list exist side by side:

| Surface | Sees | Methods |
| --- | --- | --- |
| Mapping | each key once, with its first value, in the order of its first pair | `md[key]`, `get`, `in`, `len()`, iteration, `keys`, `items`, `values`, `==` |
| Multi-value | every pair, in insertion order | `add`, `extend`, `getall`, `popone`, `popall`, `popitem`, `allitems`, `allvalues`, `to_dict` |

So a `MultiDict` is a real `collections.abc.MutableMapping`: code written for a `dict`
reads it correctly, and `len()` counts keys. `len(md.allitems())` counts pairs. One
caveat: `update` keeps every incoming value (see below), so `md.update([("a", 1)], a=2)`
leaves `md["a"] == 1` where a `dict` would hold 2, and a case-insensitive multi-dict
keeps both `A` and `a` from `update({"A": 0, "a": 1})`.

```python
from typedmultidict import MultiDict

md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
print(len(md), len(md.allitems()))  # 2 3
print(list(md.items()), md.getall("a"))  # [('a', 1), ('b', 2)] [1, 3]
```

## Writing

| Call | Effect |
| --- | --- |
| `md.add(k, v)` | appends one pair |
| `md.extend(other, **kw)` | appends every pair of `other`, then the keyword pairs |
| `md.merge(other, **kw)` | appends the pairs of `other` and the keyword pairs whose key is not present before the call |
| `md[k] = v` | the first pair of `k` becomes `(k, v)` in place, every later pair of `k` goes; a new key goes to the end |
| `md.update(other, **kw)` | for each incoming key, its incoming values overwrite its existing pairs in order; extra incoming values go to the end, extra existing pairs go |
| `md.setdefault(k, v)` | the first value of `k`; when absent, appends `(k, v)` and returns `v` |
| `del md[k]`, `md.pop(k)` | remove every pair of `k` (`pop` returns the first value) |
| `md.popone(k)` | removes and returns only the first value of `k` |
| `md.popall(k)` | removes every pair of `k` and returns their values |
| `md.popitem()` | removes and returns the last pair in order (an in-place write does not move a pair); other pairs of its key stay |
| `md.clear()` | removes everything |

The constructor takes the same arguments as `extend`: `MultiDict([("a", 1)], b=2)`.
`other` is positional only and optional, so keyword pairs may use any string key, as in
`dict()`. `other` may be a multi-dict (every pair is copied, not only first values),
anything with an `items()` method (read through `items()`: a `dict`, or a header object such as an
`http.client.HTTPMessage`, an `email.message.Message`, a `wsgiref.headers.Headers` or a
`multidict.CIMultiDict`, each of which lists every field there), anything else with
`keys()` (read like `dict.update` reads it) or an iterable of pairs. Werkzeug's
`MultiDict` lists only first values in `items()`: pass `items(multi=True)` to copy every
pair. Bulk input is read and checked in full before anything changes: an element that
is not iterable raises `TypeError`, one whose length is not 2 raises `ValueError`, both
naming its position; at most three items of each element are read, so an endless element
fails at once. `md.extend(md)` doubles the pairs and returns.

```python
import http.client
import io

from typedmultidict import CIMultiDict, MultiDict

md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
md.update([("a", 7), ("a", 8), ("a", 9)], b=0)
print(md)  # MultiDict([('a', 7), ('b', 0), ('a', 8), ('a', 9)])

raw = b"Set-Cookie: a=1\r\nX-Id: 7\r\nset-cookie: b=2\r\n\r\n"
headers = CIMultiDict(http.client.parse_headers(io.BytesIO(raw)))
print(headers.getall("SET-COOKIE"), headers["x-id"])  # ['a=1', 'b=2'] 7
```

## Case-insensitive keys

`CIMultiDict[V]` is a `MultiDict[str, V]` whose keys are compared after `str.lower`.
RFC 9110 section 5.1 states that HTTP field names are case-insensitive, and every
case-insensitive reference checked here (multidict, Werkzeug's `Headers`, requests,
`email.message` and `http.client`, `wsgiref.headers`) folds with `str.lower` too, so they
agree on non-ASCII names as well: `"K"` (Kelvin sign) matches `"k"`, while
`"Straße"` does not match `"STRASSE"` (`str.casefold` would say it does). One
exception: from Python 3.14, `email.message` refuses a field name outside printable ASCII
with `ValueError` instead of folding it.

- Every pair keeps the spelling it was added with; `md[k] = v` and `update` store the
  new spelling. Iteration and `to_dict` show each key in the spelling of its first pair.
- Keys must be `str` or a `str` subclass. Adding any other key raises `TypeError`; looking one
  up finds nothing, so `5 in headers` is `False` and `headers.get(5)` is `None`.

RFC 9110 section 5.3 makes the order of field lines with the same name significant, and
a multi-dict keeps that order exactly.

## Views and iteration

`keys()`, `items()` and `values()` are the standard live mapping views (first values);
`allitems()` and `allvalues()` return live `AllItemsView` and `AllValuesView` objects over
every pair. Changing a multi-dict while iterating over it or over any of its views raises
`RuntimeError`, as soon as the next item is requested. As in `multidict`, every write
counts, even replacing a value in place, which `dict` allows.

## Equality, copies and pickles

- Two multi-dicts are equal when their pairs are equal in order. If either one is a
  `CIMultiDict`, string keys are compared after `str.lower`; so equality between a plain
  and a case-insensitive multi-dict is not transitive.
- Any other mapping (a `dict`, a `multidict.MultiDict`) is equal when the multi-dict
  has one value per key, both have the same `len()`, and `dict(other.items())` equals
  the multi-dict's keys and values. String keys are compared exactly here, even for a
  `CIMultiDict` and even against another library's case-insensitive mapping.
- Multi-dicts are unhashable. `copy()` and `copy.copy` are shallow; `copy.deepcopy` and
  `pickle` work, keep subclass attributes and slots, and allow a multi-dict that contains
  itself. Pickles name only public, stable callables: `typedmultidict.MultiDict` /
  `CIMultiDict`, `AllItemsView` / `AllValuesView`, and `operator.methodcaller` for the
  `keys()`, `items()` and `values()` views. Pickles written by 0.1.0 and 0.2.0 load.

## Errors

| Situation | Error |
| --- | --- |
| `md[k]`, `del md[k]`, `getone`, `popone`, `popall`, `pop` without default, key absent | `KeyError(k)` |
| `popitem()` on an empty multi-dict | `KeyError` |
| bulk element that is not iterable | `TypeError` naming its position and type |
| bulk element whose length is not 2 | `ValueError` naming its position and length |
| non-`str` key added to a `CIMultiDict` | `TypeError` naming the type |
| change during iteration (also between `iter()` and the first item) | `RuntimeError` |
| a key's `__eq__` or `__hash__` writes to the same multi-dict during a write (for `pop` and `setdefault`, the lookup they start with counts as part of it) | `RuntimeError`, nothing changed |

No message ever includes a value. `KeyError` for an absent key carries the key you
passed, like `dict`; messages about bulk input or keys name a position, a length or a
type (at most 40 characters of its name). The rest are fixed sentences.

## Cost

Every operation costs time in proportion to the pairs it reads or removes: lookups,
`in`, `len()` and `getone` take constant time whatever the size, and `add`, `popone` and
`popitem` amortised constant time (holes are swept in bulk); `getall`, `popall` and `del` are linear in the values of that one key; bulk calls are
linear in their input. Removed pairs leave holes that are swept out once they outnumber
the live pairs, so deleting every key one by one is linear overall.

A multi-dict is pure Python, so unlike a `dict` (whose single operations are atomic in
CPython) it is not thread-safe: share one between threads only behind a lock that covers
reads as well as writes. Without one, concurrent writes can raise `RuntimeError` and leave
the multi-dict inconsistent for good. Key comparisons run your code in the middle of
a write; reading the multi-dict from there is fine, writing to it raises `RuntimeError`.
Keys must keep the hash contract: a key whose hash or equality changes between calls
(or raises only sometimes) can leave a failed bulk write half undone, as it can corrupt
a `dict`.

## Compared with the references

`tests/fixtures/oracle_runs.json` holds 900 seeded scenarios run through the reference
implementations by `scripts/capture_oracles.py` (multidict 7.1.0 and its pure-Python
twin, Werkzeug 3.1.9, requests 2.34.2, CPython 3.13.2). The suite replays each one on
typedmultidict and requires the same answer to every call and the same state after it;
with `TYPEDMULTIDICT_LIVE_ORACLES=1` it also runs the installed references on fresh
scenarios. Each reference is driven only through the calls whose meaning it shares:

| Reference | Agrees on |
| --- | --- |
| `multidict.MultiDict`, `CIMultiDict` (C and pure Python) | `add`, `md[k] = v`, `getone`, `getall` (with a default), `popone`, `popall`, `popitem`, `setdefault`, `in`, `extend`, `update`, `merge`, pair order and spellings |
| `werkzeug.datastructures.MultiDict` | `add`, `md[k] = v`, `get`, `getlist`, `pop`, `poplist`, `setdefault`, `in`, `update` (as our `extend`), keys and values per key |
| `werkzeug.datastructures.Headers` | `add`, `set`, `get`, `getlist`, `pop`, `popitem` (when not empty), `remove`, `setdefault`, `in`, `extend`, pair order and spellings |
| `requests.structures.CaseInsensitiveDict` | `md[k] = v`, `get`, `pop`, `setdefault`, `in`, key spelling and order |
| `email.message.Message` | appending (its `msg[k] = v`), `get`, `get_all`, deleting a name, `in`, pair order |
| `wsgiref.headers.Headers` | `add_header`, `get`, `get_all`, deleting a name, `setdefault`, `in`, pair order |
| `http.client.parse_headers` | parsed field lines read through `CIMultiDict` exactly as through its message |

The deliberate differences, each shown live by `tests/test_reference_differences.py` and
`tests/test_reference_differences_more.py`:

| Reference | Theirs | Ours |
| --- | --- | --- |
| multidict | `len()` counts pairs; `items()` and `values()` repeat keys | `len()` counts keys; mapping views show first values |
| multidict | `getall(missing)` raises `KeyError` | returns `[]` (a default works in both) |
| multidict | `pop` is `popone` | `pop` removes every value, as `MutableMapping.pop` does |
| Werkzeug `MultiDict` | `update` appends; `popitem` removes a whole key | `update` replaces; `popitem` removes the last pair |
| Werkzeug `Headers` | `update` with a list keeps the last value of each name | keeps every incoming value |
| `email.message` | `msg[k] = v` appends; deleting a missing name is silent | `md[k] = v` replaces; `del` raises `KeyError` |
| `wsgiref.headers` | assignment moves the name to the end; deleting a missing name is silent | assignment keeps the place of the first pair; `del` raises `KeyError` |
| requests | one value per name | every value is kept |
| multidict | `MultiDict` refuses non-`str` keys | any hashable key; only `CIMultiDict` needs `str` |
| multidict `CIMultiDict` | `get`, `getall` and `[]` with a non-`str` name raise `TypeError` (`in` says `False`) | the name is simply absent |
| Werkzeug `Headers`, requests, `email`, `wsgiref` | even `in` with a non-`str` name raises | `in` says `False` |
| Werkzeug `Headers`, `email`, `wsgiref` | `len()` counts field lines | `len()` counts names |
| Werkzeug `Headers` | `popitem()` when empty raises `IndexError`; values become `str` | `KeyError`; values are stored as given |
| `email.message` | `get_all(missing)` is `None` | `getall(missing)` is `[]` |
| multidict | a plain and a case-insensitive multi-dict differing only in key case are equal only when the plain one's keys are already lower case (only the case-insensitive side is folded) | equal after folding string keys on both sides |
| Werkzeug `Headers` | deleting a missing name is silent | `del` raises `KeyError` |
| multidict (C extension) | bulk input other than a multi-dict is read through `items()` or by iterating it, never through `keys()` | an object with only `keys()` and `[]` is read like `dict.update` reads it |
| multidict (pure-Python fallback) | anything with `keys()` is read through `keys()` and `[]`, so a header object repeats the first value of a repeated name | read through `items()` first: every field is kept |

The cited documentation (RFC 9110, the `collections.abc`, `email` and `wsgiref` pages,
the multidict and Werkzeug docs, requests' `structures.py` at 2.34.2) is fetched by
`scripts/fetch_sources.py` into a git-ignored folder; `tests/sources/MANIFEST.json`
records each URL, date, size, SHA-256 and licence, and `tests/test_sources.py` finds every
fact quoted above in those copies.
