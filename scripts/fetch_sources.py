"""Fetch the specifications and reference documentation the guide cites.

usage: python scripts/fetch_sources.py [--record]

Copies land in tests/sources/ (git-ignored: third-party text is never committed). With
--record the tracked tests/sources/MANIFEST.json is rewritten with each copy's URL,
fetch date, size, SHA-256 and licence; without it the copies are checked against it.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "tests" / "sources"
MANIFEST = DEST / "MANIFEST.json"

SOURCES = {
    "rfc9110.txt": (
        "https://www.rfc-editor.org/rfc/rfc9110.txt",
        "IETF Trust, BCP 78 (Revised BSD for code components)",
    ),
    "collections-abc.html": (
        "https://docs.python.org/3.14/library/collections.abc.html",
        "PSF documentation licence",
    ),
    "email-compat32-message.html": (
        "https://docs.python.org/3.14/library/email.compat32-message.html",
        "PSF documentation licence",
    ),
    "wsgiref.html": (
        "https://docs.python.org/3.14/library/wsgiref.html",
        "PSF documentation licence",
    ),
    "multidict.html": (
        "https://multidict.aio-libs.org/en/stable/multidict/",
        "Apache-2.0 (aio-libs/multidict)",
    ),
    "werkzeug-datastructures.html": (
        "https://werkzeug.palletsprojects.com/en/stable/datastructures/",
        "BSD-3-Clause (pallets/werkzeug)",
    ),
    "requests-structures.py.txt": (
        "https://raw.githubusercontent.com/psf/requests/v2.34.2/src/requests/structures.py",
        "Apache-2.0 (psf/requests)",
    ),
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "typedmultidict-sources"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data: bytes = response.read()
    return data


def main() -> int:
    record = "--record" in sys.argv
    DEST.mkdir(parents=True, exist_ok=True)
    known = json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else {}
    today = datetime.date.today().isoformat()
    entries: dict[str, dict[str, object]] = {}
    for name, (url, licence) in SOURCES.items():
        data = fetch(url)
        (DEST / name).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        entries[name] = {
            "url": url,
            "fetched": today,
            "size": len(data),
            "sha256": digest,
            "licence": licence,
        }
        old = known.get(name, {}).get("sha256")
        status = "new" if old is None else "same" if old == digest else "CHANGED upstream"
        print(f"{name}: {len(data)} bytes, {status}")
    if record:
        MANIFEST.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
