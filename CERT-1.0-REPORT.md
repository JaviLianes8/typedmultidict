# typedmultidict 1.0.0 certification report

Progress:
- [x] Branch `release/1.0.0` created from `main` (0.2.0, 04c2f6c; PyPI has 0.2.0)
- [x] Baseline gates run on 0.2.0
- [ ] API review and 1.0.0 API changes (item 1)
- [ ] Ground truth: reference implementations run live, fetched specifications (item 7)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e and upgrade from PyPI 0.2.0 (items 8, 13, 14)
- [ ] Every interpreter on this PC (item 10)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer (item 16)
- [ ] Gates (item 15)
- [ ] PR open and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Baseline on 0.2.0 (before any change)

Fresh clone of `main` (04c2f6c) under a turn, CPython 3.13.2: `pytest` green (the wheel
e2e skipped without its opt-in variable), `ruff check .` and `mypy --strict src tests`
exit 0. PyPI has 0.2.0 only. Deleting 20 000 keys one at a time took 10.1 s and
20 000 `popone` calls on one key 18.3 s: every removal rebuilt the whole pair list.
