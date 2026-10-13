"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with TYPEDMULTIDICT_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("TYPEDMULTIDICT_E2E") != "1",
    reason="set TYPEDMULTIDICT_E2E=1 to build and install",
)

PROGRAM = r"""
import copy, importlib.metadata, importlib.resources, pickle, sys
import typedmultidict
from typedmultidict import CIMultiDict, MultiDict

assert "site-packages" in typedmultidict.__file__, typedmultidict.__file__
assert importlib.metadata.version("typedmultidict") == typedmultidict.__version__
assert importlib.resources.files("typedmultidict").joinpath("py.typed").is_file()
assert importlib.metadata.requires("typedmultidict") is None or all(
    "extra ==" in r for r in importlib.metadata.requires("typedmultidict")
)

md = MultiDict([("a", 1), ("b", 2), ("a", 3)])
md.update([("a", 7), ("c", 5), ("a", 8)])
assert list(md.allitems()) == [("a", 7), ("b", 2), ("a", 8), ("c", 5)]
assert md.popone("a") == 7 and md.popall("a") == [8] and md.popitem() == ("c", 5)
md.extend(md)
assert md.to_dict() == {"b": [2, 2]}
try:
    md.extend([("x", 1), (2,)])
except ValueError:
    pass
else:
    raise AssertionError("bad pair accepted")
assert len(md.allitems()) == 2

headers = CIMultiDict([("Set-Cookie", "a"), ("set-cookie", "b")])
assert headers.getall("SET-COOKIE") == ["a", "b"] and 5 not in headers
try:
    for key in headers:
        headers.add("X", "1")
except RuntimeError:
    pass
else:
    raise AssertionError("mutation during iteration not detected")
twin = pickle.loads(pickle.dumps(headers))
assert type(twin) is CIMultiDict and twin == headers and copy.deepcopy(twin) == twin
assert not any(name in sys.modules for name in ("multidict", "werkzeug", "hypothesis"))
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("typedmultidict-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert "typedmultidict/py.typed" in names
    assert not [n for n in names if n.startswith("tests/") or "IMPROVEMENTS" in n]

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"
