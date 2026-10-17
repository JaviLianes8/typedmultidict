"""Each fact the guide cites is located in the fetched copy of its source.

Copies come from ``scripts/fetch_sources.py`` into the git-ignored tests/sources/; the
tracked MANIFEST.json holds URL, fetch date, size, SHA-256 and licence. Without the
copies these tests skip. The phrases below are short quotations used only as locators.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pytest

SOURCES = Path(__file__).parent / "sources"
MANIFEST = json.loads((SOURCES / "MANIFEST.json").read_text(encoding="utf-8"))

FACTS = {
    # RFC 9110 section 5.1 and 5.3: names compare without case; same-name order matters.
    "rfc9110.txt": [
        "Field names are case-insensitive",
        "The order in which field lines with the same name are received is",
        "proxy MUST NOT change the order of these field line values",
    ],
    # The Mapping and MutableMapping mixin methods the classes provide.
    "collections-abc.html": [
        "__contains__, keys, items, values, get, __eq__, and __ne__",
        "pop, popitem, clear, update, and setdefault",
    ],
    "email-compat32-message.html": [
        "No exception is raised if the named field",
        "does not overwrite or delete any existing header with the same name",
        "Replace the first header found in the message that matches",
    ],
    "wsgiref.html": ["Setting a header deletes any existing values for that header"],
    "multidict.html": [
        "An alias to popone()",
        "Replace all items where key is equal to key with single item",
        "uses an internal lower-cased identity",
    ],
    "werkzeug-datastructures.html": ["extends rather than replaces existing key lists"],
    "requests-structures.py.txt": ["self._store[key.lower()] = (key, value)"],
}


def _text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".html":
        raw = html.unescape(re.sub(r"<[^>]+>", "", raw))
    return re.sub(r"\s+", " ", raw)


def test_every_source_is_in_the_manifest_with_its_provenance() -> None:
    assert set(MANIFEST) == set(FACTS)
    for entry in MANIFEST.values():
        assert entry["url"].startswith("https://")
        assert {"fetched", "size", "sha256", "licence"} <= set(entry)


@pytest.mark.parametrize("name", sorted(FACTS))
def test_the_fetched_copy_holds_the_cited_facts(name: str) -> None:
    path = SOURCES / name
    if not path.exists():
        pytest.skip("run scripts/fetch_sources.py to fetch the copies")
    # Documentation sites rebuild their pages: a copy fetched later may differ in bytes
    # from the recorded one, and the cited facts must still be there.
    text = _text(path)
    for phrase in FACTS[name]:
        assert phrase in text, (name, phrase)
