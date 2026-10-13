"""Pure-Python typed ordered multi-value dictionary with a case-insensitive variant."""

from __future__ import annotations

from ._cimultidict import CIMultiDict
from ._multidict import MultiDict

__version__ = "0.2.0"

# Pickles name a class by its module: point them at the public one, which never moves.
CIMultiDict.__module__ = __name__
MultiDict.__module__ = __name__

__all__ = ["CIMultiDict", "MultiDict"]
