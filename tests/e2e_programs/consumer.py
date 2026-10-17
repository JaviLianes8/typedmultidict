"""An outside program using the installed package; prints "e2e ok" when every check holds."""

from __future__ import annotations

import copy
import importlib.metadata
import importlib.resources
import pickle
import sys
from typing import Any

import typedmultidict
from typedmultidict import AllItemsView, AllValuesView, CIMultiDict, MultiDict

assert "site-packages" in (typedmultidict.__file__ or ""), typedmultidict.__file__
assert importlib.metadata.version("typedmultidict") == typedmultidict.__version__
assert importlib.resources.files("typedmultidict").joinpath("py.typed").is_file()
# No runtime dependency: every requirement belongs to the optional dev extra.
assert all("extra ==" in r for r in importlib.metadata.requires("typedmultidict") or [])
assert typedmultidict.__all__ == ["AllItemsView", "AllValuesView", "CIMultiDict", "MultiDict"]
meta = importlib.metadata.metadata("typedmultidict")
assert meta["Requires-Python"] == ">=3.10" and meta["License-Expression"] == "MIT"
assert "Development Status :: 5 - Production/Stable" in meta.get_all("Classifier")
assert meta["Description-Content-Type"] == "text/markdown"
urls = {u.split(", ", 1)[0]: u.split(", ", 1)[1] for u in meta.get_all("Project-URL")}
assert {"Homepage", "Source", "Issues", "Changelog"} <= set(urls)

md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
md.update([("a", 7), ("c", 5), ("a", 8)])
assert list(md.allitems()) == [("a", 7), ("b", 2), ("a", 8), ("c", 5)]
assert md.popone("a") == 7 and md.popall("a") == [8] and md.popitem() == ("c", 5)
md.extend(md)
assert md.to_dict() == {"b": [2, 2]}
assert md.getall("zz") == [] and md.getall("zz", None) is None
assert isinstance(md.allitems(), AllItemsView) and isinstance(md.allvalues(), AllValuesView)
bad: Any = [("x", 1), (2,)]
try:
    md.extend(bad)
except ValueError:
    pass
else:
    raise AssertionError("bad pair accepted")
assert len(md.allitems()) == 2

big = MultiDict((i, i) for i in range(50_000))
for i in range(50_000):
    del big[i]
assert not big and len(big.allitems()) == 0

headers = CIMultiDict([("Set-Cookie", "a"), ("set-cookie", "b")])
number: Any = 5
assert headers.getall("SET-COOKIE") == ["a", "b"] and number not in headers
try:
    for _key in headers:
        headers.add("X", "1")
except RuntimeError:
    pass
else:
    raise AssertionError("mutation during iteration not detected")
twin = pickle.loads(pickle.dumps(headers))
assert type(twin) is CIMultiDict and twin == headers and copy.deepcopy(twin) == twin
assert not any(name in sys.modules for name in ("multidict", "werkzeug", "hypothesis"))
print("e2e ok")
