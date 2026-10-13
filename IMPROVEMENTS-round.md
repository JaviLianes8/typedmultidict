# typedmultidict improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Indexed storage: constant-time lookups, safe self-extend, atomic bulk input
- [x] Full multi-value API: defaults, `popone`, `merge`, multi-aware `update` and `popitem`, `to_dict`, `copy`
- [x] Live views over every pair, change detection during iteration
- [x] Equality, pickling and copying rules
- [x] Case-insensitive variant: strict key type, lookups by any object
- [x] Contracts: model-based property tests, oracle tests, typing proof, README examples, installed wheel e2e
- [ ] Mutation run proves the tests bite
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` stores every `(key, value)` pair in one list and scans it for every operation.
Reading it against the reference implementations and the abstract base class contracts:

- Every lookup, `in`, `len()` and assignment walks the whole list and normalises every key
  on the way, so a "dictionary" with 10 000 headers answers `md[key]` in linear time.
- `md.extend(md)` never returns: it reads the list it is appending to.
- `extend` and the constructor apply pairs one by one, so a malformed element halfway
  leaves a half-applied update, and the error is a bare unpacking message.
- `update`, `pop`, `popitem` and `setdefault` come from the `MutableMapping` mixins, which
  know nothing about repeated keys: `update` from a multi-dict keeps only first values and
  `popitem` throws away every value of a key to return one.
- `getone` has no default, `popall` is typed so a non-list default is rejected, there is
  no way to remove a single value, to merge only missing keys or to get `{key: [values]}`.
- `allitems()` is a one-shot generator; there is no sized, reusable view of the pairs.
- Mutating while iterating silently skips or repeats keys instead of failing.
- Pickling and copying work by accident (the private list is copied as is), so a
  refactor of the storage would break every stored pickle.
- `CIMultiDict` crashes with `AttributeError` on a non-string key, and compares unequal
  to a `MultiDict` holding the same lower-case keys depending on which side is spelled how.
- Tests cover single examples only; nothing checks the type against a model over random
  operation sequences, the generic types are not proven, and the README is not run.

## Sources (fetched 2026-10-13)

- https://multidict.aio-libs.org/en/stable/multidict/ (multidict 7.1.0 reference,
  sha256 a12898ef4d34d037f1ca8ab5dbe6b52c334f81b79098e6d995586074ef3be841).
  `d[key] = value` replaces every item for the key with one item; `popone` removes only
  the first value; `popall` removes all and returns them in order; `extend` appends,
  `merge` skips keys already present, `update` overwrites existing keys; keys are listed
  once in the spelling of their first item; `CIMultiDict` keys must be `str`.
- https://werkzeug.palletsprojects.com/en/stable/datastructures/ (Werkzeug 3.1,
  sha256 f1823e00779370c24c4aeecbf7600142715e439ae59c685882e075494f6ba2fc).
  `MultiDict` behaves like a dict over the first value of each key (so `len()` counts
  keys); `getlist` returns an empty list for a missing key; `items(multi=True)` and
  `to_dict(flat=False)` expose every value.
- https://docs.python.org/3/library/collections.abc.html
  (sha256 df95d1c6877169350f29574cb8bf0e9bc682f96e970e860edf9220f0715cd7c5).
  `Mapping` needs `__getitem__`, `__iter__`, `__len__` and provides `__contains__`,
  `keys`, `items`, `values`, `get`, `__eq__`; `MutableMapping` adds `pop`, `popitem`,
  `clear`, `update`, `setdefault` on top of `__setitem__` and `__delitem__`.
- https://docs.python.org/3/library/typing.html
  (sha256 64cd3d994bf4888cab150b81b5becd0652bc82711063d5cca624a3f7159a10a8).
  User-defined generics, `TypeVar` bounds and `@overload` for defaults.
- https://docs.python.org/3/library/pickle.html
  (sha256 97e1bc16f9b439a03d6cd48be793d5f84870725ccfb0c3682979506f2a89bb1f) and
  https://docs.python.org/3/library/copy.html
  (sha256 90fd881e49942c5a0aee5cac1c5b98303941a19970ec08afbe9d06944f708728).
  `__reduce__` returns a callable, its arguments and a state that pickle and `copy`
  restore (a `(dict, slots)` pair sets both).
- https://docs.python.org/3/reference/datamodel.html
  (sha256 e114e1d0c47636fc9ccd1ba3d174cc8eaeadc3983371fabc8f5e052c53159d9f).
  A class that defines `__eq__` and sets `__hash__ = None` is unhashable.

Behaviour of `multidict` 7.1.0 and Werkzeug 3.1.9 for the cases above was also checked by
running them; both are used in the tests as optional oracles only.

## Ranked improvements

1. **Indexed storage.** Pairs stay in one insertion-ordered list, and an index maps each
   (normalised) key to its entries: `md[key]`, `in`, `len()`, `getone`, `getall` and
   adding are constant time (per value returned); removing stays linear. Bulk input is
   read and validated in full before anything changes, so `md.extend(md)` doubles the
   pairs and a bad element (wrong length, not iterable) raises with its position and
   leaves the mapping untouched.
2. **Full multi-value API, matching `multidict` where the names overlap.**
   `getone(key, default)`, `popone(key, default)` (first value only),
   `popall(key, default)` with any default type, `merge` (adds keys not present yet),
   `update` that replaces the values of each incoming key in place (old positions are
   reused, extra new values go to the end, extra old values are dropped), `popitem`
   that removes only the last pair, `to_dict()` (`{key: [values]}`), `copy()`.
   `pop`, `get`, `setdefault`, `keys`, `items` and `values` keep their `Mapping`
   meaning over the first value of each key, so `len(md) == len(md.keys())` and every
   `Mapping` consumer sees a consistent dictionary.
3. **Live views over every pair.** `allitems()` and `allvalues()` return reusable views
   that follow the mapping, with `len()` (number of pairs), `in` and iteration.
4. **Mutation during iteration fails.** Iterating keys, views or pairs while the mapping
   changes raises `RuntimeError`, as `dict` and `multidict` do, instead of skipping.
5. **Equality, pickling, copying.** Two multi-dicts are equal when they hold the same
   pairs in the same order (keys compared case-insensitively if either side is
   case-insensitive); against a plain mapping, equal when every key has exactly one value
   and the pairs match. Pickles store plain pairs, so the format survives storage
   changes; copies and pickles of subclasses keep their own attributes.
6. **Case-insensitive variant hardened.** Non-string keys raise `TypeError` on write and
   are simply absent on read (`5 in headers` is `False`), as in `multidict`.
7. **Contracts.** A Hypothesis state machine drives random operation sequences against a
   list-of-pairs model for both classes; differential tests against `multidict` and
   Werkzeug when installed; mypy proves the generic types and rejects wrong ones; the
   README examples run and print what they claim; the built wheel is installed in a
   fresh venv and exercised.
8. **Docs and packaging.** API table, behaviour differences from `multidict` spelled
   out, CHANGELOG, version 0.2.0, classifiers per supported Python version.

## Out of scope

- `len()` counting pairs as `multidict` does: it would break the `Mapping` contract
  (`len(md) != len(md.keys())`) that this library promises, and change 0.1.0 behaviour.
- Keyword arguments in the constructor and in `extend`/`merge`: they only make sense for
  string keys; `update` accepts them because `MutableMapping.update` does.
- Read-only proxies and an `istr` type: a later round if there is demand.
- Thread safety: like `dict` subclasses written in Python, concurrent writers need a lock.
