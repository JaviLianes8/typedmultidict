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
