"""Pure-Python typed ordered multi-value dictionary with a case-insensitive variant."""

from __future__ import annotations

from ._cimultidict import CIMultiDict
from ._multidict import MultiDict

__version__ = "0.2.0"

__all__ = ["CIMultiDict", "MultiDict"]
