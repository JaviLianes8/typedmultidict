"""Packaging metadata and the local gate and release scripts keep their promises."""

from __future__ import annotations

import importlib
import pickle
import re
import sys
from pathlib import Path
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _project() -> dict[str, Any]:
    if sys.version_info < (3, 11):
        pytest.skip("tomllib arrived in Python 3.11")
    tomllib = importlib.import_module("tomllib")
    data: dict[str, Any] = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    return data


def test_project_metadata_is_complete_and_stable() -> None:
    data = _project()
    project = data["project"]
    assert project["dynamic"] == ["version"] and project["dependencies"] == []
    assert project["requires-python"] == ">=3.10" and project["license"] == "MIT"
    assert project["readme"] == "README.md" and project["license-files"] == ["LICENSE"]
    assert project["keywords"] == [
        "multidict", "multi-value", "dictionary", "mapping", "headers", "http",
        "case-insensitive", "query-string", "typed",
    ]  # fmt: skip
    classifiers = project["classifiers"]
    assert "Development Status :: 5 - Production/Stable" in classifiers
    assert "Typing :: Typed" in classifiers
    versions = [c.rsplit(" ", 1)[1] for c in classifiers if re.fullmatch(r".*:: 3\.\d+", c)]
    assert versions == ["3.10", "3.11", "3.12", "3.13", "3.14"]
    base = "https://github.com/JaviLianes8/typedmultidict"
    assert project["urls"]["Source"] == base
    assert project["urls"]["Issues"] == base + "/issues"
    assert project["urls"]["Changelog"] == base + "/blob/main/CHANGELOG.md"
    assert project["urls"]["Homepage"].startswith("https://")
    assert "pytest-timeout" in project["optional-dependencies"]["dev"]
    assert data["tool"]["pytest"]["ini_options"]["timeout"] == 300


def test_the_sdist_takes_only_the_listed_paths() -> None:
    only = _project()["tool"]["hatch"]["build"]["targets"]["sdist"]["only-include"]
    assert only == [
        "src", "tests", "scripts", "README.md", "GUIDE.md", "CHANGELOG.md",
        "CONTRIBUTING.md", "LICENSE", "pyproject.toml", "requirements-dev.txt",
    ]  # fmt: skip


def test_the_gate_stops_on_every_failing_step() -> None:
    text = (SCRIPTS / "check.ps1").read_text("utf-8")
    assert "exit $LASTEXITCODE" in text and '$ErrorActionPreference = "Stop"' in text
    for step in ("ruff format --check .", "ruff check .", "mypy --strict src tests", "pytest"):
        assert re.search(rf"Invoke-Step .*\{{ python -m {re.escape(step)}", text), step


def test_the_release_script_refuses_every_unsafe_state() -> None:
    text = (SCRIPTS / "release.ps1").read_text("utf-8")
    guards = [
        "git status --porcelain",
        "if ($dirty) { throw",
        "scripts/check.ps1",
        'if ($LASTEXITCODE -ne 0) { throw "The gate failed',
        "pypi.org/pypi/typedmultidict/$version/json",
        "if ($published) { throw",
        'if ($LASTEXITCODE -ne 0) { throw "The build failed',
        "twine check --strict",
        'if ($LASTEXITCODE -ne 0) { throw "twine check failed',
        'if ($LASTEXITCODE -ne 0) { throw "The upload failed',
    ]
    for guard in guards:
        assert guard in text, guard
    # The clean-tree and gate checks come before anything is built.
    assert text.index("git status --porcelain") < text.index("python -m build")
    assert text.index("scripts/check.ps1") < text.index("python -m build")


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_every_view_pickles_at_every_protocol(protocol: int) -> None:
    for cls in (MultiDict, CIMultiDict):
        md = cls([("a", 1), ("a", 2)])
        for view in (md.keys(), md.items(), md.values(), md.allitems(), md.allvalues()):
            again = pickle.loads(pickle.dumps(view, protocol))
            assert type(again) is type(view) and list(again) == list(view)


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_a_pickled_view_stays_bound_to_its_pickled_multi_dict(protocol: int) -> None:
    names = ["keys", "items", "values", "allitems", "allvalues"]
    md = MultiDict([("a", 1)])
    again, *loaded = pickle.loads(pickle.dumps([md, *(getattr(md, n)() for n in names)], protocol))
    again.add("b", 2)
    for name, view in zip(names, loaded, strict=True):
        assert list(view) == list(getattr(again, name)()), name
        assert len(view) == len(getattr(again, name)()), name
