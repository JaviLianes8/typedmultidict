# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release.
- `MultiDict[K, V]`: typed, insertion-ordered multi-value mapping implementing
  `MutableMapping`, with `add`, `getone`, `getall`, `popall`, `extend` and `allitems`.
- `CIMultiDict[V]`: case-insensitive string-keyed variant that preserves the original
  casing of each key.
- Pure Python, zero runtime dependencies, `py.typed`, `mypy --strict` clean. Unlike the
  C-extension `multidict`, it needs no build step.
