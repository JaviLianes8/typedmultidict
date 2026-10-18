"""Reading bulk input (mappings, multi-dicts, iterables of pairs) before anything changes."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import islice
from typing import TYPE_CHECKING, Any, TypeVar, Union

if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem

    from ._storage import _Storage

K = TypeVar("K")
V = TypeVar("V")

MultiDictInput = Union["SupportsKeysAndGetItem[K, V]", Iterable[tuple[K, V]]]

# Messages show at most this much of a type name, never the offending value itself.
_NAME_LIMIT = 40


def type_name(obj: object) -> str:
    """The name of ``obj``'s type as plain text, cut to a bounded length."""
    try:
        name: object = type(obj).__name__
    except Exception:
        name = None
    text = str.__str__(name) if isinstance(name, str) else "?"
    return text if len(text) <= _NAME_LIMIT else text[: _NAME_LIMIT - 3] + "..."


def read_pairs(source: Any, storage_type: type[_Storage[Any, Any]]) -> list[tuple[Any, Any]]:
    """Return every pair of ``source`` as a new list, validating each element first."""
    if isinstance(source, storage_type):
        return [(entry.key, entry.value) for entry in source._live()]
    items = getattr(source, "items", None)
    if callable(items):
        # Header objects (http.client, email, wsgiref, other multi-dicts) list every field
        # here, while keys() and [] would repeat the first value of a repeated name.
        source = items()
    elif hasattr(source, "keys"):
        # The same test dict.update uses: anything else with keys() is read as a mapping.
        return [(key, source[key]) for key in source.keys()]  # noqa: SIM118
    pairs: list[tuple[Any, Any]] = []
    for position, item in enumerate(source):
        try:
            # At most three items are read, so an endless or huge element cannot hang.
            pair = tuple(islice(item, 3))
        except TypeError:
            raise TypeError(
                f"element #{position} is not a (key, value) pair: {type_name(item)}"
            ) from None
        if len(pair) != 2:
            if type(item) in (tuple, list):
                length = str(len(item))
            else:
                length = str(len(pair)) if len(pair) < 3 else "3 or more"
            raise ValueError(f"element #{position} has length {length}; 2 is required")
        pairs.append(pair)
    return pairs
