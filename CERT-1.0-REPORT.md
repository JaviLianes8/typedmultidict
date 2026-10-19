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
- [x] Bulk input read through `items()`, author mutation round 3 (items 1, 7, 18)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer (item 16)
- [x] Gates (item 15): at 926996d on a fresh clone (laptop, CPython 3.14), `ruff format --check .`,
  `ruff check .`, `mypy --strict src` (and `src tests scripts`) and `pytest` each exit 0
- [ ] PR open and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Baseline on 0.2.0 (before any change)

Fresh clone of `main` (04c2f6c) under a turn, CPython 3.13.2: `pytest` green (the wheel
e2e skipped without its opt-in variable), `ruff check .` and `mypy --strict src tests`
exit 0. PyPI has 0.2.0 only. Deleting 20 000 keys one at a time took 10.1 s and
20 000 `popone` calls on one key 18.3 s: every removal rebuilt the whole pair list.

## Supported Pythons (item 10)

`requires-python = ">=3.10"`. Wheel and sdist built from a fresh clone at 7847bcc,
`twine check --strict` passed; the sdist's suite run against the installed wheel (`-I`,
source path removed) with the references, mypy and build installed,
`TYPEDMULTIDICT_E2E=1`, `TYPEDMULTIDICT_LIVE_ORACLES=1` and the fetched sources present:
616 passed on each of CPython 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded,
and 614 passed with 2 skipped on 3.10.19 (the two checks that read `pyproject.toml` need
`tomllib`, new in 3.11). Each test was limited to 180 s. An earlier run at 3d67cc4 gave
392 passed on the same six. 3.8 and 3.9 are installed but
below `requires-python`.

## API review (items 1 to 5)

Kept from 0.2.0 with the same names, signatures and defaults: `CIMultiDict`, `add`,
`update(other=(), /, **kwargs)`, `getone`,
`getall`, `popone`, `popall`, `popitem`, `allitems`, `allvalues`, `to_dict`, `copy` and
the `MutableMapping` methods (`get`, `pop`, `setdefault`, `keys`, `items`, `values`,
`clear`, keyword-capable as before). `tests/test_contract.py` freezes every public
signature, `__all__`, the public module path of each class and the absence of any other
public name; the "no default" marker shows as `<missing>` in `help()`. Changed after QA
round 1 (lens a A2, lens b F3): the constructor is `MultiDict(initial=None, /, **kwargs)`
and `extend` and `merge` are `(other=(), /, **kwargs)`, matching `update`, `dict()` and
`multidict`, so the source can no longer be passed by name.

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
messages are cut to 40 characters; removals are no longer quadratic; a bulk source with a
callable `items()` is read through it, so an `http.client.HTTPMessage`, an
`email.message.Message` or a `wsgiref.headers.Headers` keeps every field of a repeated
name (0.2.0 read such objects through `keys()` and `[]`, which repeated the first value).
An object with only `keys()` and `[]` is still read as `dict.update` reads it.
After QA round 1: the constructor, `extend` and `merge` take keyword pairs and their
source is positional only (`MultiDict(initial=x)` now stores a pair named `"initial"`, as
`dict` does); `pop` and `setdefault` refuse a write made by a key comparison during their
lookup; an object that only claims to be a `str` is absent from a `CIMultiDict`; mapping
views pickle through `operator.methodcaller` (0.2.0 view pickles still load).

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
  Werkzeug docs and requests' `structures.py` (v2.34.2) into the git-ignored
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

How bulk input is read was checked live as well (`tests/test_reference_sources.py`,
`tests/test_contracts_sources.py`): the standard library's own `items()` of an
`http.client` message, an `email` message and a `wsgiref` header list is the expected
answer; multidict 7.1.0's C extension reads a header object through `items()` (same
fields as typedmultidict) and never calls `keys()`, while its pure-Python fallback reads
`keys()` and `[]` and repeats the first value; Werkzeug's `Headers` lists every field in
`items()` and its `MultiDict` only first values unless `items(multi=True)`.

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

