"""Case-insensitive multi-value mapping for HTTP-style string keys."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TypeVar

from ._multidict import MultiDict

V = TypeVar("V")


class CIMultiDict(MultiDict[str, V]):
    """Keys compare case-insensitively; their original casing is kept in items()."""

    def _norm(self, key: str) -> Hashable:
        return key.lower()
