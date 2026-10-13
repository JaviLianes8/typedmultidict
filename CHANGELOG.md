# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
  first value of a multi-dict source, and `popitem` removes only the last pair added.
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
