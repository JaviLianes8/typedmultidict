"""One write at a time: a key comparison that writes to the same multi-dict is refused."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])

_REENTERED = "multi-dict written to while one of its writes was running"


def exclusive(method: F) -> F:
    """Run a writing method, refusing any write that starts before it ends.

    A key's ``__eq__`` or ``__hash__``, or the input being read, runs user code in the
    middle of a write; if that code writes to the same multi-dict, it gets ``RuntimeError``
    instead of corrupting it.
    """

    @functools.wraps(method)
    def run(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self._busy:
            raise RuntimeError(_REENTERED)
        self._busy = True
        try:
            return method(self, *args, **kwargs)
        finally:
            self._busy = False

    return cast(F, run)
