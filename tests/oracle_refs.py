"""Seeded scenarios driven through established multi-value mappings, and through ours.

Each reference gets only the operations whose meaning it shares with typedmultidict; the
documented differences (``len()``, ``pop``, Werkzeug's ``update``, ...) are left out here
and pinned in ``test_reference_differences.py``. ``scripts/capture_oracles.py`` runs the
references and stores their answers; ``test_reference_runs.py`` replays them on ours.
"""

from __future__ import annotations

import random
from typing import Any

MISSING = "<missing>"
PLAIN_KEYS = ["a", "b", "c", "A", "content-type"]
CASE_KEYS = ["Accept", "accept", "ACCEPT", "Set-Cookie", "set-cookie", "X-Id", "x-id"]
# Non-ASCII spellings on which every case-insensitive reference agrees with str.lower.
UNICODE_KEYS = ["Straße", "STRAßE", "K", "k", "ǅ", "ǆ", "İ", "i"]  # noqa: RUF001

# Operation name -> what typedmultidict does for it; the reference adapters below mirror it.
OURS: dict[str, Any] = {
    "add": lambda md, k, v: md.add(k, v),
    "set": lambda md, k, v: md.__setitem__(k, v),
    "delete": lambda md, k: md.popall(k, MISSING),
    "pop": lambda md, k: md.pop(k, MISSING),
    "first": lambda md, k: md.getone(k, MISSING),
    "all": lambda md, k: md.getall(k),
    "popfirst": lambda md, k: md.popone(k, MISSING),
    "poplast": lambda md: md.popitem() if md else MISSING,
    "setdefault": lambda md, k, v: md.setdefault(k, v),
    "has": lambda md, k: k in md,
    "extend": lambda md, pairs: md.extend(pairs),
    "update": lambda md, pairs: md.update(pairs),
    "merge": lambda md, pairs: md.merge(pairs),
}


def _multidict_ops(module: Any) -> dict[str, Any]:
    def poplast(md: Any) -> Any:
        return md.popitem() if md else MISSING

    return {
        "add": lambda md, k, v: md.add(k, v),
        "set": lambda md, k, v: md.__setitem__(k, v),
        "delete": lambda md, k: md.popall(k, MISSING),
        "first": lambda md, k: md.getone(k, MISSING),
        "all": lambda md, k: md.getall(k, []),
        "popfirst": lambda md, k: md.popone(k, MISSING),
        "poplast": poplast,
        "setdefault": lambda md, k, v: md.setdefault(k, v),
        "has": lambda md, k: k in md,
        "extend": lambda md, pairs: md.extend(pairs),
        "update": lambda md, pairs: md.update(pairs),
        "merge": lambda md, pairs: md.merge(pairs),
    }


def _drain(get_all: Any, remove: Any) -> Any:
    values = list(get_all() or [])
    remove()
    return values or MISSING


def _headers_ops() -> dict[str, Any]:
    return {
        "add": lambda h, k, v: h.add(k, v),
        "set": lambda h, k, v: h.set(k, v),
        "delete": lambda h, k: _drain(lambda: h.getlist(k), lambda: h.remove(k)),
        "pop": lambda h, k: h.pop(k, MISSING),
        "first": lambda h, k: h.get(k, MISSING),
        "all": lambda h, k: h.getlist(k),
        "poplast": lambda h: h.popitem() if h else MISSING,
        "setdefault": lambda h, k, v: h.setdefault(k, v),
        "has": lambda h, k: k in h,
        "extend": lambda h, pairs: h.extend(pairs),
    }


def _werkzeug_multidict_ops() -> dict[str, Any]:
    return {
        "add": lambda md, k, v: md.add(k, v),
        "set": lambda md, k, v: md.__setitem__(k, v),
        "delete": lambda md, k: md.poplist(k) or MISSING,
        "pop": lambda md, k: md.pop(k, MISSING),
        "first": lambda md, k: md.get(k, MISSING),
        "all": lambda md, k: md.getlist(k),
        "setdefault": lambda md, k, v: md.setdefault(k, v),
        "has": lambda md, k: k in md,
        "extend": lambda md, pairs: md.update(pairs),  # Werkzeug's update appends
    }


