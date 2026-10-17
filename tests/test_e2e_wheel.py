"""Build the wheel and sdist, install them in throwaway venvs and use them from outside.

Slow and needs the build backend and network (the upgrade starts from PyPI 0.2.0), so it
runs only with TYPEDMULTIDICT_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
E2E = Path(__file__).with_name("e2e_programs")

pytestmark = pytest.mark.skipif(
    os.environ.get("TYPEDMULTIDICT_E2E") != "1",
    reason="set TYPEDMULTIDICT_E2E=1 to build, install and upgrade",
)


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    # The Windows venv launcher variable would make a child report the wrong interpreter.
    env = {k: v for k, v in os.environ.items() if k != "__PYVENV_LAUNCHER__"}
    return subprocess.run(
        [str(c) for c in cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
        env=env,
    )


def _venv(path: Path) -> Path:
    venv.create(path, with_pip=True)
    return path / ("Scripts" if sys.platform == "win32" else "bin") / "python"


def _program(python: Path, name: str, work: Path, *args: str) -> str:
    # Run from an empty folder so the source tree cannot shadow the install.
    result = _run(python, "-I", E2E / name, *args, cwd=work)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    if not (ROOT / "src" / "typedmultidict" / "__init__.py").exists():
        pytest.fail("no source tree to build from")
    built = _run(sys.executable, "-m", "build", "--outdir", out, ROOT)
    assert built.returncode == 0, built.stderr
    return out


def test_archives_hold_exactly_what_should_ship(dist: Path) -> None:
    (wheel,) = dist.glob("typedmultidict-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert "typedmultidict/py.typed" in names
    assert any(n.endswith("licenses/LICENSE") for n in names)
    assert all(n.startswith(("typedmultidict/", "typedmultidict-")) for n in names), names
    (sdist,) = dist.glob("typedmultidict-*.tar.gz")
    with tarfile.open(sdist) as archive:
        members = [m.split("/", 1)[1] for m in archive.getnames() if "/" in m]
    assert "LICENSE" in members and "src/typedmultidict/py.typed" in members
    assert "tests/sources/MANIFEST.json" in members
    unwanted = ("IMPROVEMENTS", "CERT-1.0", ".pyc", "tests/sources/rfc", ".hypothesis")
    assert not [m for m in members if any(u in m for u in unwanted)]


def test_installed_wheel_end_to_end(dist: Path, tmp_path: Path) -> None:
    (wheel,) = dist.glob("typedmultidict-*.whl")
    python = _venv(tmp_path / "venv")
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr
    work = tmp_path / "work"
    work.mkdir()
    assert _program(python, "consumer.py", work) == "e2e ok"


def test_sdist_installs_and_works(dist: Path, tmp_path: Path) -> None:
    (sdist,) = dist.glob("typedmultidict-*.tar.gz")
    python = _venv(tmp_path / "venv")
    installed = _run(python, "-m", "pip", "install", "-q", sdist)
    assert installed.returncode == 0, installed.stderr
    work = tmp_path / "work"
    work.mkdir()
    assert _program(python, "consumer.py", work) == "e2e ok"


def test_upgrade_from_the_pypi_release_keeps_working(dist: Path, tmp_path: Path) -> None:
    (wheel,) = dist.glob("typedmultidict-*.whl")
    python = _venv(tmp_path / "venv")
    old = _run(python, "-m", "pip", "install", "-q", "--no-cache-dir", "typedmultidict==0.2.0")
    assert old.returncode == 0, old.stderr
    work = tmp_path / "work"
    work.mkdir()
    stored = work / "old.pickle"
    assert _program(python, "upgrade.py", work, "0.2.0", str(stored)) == "0.2.0 ok"
    new = _run(python, "-m", "pip", "install", "-q", "--upgrade", wheel)
    assert new.returncode == 0, new.stderr
    assert _program(python, "upgrade.py", work, "1.0.0", str(stored)) == "1.0.0 ok"


def test_a_strict_typed_consumer_checks_against_the_installed_wheel(
    dist: Path, tmp_path: Path
) -> None:
    pytest.importorskip("mypy")
    (wheel,) = dist.glob("typedmultidict-*.whl")
    python = _venv(tmp_path / "venv")
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr
    work = tmp_path / "work"
    work.mkdir()
    checked = _run(
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "--no-incremental",
        f"--python-executable={python}",
        E2E / "typed_consumer.py",
        cwd=work,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert _program(python, "typed_consumer.py", work) == "typed ok"
