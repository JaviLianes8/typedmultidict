# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/typedmultidict/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. The default suite needs no network; only the
  opt-in end-to-end test reaches PyPI.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- Set `TYPEDMULTIDICT_E2E=1` to also build the wheel and sdist, install them in fresh
  venvs, upgrade from the PyPI release and type-check a consumer against the install.
- `multidict`, `werkzeug` and `requests` are dev dependencies used only as reference
  implementations in the tests; the library never imports them. After changing
  behaviour they share, refresh `tests/fixtures/oracle_runs.json` with
  `python scripts/capture_oracles.py`; set `TYPEDMULTIDICT_LIVE_ORACLES=1` to also run
  the installed references on fresh scenarios.
- `python scripts/fetch_sources.py` fetches the specifications the guide cites into the
  git-ignored `tests/sources/`, so `tests/test_sources.py` can check them.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
