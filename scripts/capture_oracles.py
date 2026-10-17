"""Drive the reference implementations through seeded scenarios and store their answers.

usage: python scripts/capture_oracles.py [scenarios-per-reference] [seed]

Writes tests/fixtures/oracle_runs.json: for every reference, the scenarios and what the
reference returned and showed after each step. Run it with multidict, werkzeug and
requests installed (the dev extras); the output records their versions.
"""

from __future__ import annotations

import contextlib
import datetime
import importlib.metadata
import json
import platform
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from oracle_refs import references, scenario  # noqa: E402
from oracle_run import run_reference  # noqa: E402


def capture(count: int, seed: int) -> dict[str, object]:
    runs: dict[str, object] = {}
    for name, ref in references().items():
        rng = random.Random(f"{seed}-{name}")
        cases = [scenario(rng, ref[1], sorted(ref[3])) for _ in range(count)]
        runs[name] = [{**case, "record": run_reference(name, ref, case)} for case in cases]
    versions = {"python": platform.python_version()}
    for package in ("multidict", "werkzeug", "requests"):
        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            versions[package] = importlib.metadata.version(package)
    return {
        "captured": datetime.date.today().isoformat(),
        "seed": seed,
        "versions": versions,
        "runs": runs,
    }


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    data = capture(count, seed)
    out = ROOT / "tests" / "fixtures" / "oracle_runs.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, separators=(",", ":"), sort_keys=True) + "\n", "utf-8")
    runs: dict[str, list[object]] = data["runs"]  # type: ignore[assignment]
    print(f"{sum(len(cases) for cases in runs.values())} scenarios, {data['versions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
