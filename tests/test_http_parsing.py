"""Headers parsed by the standard library read the same through CIMultiDict.

http.client.parse_headers is CPython's own HTTP/1.1 header parser; its HTTPMessage
(an email.message.Message) is the reference for name folding and repeated fields.
"""

from __future__ import annotations

import http.client
import io
import random

import pytest

from typedmultidict import CIMultiDict

NAMES = ["Accept", "Set-Cookie", "X-Request-Id", "Vary", "Cache-Control", "Via"]


def _spellings(name: str) -> list[str]:
    return [name, name.lower(), name.upper(), name.swapcase()]


def _raw(rng: random.Random) -> tuple[bytes, list[tuple[str, str]]]:
    lines = []
    for index in range(rng.randrange(0, 12)):
        lines.append((rng.choice(_spellings(rng.choice(NAMES))), f"v{index}"))
    raw = "".join(f"{name}: {value}\r\n" for name, value in lines) + "\r\n"
    return raw.encode("ascii"), lines


@pytest.mark.parametrize("seed", range(40))
def test_parsed_headers_agree_name_by_name(seed: int) -> None:
    raw, lines = _raw(random.Random(seed))
    message = http.client.parse_headers(io.BytesIO(raw))
    headers = CIMultiDict(message.items())
    assert list(headers.allitems()) == message.items() == lines
    for name in NAMES:
        for spelling in _spellings(name):
            assert headers.getall(spelling) == message.get_all(spelling, [])
            assert (spelling in headers) == (spelling in message)
            assert headers.get(spelling) == message.get(spelling)
    headers.popall("vary", None)
    del message["vary"]
    assert list(headers.allitems()) == message.items()
