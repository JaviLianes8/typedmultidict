"""Run by the installed release before and after an upgrade: same results, pickles carry over.

usage: python upgrade.py <expected-version> <pickle-path>
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import typedmultidict
from typedmultidict import CIMultiDict, MultiDict

version, stored = sys.argv[1], Path(sys.argv[2])
assert typedmultidict.__version__ == version, typedmultidict.__version__

md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
md.update([("a", 7), ("c", 5), ("a", 8)], b=0)
md.merge([("c", 0), ("d", 4)])
assert list(md.allitems()) == [("a", 7), ("b", 0), ("a", 8), ("c", 5), ("d", 4)]
assert md.getone("a") == 7 and md.getall("a") == [7, 8] and md.getall("x") == []
assert md.popone("a") == 7 and md.pop("a") == 8 and md.popitem() == ("d", 4)
assert md == {"b": 0, "c": 5} and len(md) == 2 and md.to_dict() == {"b": [0], "c": [5]}
headers = CIMultiDict([("Accept", "x"), ("ACCEPT", "y")])
headers["accept"] = "z"
assert list(headers.allitems()) == [("accept", "z")] and headers.setdefault("Via", "1") == "1"
assert repr(headers) == "CIMultiDict([('accept', 'z'), ('Via', '1')])"

if version == "0.2.0":
    stored.write_bytes(pickle.dumps((md, headers)))
else:
    old_md, old_headers = pickle.loads(stored.read_bytes())
    assert type(old_md) is MultiDict and old_md == md
    assert type(old_headers) is CIMultiDict and list(old_headers.allitems()) == list(
        headers.allitems()
    )
    old_headers.add("VIA", "2")
    assert old_headers.getall("via") == ["1", "2"]
print(f"{version} ok")
