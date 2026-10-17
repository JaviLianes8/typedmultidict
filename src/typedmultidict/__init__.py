"""Pure-Python typed ordered multi-value dictionary with a case-insensitive variant."""

from ._cimultidict import CIMultiDict
from ._multidict import MultiDict
from ._views import AllItemsView, AllValuesView

__version__ = "1.0.0"

# Pickles name a class by its module: point them at the public one, which never moves.
for _public in (AllItemsView, AllValuesView, CIMultiDict, MultiDict):
    _public.__module__ = __name__
del _public

__all__ = ["AllItemsView", "AllValuesView", "CIMultiDict", "MultiDict"]