def _email_ops() -> dict[str, Any]:
    return {
        "add": lambda m, k, v: m.__setitem__(k, v),  # email's item assignment appends
        "delete": lambda m, k: _drain(lambda: m.get_all(k), lambda: m.__delitem__(k)),
        "first": lambda m, k: m.get(k, MISSING),
        "all": lambda m, k: m.get_all(k, []),
        "has": lambda m, k: k in m,
    }


def _wsgiref_ops() -> dict[str, Any]:
    return {
        "add": lambda h, k, v: h.add_header(k, v),
        "delete": lambda h, k: _drain(lambda: h.get_all(k), lambda: h.__delitem__(k)),
        "first": lambda h, k: h.get(k, MISSING),
        "all": lambda h, k: h.get_all(k),
        "setdefault": lambda h, k, v: h.setdefault(k, v),
        "has": lambda h, k: k in h,
    }


def _requests_ops() -> dict[str, Any]:
    return {
        "set": lambda d, k, v: d.__setitem__(k, v),
        "pop": lambda d, k: d.pop(k, MISSING),
        "first": lambda d, k: d.get(k, MISSING),
        "setdefault": lambda d, k, v: d.setdefault(k, v),
        "has": lambda d, k: k in d,
    }


def references() -> dict[str, tuple[bool, list[str], Any, dict[str, Any]]]:
    """name -> (case-insensitive, key pool, factory, operations); missing packages skipped."""
    import email.message
    import wsgiref.headers

    refs: dict[str, tuple[bool, list[str], Any, dict[str, Any]]] = {}
    case = CASE_KEYS + UNICODE_KEYS
    try:
        import multidict
        import multidict._multidict_py as pure

        refs["multidict"] = (False, PLAIN_KEYS, multidict.MultiDict, _multidict_ops(multidict))
        refs["multidict-ci"] = (True, case, multidict.CIMultiDict, _multidict_ops(multidict))
        refs["multidict-py"] = (False, PLAIN_KEYS, pure.MultiDict, _multidict_ops(pure))
        refs["multidict-py-ci"] = (True, case, pure.CIMultiDict, _multidict_ops(pure))
    except ImportError:
        pass
    try:
        from werkzeug.datastructures import Headers
        from werkzeug.datastructures import MultiDict as WerkzeugMultiDict

        refs["werkzeug-multidict"] = (
            False, PLAIN_KEYS, WerkzeugMultiDict, _werkzeug_multidict_ops()
        )  # fmt: skip
        refs["werkzeug-headers"] = (True, case, Headers, _headers_ops())
    except ImportError:
        pass
    try:
        from requests.structures import CaseInsensitiveDict

        refs["requests"] = (True, case, CaseInsensitiveDict, _requests_ops())
    except ImportError:
        pass

    # email and wsgiref check names against RFC 5322 on newer Pythons: ASCII names only.
    def message(pairs: list[tuple[str, str]]) -> Any:
        return _filled_message(email.message, pairs)

    def wsgi(pairs: list[tuple[str, str]]) -> Any:
        return wsgiref.headers.Headers(list(pairs))

    refs["email-message"] = (True, CASE_KEYS, message, _email_ops())
    refs["wsgiref-headers"] = (True, CASE_KEYS, wsgi, _wsgiref_ops())
    return refs


def _filled_message(module: Any, pairs: list[tuple[str, str]]) -> Any:
    message = module.Message()
    for key, value in pairs:
        message[key] = value
    return message


def scenario(rng: random.Random, keys: list[str], ops: list[str]) -> dict[str, Any]:
    """A random starting list of pairs and a random sequence of the given operations."""

    def pairs(most: int) -> list[list[str]]:
        return [[rng.choice(keys), str(rng.randrange(4))] for _ in range(rng.randrange(most))]

    steps: list[list[Any]] = []
    for _ in range(rng.randrange(1, 13)):
        name = rng.choice(ops)
        if name in ("add", "set", "setdefault"):
            steps.append([name, rng.choice(keys), str(rng.randrange(4))])
        elif name in ("extend", "update", "merge"):
            steps.append([name, pairs(5)])
        elif name == "poplast":
            steps.append([name])
        else:
            steps.append([name, rng.choice(keys)])
    # A single-valued reference starts empty: a list with repeated keys means nothing to it.
    return {"initial": pairs(6) if "add" in ops else [], "steps": steps}
