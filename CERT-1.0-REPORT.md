# typedmultidict 1.0.0 certification report

Progress:
- [x] Branch `release/1.0.0` created from `main` (0.2.0, 04c2f6c; PyPI has 0.2.0)
- [x] Baseline gates run on 0.2.0
- [x] API review and 1.0.0 API changes (item 1)
- [x] Ground truth: reference implementations run live, fetched specifications (item 7)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e and upgrade from PyPI 0.2.0 (items 8, 13, 14)
- [x] Every interpreter on this PC (item 10)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer (item 16)
- [ ] Gates (item 15)
- [ ] PR open and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Baseline on 0.2.0 (before any change)

Fresh clone of `main` (04c2f6c) under a turn, CPython 3.13.2: `pytest` green (the wheel
e2e skipped without its opt-in variable), `ruff check .` and `mypy --strict src tests`
exit 0. PyPI has 0.2.0 only. Deleting 20 000 keys one at a time took 10.1 s and
20 000 `popone` calls on one key 18.3 s: every removal rebuilt the whole pair list.

## Supported Pythons (item 10)

`requires-python = ">=3.10"`. Wheel and sdist built from a fresh clone at 3d67cc4,
`twine check --strict` passed; the sdist's suite run against the installed wheel (`-I`,
source path removed) with the references, mypy and build installed,
`TYPEDMULTIDICT_E2E=1`, `TYPEDMULTIDICT_LIVE_ORACLES=1` and the fetched sources present,
so nothing skips: 392 passed on each of CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2
and 3.14.2 free-threaded (each test limited to 180 s). 3.8 and 3.9 are installed but
below `requires-python`.

## API review (items 1 to 5)

Kept from 0.2.0 with the same names, signatures and defaults: `MultiDict(initial=None)`,
`CIMultiDict`, `add`, `extend`, `merge`, `update(other=(), /, **kwargs)`, `getone`,
`getall`, `popone`, `popall`, `popitem`, `allitems`, `allvalues`, `to_dict`, `copy` and
the `MutableMapping` methods (`get`, `pop`, `setdefault`, `keys`, `items`, `values`,
`clear`, keyword-capable as before). `tests/test_contract.py` freezes every public
signature, `__all__`, the public module path of each class and the absence of any other
public name; the "no default" marker shows as `<missing>` in `help()`.

Defects of 0.2.0 found by the review, each checked against the real 0.2.0:

- Every removal rebuilt the whole pair list (quadratic, figures above).
- An endless element in bulk input (`MultiDict([itertools.count()])`) hung, and a huge
  one was copied whole before being refused.
- Error messages echoed a type name of any length.
- `allitems()` and `allvalues()` returned types importable only from a private module,
  so they could not be named in annotations.
- `getall` had no default, unlike `multidict.getall`.
- The README claimed `orderedmultidict` ships no type hints; its 1.0.2 wheel has
  `py.typed`. Rewritten with verified facts only.
- `release.ps1` refused to run for any project already on PyPI (so no update could be
  released) and did not run the gate; `check.ps1` used whatever tools came first on PATH.

Changed for 1.0.0, all in the CHANGELOG: storage with holes swept once they outnumber
live pairs and per-key deques, so every operation costs time in proportion to the pairs
it touches (20 000 deletions: 0.014 s); at most three items read per bulk element; type
names cut to 40 characters; `AllItemsView` and `AllValuesView` exported; `getall(key,
default)`; the mapping methods written out with docstrings (behaviour checked against the
`collections.abc` mixins); version from one source; release and gate scripts fixed. Every
public class and method carries a docstring with examples, run by
`tests/test_docstrings.py`; README and GUIDE examples run in `tests/test_docs.py`.
`mypy --strict src tests scripts` is clean, `py.typed` ships, and a strictly typed
consumer is checked by mypy against the installed wheel in the e2e test.

## Behaviour changes against PyPI 0.2.0

Everything 0.2.0 code does with valid input keeps working: the opt-in e2e test runs the
same program on 0.2.0 from PyPI and again after an in-place upgrade to the 1.0.0 wheel,
and pickles written by 0.2.0 load in 1.0.0. Differences: `getall` accepts a default; the
two view classes are public; a bulk element longer than two items that is not a tuple or
list is reported as "has length 3 or more" (it used to be read in full); type names in
messages are cut to 40 characters; removals are no longer quadratic.

## Ground truth (item 7)

Three kinds of truth, none of them the library's own output:

