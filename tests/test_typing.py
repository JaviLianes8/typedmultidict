"""mypy --strict infers the documented generic types and rejects wrong ones."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

SRC = Path(__file__).resolve().parents[1] / "src"

# Line numbers matter: the tests below refer to them.
SNIPPET = """
from typedmultidict import CIMultiDict, MultiDict
md = MultiDict([("a", 1)])
reveal_type(md)
reveal_type(md.getone("a"))
reveal_type(md.getone("a", None))
reveal_type(md.getall("a"))
reveal_type(md.popone("a", "x"))
reveal_type(md.popall("a", None))
reveal_type(md.to_dict())
reveal_type(md.copy())
reveal_type(list(md.allitems()))
reveal_type(list(md.allvalues()))
ci: CIMultiDict[bytes] = CIMultiDict()
reveal_type(ci.copy())
reveal_type(ci.popitem())
reveal_type(ci.get("a"))
md.update(b=2)
ci.update([("a", b"x")], b=b"y")
md.add("a", "x")
md.add(1, 2)
ci.add(1, b"")
MultiDict[list[int], int]()
MultiDict[int, int]().update(x=1)
md.extend([("a", "b")])
ci.update(b=1)
reveal_type(md["a"])
reveal_type(md.get("a", 0))
reveal_type(md.get("a", "x"))
reveal_type(md.pop("a"))
reveal_type(md.pop("a", None))
reveal_type(md.setdefault("a", 1))
reveal_type(md.getall("a", None))
reveal_type(md.popone("a"))
reveal_type(md.popall("a"))
reveal_type(md.keys())
reveal_type(md.items())
reveal_type(md.values())
reveal_type(md.allitems())
reveal_type(md.allvalues())
reveal_type(next(iter(md)))
reveal_type(md.popitem())
reveal_type(ci.get("a", b""))
reveal_type(ci.setdefault("a", b""))
reveal_type(ci["a"])
reveal_type(md.pop("a", 0))
reveal_type(MultiDict(a=1))
reveal_type(CIMultiDict([("a", b"")], b=b""))
md.extend(c=3)
md.merge([("a", 1)], d=4)
MultiDict[int, int]().extend(x=1)
bad: MultiDict[int, int] = MultiDict(x=1)
"""

# Lines 27 onwards: what every other public method returns, with and without a default.
MORE_REVEALED = {
    27: "int",
    28: "int",
    29: "int | str",
    30: "int",
    31: "int | None",
    32: "int",
    33: "list[int] | None",
    34: "int",
    35: "list[int]",
    36: "typing.KeysView[str]",
    37: "typing.ItemsView[str, int]",
    38: "typing.ValuesView[int]",
    39: "typedmultidict._views.AllItemsView[str, int]",
    40: "typedmultidict._views.AllValuesView[int]",
    41: "str",
    42: "tuple[str, int]",
    43: "bytes",
    44: "bytes",
    45: "bytes",
    46: "int",
}


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    # A cold Windows venv once raised FileNotFoundError from the cache: the folder exists
    # before mypy starts, and no earlier cache is read.
    cache = folder / "cache"
    cache.mkdir()
    args = ["--strict", "--no-incremental", "--config-file", str(config), "--cache-dir"]
    out, err, _ = api.run([*args, str(cache), str(target)])
    return str(out) + str(err)


def test_construction_infers_both_parameters(mypy_output: str) -> None:
    assert _revealed(mypy_output, 4) == "typedmultidict._multidict.MultiDict[str, int]"


def test_reads_carry_the_value_type_and_defaults(mypy_output: str) -> None:
    assert _revealed(mypy_output, 5) == "int"
    assert _revealed(mypy_output, 6) == "int | None"
    assert _revealed(mypy_output, 7) == "list[int]"
    assert _revealed(mypy_output, 8) == "int | str"
    assert _revealed(mypy_output, 9) == "list[int] | None"
    assert _revealed(mypy_output, 10) == "dict[str, list[int]]"
    assert _revealed(mypy_output, 12) == "list[tuple[str, int]]"
    assert _revealed(mypy_output, 13) == "list[int]"


def test_copy_keeps_the_exact_class(mypy_output: str) -> None:
    assert _revealed(mypy_output, 11) == "typedmultidict._multidict.MultiDict[str, int]"
    assert _revealed(mypy_output, 15) == "typedmultidict._cimultidict.CIMultiDict[bytes]"


def test_case_insensitive_keys_are_str(mypy_output: str) -> None:
    assert _revealed(mypy_output, 16) == "tuple[str, bytes]"
    assert _revealed(mypy_output, 17) == "bytes | None"


def test_keyword_update_is_accepted_for_string_keys(mypy_output: str) -> None:
    for line in (18, 19):
        assert not re.search(rf"snippet\.py:{line}: error", mypy_output), mypy_output


def test_wrong_types_are_rejected(mypy_output: str) -> None:
    for line in range(20, 27):
        assert re.search(rf"snippet\.py:{line}: error", mypy_output), (line, mypy_output)


def test_unhashable_key_types_are_rejected_by_the_bound(mypy_output: str) -> None:
    assert re.search(r"snippet\.py:23: error: .*\[type-var\]", mypy_output), mypy_output


def test_every_other_public_method_carries_its_types(mypy_output: str) -> None:
    for line, expected in MORE_REVEALED.items():
        assert _revealed(mypy_output, line) == expected, line


def test_keyword_pairs_build_and_extend_string_keyed_multi_dicts(mypy_output: str) -> None:
    assert _revealed(mypy_output, 47) == "typedmultidict._multidict.MultiDict[str, int]"
    assert _revealed(mypy_output, 48) == "typedmultidict._cimultidict.CIMultiDict[bytes]"
    for line in (51, 52):
        assert re.search(rf"snippet\.py:{line}: error", mypy_output), (line, mypy_output)


def test_no_other_line_has_an_error(mypy_output: str) -> None:
    lines = {int(n) for n in re.findall(r"snippet\.py:(\d+): error", mypy_output)}
    assert lines == set(range(20, 27)) | {51, 52}


def _revealed(output: str, line: int) -> str:
    match = re.search(rf"snippet\.py:{line}: note: Revealed type is \"(.+)\"", output)
    assert match, output
    # Older mypy releases spell builtins with their module prefix and a trailing star.
    return match.group(1).replace("builtins.", "").replace("*", "")
