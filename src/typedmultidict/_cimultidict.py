"""Case-insensitive multi-value mapping for HTTP-style string keys."""

from __future__ import annotations

from collections.abc import Hashable
from typing import ClassVar, TypeVar

from ._multidict import MultiDict

V = TypeVar("V")

# Never equal to a stored token, so a key of the wrong type is simply absent on lookup.
_NO_MATCH = object()


class CIMultiDict(MultiDict[str, V]):
    """Keys compare case-insensitively (``str.lower``); each pair keeps its own spelling.

    Keys must be ``str`` (or a subclass): adding any other key raises ``TypeError``, while
    looking one up simply finds nothing.
    """

    __slots__ = ()

    _folds_case: ClassVar[bool] = True

    def _token(self, key: str) -> Hashable:
        if not isinstance(key, str):
            raise TypeError(f"{type(self).__name__} keys must be str, not {type(key).__name__}")
        return str.lower(key)

    def _probe(self, key: object) -> Hashable:
        return str.lower(key) if isinstance(key, str) else _NO_MATCH
