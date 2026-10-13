"""Reading bulk input (mappings, multi-dicts, iterables of pairs) before anything changes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeVar, Union

if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem

    from ._storage import _Storage

K = TypeVar("K")
V = TypeVar("V")

MultiDictInput = Union["SupportsKeysAndGetItem[K, V]", Iterable[tuple[K, V]]]


def read_pairs(source: Any, storage_type: type[_Storage[Any, Any]]) -> list[tuple[Any, Any]]:
    """Return every pair of ``source`` as a new list, validating each element first."""
    if isinstance(source, storage_type):
        return [(entry.key, entry.value) for entry in source._entries]
    if hasattr(source, "keys"):
        # The same test dict.update uses: anything with keys() is read as a mapping.
        return [(key, source[key]) for key in source.keys()]  # noqa: SIM118
    pairs: list[tuple[Any, Any]] = []
    for position, item in enumerate(source):
        try:
            pair = tuple(item)
        except TypeError:
            raise TypeError(
                f"element #{position} is not a (key, value) pair: {type(item).__name__}"
            ) from None
        if len(pair) != 2:
            raise ValueError(f"element #{position} has length {len(pair)}; 2 is required")
        pairs.append(pair)
    return pairs
