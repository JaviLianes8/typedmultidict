"""The gate and release scripts, run for real against a stub python that records each call.

Windows only (they are PowerShell scripts); skipped where PowerShell or git is missing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHELL = shutil.which("powershell") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(
    os.name != "nt" or SHELL is None or shutil.which("git") is None,
    reason="needs Windows PowerShell and git",
)


def _stub(tmp: Path, failing: str) -> tuple[dict[str, str], Path]:
    # A python.cmd placed first on PATH: logs its arguments, fails when they contain `failing`.
    bin_dir, log = tmp / "bin", tmp / "calls.log"
    bin_dir.mkdir()
    fail = f'echo %* | findstr /C:"{failing}" >nul && exit /b 3' if failing else "rem"
    (bin_dir / "python.cmd").write_text(
        f'@echo off\r\necho %*>>"{log}"\r\n{fail}\r\nexit /b 0\r\n', encoding="ascii"
    )
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return env, log


def _run(script: Path, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    assert SHELL is not None
    command = [SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)


def _calls(log: Path) -> list[str]:
    return log.read_text("ascii").splitlines() if log.exists() else []


@pytest.mark.parametrize("failing", ["ruff format", "ruff check", "mypy", "pytest"])
def test_the_gate_stops_at_the_first_failing_step(tmp_path: Path, failing: str) -> None:
    env, log = _stub(tmp_path, failing)
    result = _run(ROOT / "scripts" / "check.ps1", tmp_path, env)
    assert result.returncode == 3, result.stdout + result.stderr
    calls = _calls(log)
    assert failing in calls[-1] and "gate green" not in result.stdout


def test_the_gate_runs_every_step_when_all_pass(tmp_path: Path) -> None:
    env, log = _stub(tmp_path, "")
    result = _run(ROOT / "scripts" / "check.ps1", tmp_path, env)
    assert result.returncode == 0 and "gate green" in result.stdout
    assert [call.split()[1] for call in _calls(log)] == ["ruff", "ruff", "mypy", "pytest"]
    assert "--strict" in _calls(log)[2]


def _repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "release.ps1", repo / "scripts" / "release.ps1")
    shutil.copy(ROOT / "scripts" / "check.ps1", repo / "scripts" / "check.ps1")
    for args in (["init", "-q"], ["add", "."]):
        subprocess.run(["git", *args], cwd=repo, check=True, timeout=60)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
        cwd=repo, check=True, timeout=60,
    )  # fmt: skip
    return repo


def test_release_refuses_an_untracked_file_deep_in_the_tree(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "scratch.py").write_text("x = 1\n", "ascii")
    env, log = _stub(tmp_path, "")
    result = _run(repo / "scripts" / "release.ps1", repo, env)
    assert result.returncode != 0 and "not clean" in result.stdout + result.stderr
    assert _calls(log) == []


def test_release_refuses_outside_a_git_checkout(tmp_path: Path) -> None:
    folder = tmp_path / "plain" / "scripts"
    folder.mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "release.ps1", folder / "release.ps1")
    env, log = _stub(tmp_path, "")
    env["GIT_CEILING_DIRECTORIES"] = str(tmp_path)
    result = _run(folder / "release.ps1", folder.parent, env)
    assert result.returncode != 0 and "git status failed" in result.stdout + result.stderr
    assert _calls(log) == []


def test_release_stops_on_a_red_gate_before_building(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    env, log = _stub(tmp_path, "pytest")
    result = _run(repo / "scripts" / "release.ps1", repo, env)
    assert result.returncode != 0 and "gate failed" in result.stdout + result.stderr
    assert not [call for call in _calls(log) if "build" in call or "twine" in call]