- **Reference implementations, run live.** `scripts/capture_oracles.py` (2026-10-17,
  CPython 3.13.2) drives multidict 7.1.0 (C and pure Python), Werkzeug 3.1.9 `MultiDict`
  and `Headers`, requests 2.34.2 `CaseInsensitiveDict`, `email.message.Message` and
  `wsgiref.headers.Headers` through 100 seeded scenarios each (900 in all), using only
  the calls whose meaning each shares with typedmultidict. `tests/fixtures/oracle_runs.json`
  holds every answer and the state after every step; `tests/test_reference_runs.py`
  replays all 900 and requires identical answers and states. With
  `TYPEDMULTIDICT_LIVE_ORACLES=1` it runs the installed references on 150 fresh
  scenarios each (done on Elena's PC with CPython 3.14 and in the interpreter matrix).
  Swapping the class (plain for case-insensitive) makes 44 to 94 of each reference's
  scenarios disagree, so the comparison discriminates.
- **The standard library, live.** `http.client.parse_headers` parses 40 seeded raw
  header blocks; a `CIMultiDict` built from the message answers every name in four
  spellings as the message does (`tests/test_http_parsing.py`). The documented mapping
  methods are checked against the `collections.abc` mixins on identical copies over
  random operations (`tests/test_abc_mixins.py`).
- **Fetched sources.** `scripts/fetch_sources.py` fetches RFC 9110, the Python 3.14
  `collections.abc`, `email.compat32-message` and `wsgiref` pages, the multidict and
  Werkzeug docs and requests' `structures.py` (v2.32.3) into the git-ignored
  `tests/sources/`; `MANIFEST.json` records URL, date, size, SHA-256 and licence, and
  `tests/test_sources.py` locates every cited fact in those copies.

The deliberate differences (multidict's pair-counting `len()`, raising `getall` and
one-value `pop`; Werkzeug's appending `update` and whole-key `popitem`; Headers'
last-value `update`; email's appending assignment; wsgiref's move to the end; requests'
single value; silent deletes) are shown live by `tests/test_reference_differences.py`
and listed in the GUIDE. Every case-insensitive reference folds with `str.lower`,
non-ASCII names included (Kelvin sign, sharp s, dotted capital I, titlecase digraphs),
and so does `CIMultiDict`. Python 3.14's `email` refuses non-ASCII header names, so the
email and wsgiref scenarios use ASCII names only.

## Fuzz and robustness (item 9)

`tests/test_fuzz.py`: 60 fixed seeds of 600 removal-heavy operations against a naive
list model, both classes, with pickle, copy and `to_dict` checks along the way (1 054
sweeps reached). The hypothesis state machines stay. `tests/test_robustness.py`:
removing everything one by one is linear (4 000 against 64 000 pairs, three shapes); a
200 000-pair `CIMultiDict` answers 5 000 lookups at once; endless and 50 000-item
elements fail at once; type names are bounded (also for a metaclass whose `__name__` is
not a string); values never appear in messages; a key whose hash raises leaves the
mapping unchanged on every write path. `tests/test_contracts_extra.py`: memory stays flat
over 200 000 add and `popone` cycles.

## Author mutation round (item 18)

Each mutant applied alone to a fresh clone of the pushed branch, `pytest -x` without the
wheel test, 240 s limit per run, baseline green before and after, run under a turn in
three batches. 36 mutants: 32 killed at once, 3 survivors closed by contracts added in
`tests/test_contracts_extra.py` (each then confirmed killed), 1 equivalent control.

| Id | File | Mutation | Caught by |
| --- | --- | --- | --- |
| A01 | `_storage.py` | sweep never runs | survived; then `tests/test_contracts_extra.py::test_holes_left_by_removals_are_swept_so_memory_stays_flat` (added) |
| A02 | `_storage.py` | sweep forgets to renumber positions | `tests/test_fuzz.py::test_long_runs_agree_with_a_naive_model[0]` |
| A03 | `_storage.py` | holes not counted | `tests/test_docstrings.py::test_every_public_class_has_a_passing_example[MultiDict]` |
| A04 | `_storage.py` | removed pair stays in the list | `tests/test_abc_mixins.py::test_overrides_match_the_mixins` |
| A05 | `_storage.py` | trim keeps one value too many | `tests/test_api.py::test_popall_default_may_be_any_type` |
| A06 | `_storage.py` | emptied key stays indexed | `tests/test_abc_mixins.py::test_overrides_match_the_mixins` |
| A07 | `_storage.py` | no change check per step | `tests/test_iteration.py::test_mutation_during_iteration_raises[<lambda>0-<lambda>5]` |
| A08 | `_storage.py` | assignment keeps the old spelling | `tests/test_ci.py::test_spelling_of_each_pair_is_kept_and_setitem_takes_the_new_one` |
| A09 | `_storage.py` | assignment in place is not a write | `tests/test_edges.py::test_replacing_a_single_value_during_iteration_raises` |
| A10 | `_storage.py` | version resets on clear | survived; then `tests/test_contracts_extra.py::test_an_iterator_still_fails_after_clear_and_refill` (added) |
| A11 | `_storage.py` | failed append not undone | `tests/test_input.py::test_unhashable_keys_are_refused_without_changes` |
| A12 | `_storage.py` | plain-mapping equality ignores repeated keys | survived; then `tests/test_contracts_extra.py::test_repeated_equal_values_still_differ_from_a_plain_mapping` (added) |
| A13 | `_storage.py` | mixed equality does not fold case | `tests/test_docs.py::test_every_readme_example_runs_and_prints_its_comment` |
| A14 | `_mapping.py` | get returns the last value | `tests/test_abc_mixins.py::test_overrides_match_the_mixins` |
| A15 | `_mapping.py` | pop leaves the first value | `tests/test_abc_mixins.py::test_overrides_match_the_mixins` |
| A16 | `_mapping.py` | setdefault stores with the lookup identity | `tests/test_ci.py::test_non_string_keys_are_refused_on_write[5]` |
| A17 | `_values.py` | getall ignores its default | `tests/test_docstrings.py::test_every_public_method_has_a_passing_example[CIMultiDict.getall]` |
| A18 | `_values.py` | popone takes the last value | `tests/test_api.py::test_popone_removes_only_the_first_value` |
| A19 | `_values.py` | popitem miscounts trailing holes | `tests/test_abc_mixins.py::test_overrides_match_the_mixins` |
| A20 | `_values.py` | to_dict drops each first value | `tests/test_api.py::test_to_dict_groups_values_under_the_key_order` |
| A21 | `_multidict.py` | merge appends present keys | `tests/test_api.py::test_merge_skips_keys_that_were_present` |
| A22 | `_multidict.py` | update never reuses positions | `tests/test_api.py::test_update_reuses_positions_and_appends_extras` |
| A23 | `_multidict.py` | update keeps extra old values | `tests/test_api.py::test_update_drops_old_values_beyond_the_new_ones` |
| A24 | `_multidict.py` | update keeps one extra old value | `tests/test_api.py::test_update_drops_old_values_beyond_the_new_ones` |
| A25 | `_pairs.py` | element read in full | `tests/test_robustness.py::test_an_endless_element_fails_at_once_instead_of_hanging` |
| A26 | `_pairs.py` | type name unbounded | `tests/test_robustness.py::test_type_names_in_messages_are_bounded` |
| A27 | `_pairs.py` | wrong error type for bad length | `tests/test_edges.py::test_a_one_item_element_is_reported_with_its_length` |
| A28 | `_cimultidict.py` | casefold instead of lower on write | `tests/test_ci.py::test_folding_is_lower_not_casefold` |
| A29 | `_cimultidict.py` | non-str lookup matches | `tests/test_ci.py::test_non_string_keys_are_absent_on_read[key4]` |
| A30 | `_views.py` | items view only checks first value | `tests/test_api.py::test_views_are_live_and_sized` |
| A31 | `_views.py` | items view counts holes | `tests/test_contracts_extra.py::test_holes_left_by_removals_are_swept_so_memory_stays_flat` |
| A32 | `_state.py` | unpickling drops a pair | `tests/test_api.py::test_copy_is_shallow_and_independent` |
| A33 | `_state.py` | holes travel in the pickle state | `tests/test_equality.py::test_pickles_store_plain_pairs` |
| A34 | `_mapping.py` | clear leaves the index | `tests/test_abc_mixins.py::test_overrides_match_the_mixins` |
| A35 | `__init__.py` | private module names | `tests/test_contract.py::test_every_exported_name_resolves_and_names_its_public_module` |
| A36 | `_storage.py` | sweep floor 0 | equivalent control: sweeping earlier changes memory use, never results |

## QA lenses (item 19)

Five independent reviews, one at a time, each reading the certification rules, running
the code and reporting only to the maintainer. Later rounds confirm the earlier findings
and sweep at most 40 new mutations on the code changed since.

| Lens | Round | Head | Verdict | Findings and outcome |
| --- | --- | --- | --- | --- |
| a. API and docs | 1 | a7001f1 | FAIL | signatures against the real 0.2.0 only add, every example and reference fact checked live, 20 000 random sequences against 0.2.0 differ only where the CHANGELOG says; `get`, `pop` and `setdefault` no longer went through the item hooks (a subclass saw different calls); README wheel count off by one; three survivors of 40 mutants (casefold in mixed equality, `allvalues` membership, `KeyError` arguments); source copies failed after a refetch because the byte hash was pinned; four wording details. Fixed in 2b3008e |
| a | 2 | 2b3008e | FAIL | all round 1 findings confirmed fixed; 16 mutants on the changed code, two survivors (`get` and `pop` swallowing `TypeError`). Contracts added in fc26142 |
| a | 3 | fc26142 | PASS | both survivors and a third (`setdefault` catching any exception) killed |
| b. Correctness and ground truth | 1 | b681d12 | FAIL | own drivers: 9 500 random sequences per reference (multidict C and pure, Werkzeug `MultiDict` and `Headers`, requests, `email`, `wsgiref`), 2 000 random `http.client` messages, 6 000 `collections.abc` checks, 0 mismatches outside the documented differences; RFC 9110 fetched and checked; the oracle fixture regenerates byte for byte; 40 mutants, three survivors (rollback popping the wrong end, `update` skipping the sweep, keyword pairs before positional ones); README listed `keys()` as a multidict difference although multidict 7 lists each key once; equality rule imprecise; several differences undocumented. Fixed in d3e25f2 |
| b | 2 | d3e25f2 | FAIL | the three survivors killed; two new GUIDE rows inexact and not tested live; Headers' silent delete undocumented. Fixed in 05ad952 (`tests/test_reference_differences_more.py`) |
| b | 3 | 05ad952 | PASS | every row true and run live with the references installed (C and pure-Python multidict) |
| c. Adversarial and robustness | 1 | 28aba6f | FAIL | 300 seeds of 1 500 operations with internal invariants checked, hostile keys, subclasses and inputs, scaling to 10^6 pairs (linear; add 3.2 s, popone 0.97 s, equality 0.26 s at 10^6), memory flat; a key whose `__eq__` writes to the same multi-dict corrupted the index silently; `repr` of a multi-dict holding its own `allitems()` recursed; `keys()`, `items()` and `values()` missed a write made before their first item; rollback under a hash that changes between calls (documented as outside the hash contract); five of 40 mutants survived. Fixed in 059f9cb (`_guard.py`, `_mapviews.py`, `tests/test_hostile.py`) |
| c | 2 | 059f9cb | FAIL | 90 reentrancy cases clean; the views renamed in place no longer pickled; `__init__` and `__setstate__` bypassed the guard; 33 mutants, three survivors (`popitem` guard and order, view names). Fixed in bbd4171 |
| c | 3 | bbd4171 | FAIL | 120 reentrancy cases clean; the constructor no longer went through `extend` (a subclass hook missed its input); a survivor on the re-init order. Constructor restored in 15748ec |
| c | 4 | 15748ec | FAIL | everything confirmed; `if initial:` instead of `is not None` survived. Contract added in 68e7f8f |
| c | 5 | 68e7f8f | PASS | survivor killed; the only remaining survivors are argued equivalent (a rollback that differs only for keys breaking the hash contract; slot names Python refuses to declare) |
| d. Packaging and real e2e | 1 | 973b649 | FAIL | reproducible builds, `twine check --strict`, wheel and sdist contents and metadata clean, wheel and sdist installed in clean venvs and used from outside, strict typed consumer, 62 pickles written by PyPI 0.2.0 load after the in-place upgrade, every CHANGELOG item checked against the real 0.2.0, suite on 3.10.19 to 3.14.2t (486 passed each); untracked files could reach the sdist (no clean-tree guard); one CHANGELOG line overstated; `allitems()`/`allvalues()` did not pickle at protocols 0 and 1, and mapping views came back broken at those protocols on 3.10 (both already so in 0.2.0); 18 of 33 packaging mutants survived (metadata, scripts). Fixed in 2df6361 and c776947 |
| d | 2 | c776947 | FAIL | fixes confirmed, matrix green (496 passed, 3.10 skips the two `tomllib` tests); 11 survivors (script guards checked only as text, detached view pickles, partial sdist list and keywords). Fixed in 825b992 (`tests/test_scripts.py` runs both scripts against a stub interpreter) |
| d | 3 | 825b992 | PASS | all 11 survivors killed |
