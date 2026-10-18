# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-19

The public API is now stable: `MultiDict`, `CIMultiDict`, `AllItemsView` and
`AllValuesView`, every method name, signature and default, the error types and the
behaviour described in the README and the guide. Later 1.x releases only add.

### Added

- `AllItemsView` and `AllValuesView` are exported, so the views returned by `allitems()`
  and `allvalues()` can be named in annotations.
- `getall(key, default)` returns `default` for an absent key, as in `multidict`;
  `getall(key)` still returns an empty list.
- Every public class and method carries a docstring with examples that the test suite
  runs.

### Changed (upgrading from 0.2.0)

- The constructor, `extend` and `merge` take keyword pairs for string keys, as `update`
  already did and as in `dict()` and `multidict`: `MultiDict([("a", 1)], b=2)`,
  `md.extend(c=3)`. Their source argument is positional only and optional, so
  `extend()` and `merge()` with no argument do nothing. `MultiDict(initial=x)` now stores
  one pair named `"initial"`, as `dict(initial=x)` does; pass the source positionally.
- `pop` and `setdefault` refuse, with `RuntimeError` and no change, a write that a key's
  `__eq__` or `__hash__` makes while they look the key up; before, that write went through.
  The lookup is `self[key]`, so a subclass `__getitem__` that writes to the multi-dict
  (to fill in a missing key, say) makes `pop` and `setdefault` raise `RuntimeError` too;
  `md[key]` alone still runs it.
- A keyword pair may be named `self`, as in `dict(self=1)`: `MultiDict(self=1)`,
  `extend`, `merge` and `update` store it; in 0.2.0 `update(self=1)` raised `TypeError`.
- `CIMultiDict` checks the real type of a key, so an object that only claims to be a
  `str` (a `Mock(spec=str)`, a proxy) is absent on lookup and refused with the documented
  `TypeError` on write, instead of failing inside `str.lower`.
- `keys()`, `items()` and `values()` views pickle as a call of that method on the
  multi-dict (`operator.methodcaller`), so a pickle never names a private module.
  Pickles of these views written by 0.2.0 still load.
- Removing pairs no longer scans the whole multi-dict: `del md[key]`, `pop`, `popone`,
  `popall`, assignment and `update` cost time in proportion to the pairs they remove.
  Deleting every key one by one is linear overall instead of quadratic.
- Bulk input reads at most three items of each element, so an endless or huge element
  fails at once with `ValueError` instead of hanging. The message gives the exact length
  of a tuple or list and says "3 or more" for other iterables.
- A source with an `items()` method is read through `items()`, as the `multidict` C
  extension reads it, so building from an `http.client.HTTPMessage`, an
  `email.message.Message`, a `wsgiref.headers.Headers` or another library's multi-dict
  keeps every field. 0.2.0 read such objects through `keys()` and `[]`, which repeated
  the first value of a repeated name. An object with only `keys()` and `[]` is still read
  like `dict.update` reads it.
- Error messages show at most 40 characters of a type name, and never the offending value.
- The version has a single source (`typedmultidict.__version__`).
- A key whose `__eq__` or `__hash__` writes to the same multi-dict in the middle of a write
  now gets `RuntimeError` and the multi-dict is left unchanged; before, the internal index
  could silently go out of step.
- `keys()`, `items()` and `values()` iterators raise `RuntimeError` for a change made
  between `iter()` and the first item, as `iter(md)` and `dict` views do.
- `repr` of a view held inside its own multi-dict prints `...` instead of recursing.
- Every view pickles at every protocol (`allitems()` and `allvalues()` failed at protocols
  0 and 1, and on Python 3.10 `keys()`, `items()` and `values()` came back broken).
- `get`, `pop`, `setdefault`, `keys`, `items`, `values` and `clear` are now written out on
  the class with their own docstrings. They behave as the `collections.abc` mixins did,
  and `get`, `pop` and `setdefault` still go through `__getitem__`, `__setitem__` and
  `__delitem__`, so a subclass that overrides those hooks sees the same calls as before.

## [0.2.0] - 2026-10-13

### Added

- `getone(key, default)`, `popone(key[, default])`, `merge(other)`, `to_dict()` and
  `copy()`.
- `allitems()` and `allvalues()` return live, sized views of every pair or value.
- `update` accepts keyword arguments for string keys, like `MutableMapping.update`.

### Changed

- Lookups, `in`, `len()` and adding no longer scan every pair: an index keeps them
  constant time whatever the size.
- `update` replaces the values of each incoming key in place instead of keeping only the
  first value of a multi-dict source, and `popitem` removes only the last pair.
- `popall(key, default)` accepts a default of any type.
- Bulk input is checked in full before anything changes: `md.extend(md)` no longer hangs,
  and a malformed element raises `TypeError` or `ValueError` with its position.
- Changing a multi-dict while iterating over it or its views raises `RuntimeError`.
- Comparing with a plain mapping is equal only when every key has exactly one value, and
  a plain and a case-insensitive multi-dict compare with case folded.
- Pickles hold plain pairs and name the classes by their public path
  (`typedmultidict.MultiDict`); pickles written by 0.1.0 still load. Copies and pickles
  of subclasses keep their attributes and slots, and a multi-dict may contain itself.
- `CIMultiDict` raises `TypeError` for a non-`str` key on write and treats it as absent on
  read, instead of failing with `AttributeError`.

## [0.1.0]

- First release.
- `MultiDict[K, V]`: typed, insertion-ordered multi-value mapping implementing
  `MutableMapping`, with `add`, `getone`, `getall`, `popall`, `extend` and `allitems`.
- `CIMultiDict[V]`: case-insensitive string-keyed variant that preserves the original
  casing of each key.
- Pure Python, zero runtime dependencies, `py.typed`, `mypy --strict` clean. Unlike the
  C-extension `multidict`, it needs no build step.
