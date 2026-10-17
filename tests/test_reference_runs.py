"""typedmultidict answers like the references on every scenario they were run through.

The stored answers come from ``scripts/capture_oracles.py`` (real runs of multidict, its
pure-Python twin, Werkzeug's MultiDict and Headers, requests, email.message and
wsgiref.headers). With TYPEDMULTIDICT_LIVE_ORACLES=1 the installed references are also
run here on fresh scenarios.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

import pytest
from oracle_refs import references, scenario
from oracle_run import agrees, run_ours, run_reference

from typedmultidict import CIMultiDict, MultiDict

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "oracle_runs.json").read_text(encoding="utf-8")
)
CASE_INSENSITIVE = {
    "multidict-ci", "multidict-py-ci", "werkzeug-headers", "requests", "email-message",
    "wsgiref-headers",
}  # fmt: skip


def _ours(name: str) -> Any:
    return CIMultiDict if name in CASE_INSENSITIVE else MultiDict


def test_the_fixture_covers_every_reference() -> None:
    assert set(FIXTURE["runs"]) == {"multidict", "multidict-py", "werkzeug-multidict"} | (
        CASE_INSENSITIVE
    )
    assert all(len(cases) >= 80 for cases in FIXTURE["runs"].values())
    assert {"multidict", "werkzeug", "requests"} <= set(FIXTURE["versions"])


@pytest.mark.parametrize("name", sorted(FIXTURE["runs"]))
def test_every_stored_scenario_matches(name: str) -> None:
    for case in FIXTURE["runs"][name]:
        mine = run_ours(_ours(name), case)
        assert agrees(case["record"], mine), (name, case["initial"], case["steps"])


@pytest.mark.skipif(
    os.environ.get("TYPEDMULTIDICT_LIVE_ORACLES") != "1",
    reason="set TYPEDMULTIDICT_LIVE_ORACLES=1 to run the installed references",
)
def test_fresh_scenarios_match_the_installed_references() -> None:
    rng = random.Random()
    refs = references()
    assert len(refs) == len(FIXTURE["runs"]), sorted(refs)
    for name, ref in refs.items():
        for _ in range(150):
            case = scenario(rng, ref[1], sorted(ref[3]))
            theirs = run_reference(name, ref, case)
            assert agrees(theirs, run_ours(_ours(name), case)), (name, case)