### Round 3: the change to bulk input

Run at 7847bcc on Elena's PC under a turn, same procedure (`pytest -x`, the wheel test
left out, 300 s limit per test), unchanged control first and last, both green. 14 mutants,
14 killed.

| Id | File | Mutation | Caught by |
| --- | --- | --- | --- |
| M01 | `_pairs.py` | `items()` never used | `tests/test_contracts_sources.py::test_a_header_object_gives_every_field_in_order[_http]` |
| M02 | `_pairs.py` | a non-callable `items` attribute taken as the reader | `tests/test_contracts_sources.py::test_a_non_callable_items_attribute_falls_back_to_keys` |
| M03 | `_pairs.py` | what `items()` gives is not validated | `tests/test_contracts_sources.py::test_what_items_gives_is_checked_like_any_bulk_input` |
| M04 | `_pairs.py` | `items()` read only when `keys()` exists too | `tests/test_contracts_sources.py::test_an_object_with_only_items_is_read_through_it` |
| M05 | `_pairs.py` | two items read per element instead of three | `tests/test_contracts_edges.py::test_a_list_subclass_is_measured_by_reading_never_by_its_len` |
| M06 | `_pairs.py` | elements longer than two accepted | `tests/test_contracts_edges.py::test_a_list_subclass_is_measured_by_reading_never_by_its_len` |
| M07 | `_pairs.py` | "3 or more" reported as "3" | `tests/test_contracts_edges.py::test_a_list_subclass_is_measured_by_reading_never_by_its_len` |
| M08 | `_pairs.py` | another multi-dict read through `items()` (first values only) | `tests/test_contracts_input.py::test_a_case_insensitive_source_gives_each_pair_in_its_own_spelling` |
| M09 | `_pairs.py` | type name limit 41 | `tests/test_contracts_edges.py::test_a_longer_type_name_is_cut_to_forty_characters` |
| M10 | `_pairs.py` | element position off by one | `tests/test_contracts_edges.py::test_a_type_name_of_forty_characters_is_shown_whole` |
| M11 | `_multidict.py` | keyword pairs before positional ones | `tests/test_contracts_extra.py::test_update_takes_positional_pairs_before_keyword_ones` |
| M12 | `_pairs.py` | any error while reading an element becomes `TypeError` | `tests/test_contracts_input.py::test_an_element_whose_reading_fails_keeps_its_own_error[element0]` |
| M13 | `_pairs.py` | `items()` read in reverse | `tests/test_contracts_sources.py::test_a_header_object_gives_every_field_in_order[_http]` |
| M14 | `_pairs.py` | repeated equal pairs dropped | `tests/test_contracts_extra.py::test_repeated_equal_values_still_differ_from_a_plain_mapping` |

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
| e. Contract strength | 1 | 95c553a | FAIL | own mutation round without the author's list; 29 survivors (slot shapes through copies, the view pickle form, key errors as given, message edges, writes from comparisons with another multi-dict, lookup errors, mapping equality, foreign input errors, view membership). Contracts added in 1ab302b and 8027556 |
| a | 4 | 220c40a | FAIL | every README and GUIDE example and 63 doctests run, `__all__` exact, mypy strict clean, 28 pickles from 0.1.0 and 0.2.0 load; A1 mapping views pickled under the private `_mapviews`; A2 constructor signature unlike `update`, `dict` and multidict (`initial` by name, no keywords); A3 `popitem` documented as "last pair added"; A4 the Errors rule on messages overstated. Fixed in 11cb80a |
| b | 4 | 220c40a | FAIL | F3 constructor, `extend` and `merge` refused multidict's keyword pairs and `extend()` with no argument; F1 GUIDE row on multidict's mixed-kind equality true in one direction only; F2 `email.message` rejects non-ASCII names on 3.14, so the "all agree" sentence was false there. Fixed in 11cb80a |
| c | 6 | 220c40a | FAIL | fuzz (1 600 seeds, 3 interpreters, injected bugs caught 20 of 20), scaling linear, bounded messages; F1 unlocked writes from several threads raise misleading `RuntimeError` and corrupt the multi-dict, while the docs said "like `dict`"; F2 `pop` and `setdefault` let a key comparison write during their lookup; F3 `Mock(spec=str)` keys made `CIMultiDict` raise inside `str.lower`. Fixed in 11cb80a |
| e | 2 | 220c40a | FAIL | own mutation round; M59 (`update` overwriting reused pairs before indexing fresh ones) survived: no test made indexing a fresh key fail after a reused one. Fixed in 11cb80a |
| a | 5 | 975b020 | FAIL | A1 to A4 confirmed fixed, rest of the sweep clean; B1 a keyword pair named `self` raised `TypeError` in the constructor, `extend`, `merge` and `update`, against the GUIDE's "any string key, as in `dict()`". Fixed in 3314dad |
| b | 5 | 975b020 | FAIL | N1 the same `self` keyword pair (multidict's C extension accepts it); N2 the 3.14 exception named only `email.message`, while `http.client.HTTPMessage` refuses non-ASCII names there too. Fixed in 3314dad |
| c | 7 | 975b020 | FAIL | N1 the same `self` keyword pair (3.10.19, 3.13.2, 3.14.2t); N2 a subclass `__getitem__` that writes now makes `pop` and `setdefault` raise `RuntimeError`, undocumented. Documented and pinned in 3314dad |
| e | 3 | 975b020 | FAIL | M59 confirmed killed; F2-N38 (keyword pairs equal to a positional pair dropped) and F3-N19 (`isinstance` back in `type_name`) survived 697 tests. Contracts added in 3314dad |

### QA round 1 at 220c40a: what changed (11cb80a)

| Finding | Change | Proof |
| --- | --- | --- |
| a A1 | `keys()`, `items()`, `values()` views reduce to `operator.methodcaller(name)` called with the multi-dict; the old classes stay so 0.2.0 view pickles load | `tests/test_contracts_copies.py::test_view_pickles_name_only_public_modules` (every protocol), red on 220c40a |
| a A2, b F3 | `__init__(initial=None, /, **kwargs)`, `extend` and `merge` `(other=(), /, **kwargs)` with typed overloads (string keys for keywords); README, GUIDE, CHANGELOG, signature contract updated | `tests/test_contracts_keywords.py` (8 tests, all red on 220c40a), `tests/test_typing.py` lines 47 to 52 |
| a A3 | "last pair in order" in the docstring, README (twice), GUIDE and CHANGELOG | doctest unchanged |
| a A4 | GUIDE Errors paragraph: no message includes a value; bulk-input and key messages name a position, length or type; the rest are fixed sentences | docs |
| b F1 | GUIDE row: multidict calls them equal only when the plain side is already lower case | `tests/test_reference_differences_more.py::test_multidict_folds_only_the_case_insensitive_side_across_kinds` (C and pure Python, both orders) |
| b F2 | GUIDE: from 3.14 `email.message` refuses non-ASCII field names | `test_email_folds_non_ascii_names_only_before_python_3_14` (version-aware) |
| c F1 | option (b): README and GUIDE now say a multi-dict is not thread-safe, unlike `dict`, and must be shared behind a lock covering reads and writes; unlocked concurrent writes can raise `RuntimeError` and corrupt it. A per-instance write lock was not taken because reads racing a write would still be unsafe, so "like `dict`" could not be made true | `tests/test_contracts_threads.py` (4 threads, switch interval 1e-6, behind a lock: exact contents, popitem drains) |
| c F2 | the lookup of `pop` and `setdefault` runs under the write guard; the item hooks are still called as before | `tests/test_hostile.py` (pop and setdefault added to the reentrancy matrix, red on 220c40a), hook-order test unchanged |
| c F3 | `CIMultiDict`, mixed equality, type names and `allitems()` membership test the real type (`issubclass(type(x), str)` / `tuple`) | `tests/test_contracts_spoofed.py` (4 tests, red on 220c40a) |
| e M59 | contract added: `update([("x", 5), (meddler, 2)])` with the refused write at comparison 1 to 3 | `tests/test_hostile.py`, kills M59 at comparison 3 (checked by applying M59 to 11cb80a: 3 failures) |

Gates at 11cb80a on a fresh clone (Elena's PC, turn elena/7, CPython 3.14): `ruff format
--check .`, `ruff check .`, `mypy --strict src tests scripts` and `pytest` (697 passed,
13 skipped, all opt-in) each exit 0.

### QA round 2 at 975b020: what changed (3314dad, 637ff25)

| Finding | Change | Proof |
| --- | --- | --- |
| a B1, b N1, c N1 | the write guard's wrapper takes `self` positional only (`run(self, /, *args, **kwargs)`), so a keyword pair named `self` reaches the method; CHANGELOG says any string can be a keyword key, `self` included (0.2.0's `update` already took it, so no upgrade change) | `tests/test_contracts_keywords.py::test_a_keyword_pair_may_be_named_self` (constructor, `extend`, `merge`, `update`, both classes), red on 975b020 |
| b N2 | GUIDE: from 3.14 `email.message`, and so `http.client` whose messages are `email.message.Message` objects, refuses non-ASCII field names (checked on 3.14.2: `ValueError`; on 3.12.12 accepted) | `tests/test_reference_differences_more.py::test_email_and_http_client_fold_non_ascii_names_only_before_python_3_14` (both classes, version-aware) |
| c N2 | option (a): the GUIDE Errors row and the CHANGELOG say the lookup of `pop` and `setdefault` is `self[key]`, so a subclass `__getitem__` that writes makes them raise `RuntimeError`; `md[key]` alone still runs it. Behaviour kept: `dict.pop` does not call an overridden `__getitem__` either, and calling the hook outside the guard would reopen round 1's c F2 | `tests/test_hostile_more.py::test_a_getitem_hook_that_writes_is_refused_inside_pop_and_setdefault` (nothing changed after the error) |
| e F2-N38 | contract: a keyword pair equal to a positional pair is kept by the constructor, `extend`, `merge` and `update` | `tests/test_contracts_keywords.py::test_a_keyword_pair_repeating_a_positional_pair_is_kept`, fails with N38 applied |
| e F3-N19 | contract: a type whose `__name__` is a fake `str` prints as `?` in the CI key error and the bad-element error | `tests/test_contracts_spoofed.py::test_a_type_name_that_only_pretends_to_be_a_str_prints_as_a_question_mark`, fails with N19 applied |

Gates at 637ff25 on a fresh clone (Elena's PC, turn elena/2, CPython 3.14): `ruff format
--check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests scripts` and
`pytest` (703 passed, 13 skipped, all opt-in) each exit 0.

### Independent review round 1 at 5f6b228: what changed

The reviewer scored items 1 to 18 by running them: 16 PASS, item 17 pending the merge,
item 11 FAIL (so item 16 FAIL until a re-review), plus three observations.

| Finding | Change | Proof |
| --- | --- | --- |
| R1 item 11 | the README Why section said behaviour was checked against "all of the above", which included `orderedmultidict`, never run against the library; it now names only what is checked: multidict, Werkzeug, requests and the standard library | README; `twine check --strict` and `tests/test_docs.py` rerun |
| R1 item 16 | follows from item 11; re-review requested | |
| OBS a | requests' `structures.py` version in this report corrected to v2.34.2, as in the manifest, `fetch_sources.py` and the GUIDE | this report, Ground truth |
| OBS b | `scripts/capture_oracles.py` now defaults to 100 scenarios per reference (seed 2026), the size of the committed fixture, and says so in its usage text | script |
| OBS c, d, e | lens d's ground was rerun by the reviewer at 5f6b228 (archives, clean venvs, upgrade from PyPI 0.2.0, 3.10 to 3.14t), all green; the summaries of lens a round 6 and of this review are recorded here and in the lens table at finalize | |

### Disputed findings

None. Every finding of rounds 1 and 2 and of review round 1 was reproduced before it was fixed.
