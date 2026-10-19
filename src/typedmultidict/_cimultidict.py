"""Case-insensitive multi-value mapping for HTTP-style string keys."""

from __future__ import annotations

from collections.abc import Hashable
from typing import ClassVar, TypeVar

from ._multidict import MultiDict
from ._pairs import is_str, type_name

V = TypeVar("V")

# Never equal to a stored token, so a key of the wrong type is simply absent on lookup.
_NO_MATCH = object()


class CIMultiDict(MultiDict[str, V]):
    """Keys compare case-insensitively (``str.lower``); each pair keeps its own spelling.

    Keys must be ``str`` (or a subclass): adding any other key raises ``TypeError``, while
    looking one up simply finds nothing. Keys are listed in the spelling of their first pair.

    >>> from typedmultidict import CIMultiDict
    >>> headers = CIMultiDict([("Set-Cookie", "a=1"), ("set-cookie", "b=2")])
    >>> headers["SET-COOKIE"], headers.getall("Set-Cookie"), list(headers)
    ('a=1', ['a=1', 'b=2'], ['Set-Cookie'])
    >>> 1 in headers, headers == {"set-cookie": "a=1"}
    (False, False)
    """

    _folds_case: ClassVar[bool] = True

    def _token(self, key: str) -> Hashable:
        if not is_str(key):
            raise TypeError(f"{type_name(self)} keys must be str, not {type_name(key)}")
        return str.lower(key)

    def _probe(self, key: object) -> Hashable:
        return str.lower(key) if is_str(key) else _NO_MATCH
