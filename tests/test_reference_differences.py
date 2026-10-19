"""Where typedmultidict deliberately differs from a reference, the difference is real.

Each test runs the reference live and shows both answers, so the guide's table of
differences stays true. Third-party references skip when they are not installed.
"""

from __future__ import annotations

import email.message
import wsgiref.headers

import pytest

from typedmultidict import CIMultiDict, MultiDict

PAIRS = [("a", "1"), ("b", "2"), ("a", "3")]


def test_multidict_counts_pairs_where_we_count_keys() -> None:
    multidict = pytest.importorskip("multidict")
    assert len(multidict.MultiDict(PAIRS)) == 3
    assert len(MultiDict(PAIRS)) == 2
    assert len(MultiDict(PAIRS).allitems()) == 3


def test_multidict_views_show_every_pair_where_ours_show_first_values() -> None:
    multidict = pytest.importorskip("multidict")
    # multidict 7 lists each key once in keys(); items() and values() still repeat.
    assert list(multidict.MultiDict(PAIRS).items()) == PAIRS
    assert list(multidict.MultiDict(PAIRS).values()) == ["1", "2", "3"]
    assert list(MultiDict(PAIRS).keys()) == ["a", "b"]
    assert list(MultiDict(PAIRS).values()) == ["1", "2"]
    assert list(MultiDict(PAIRS).items()) == [("a", "1"), ("b", "2")]


def test_multidict_getall_raises_for_a_missing_key_where_ours_returns_empty() -> None:
    multidict = pytest.importorskip("multidict")
    with pytest.raises(KeyError):
        multidict.MultiDict(PAIRS).getall("z")
    assert MultiDict(PAIRS).getall("z") == []
    assert multidict.MultiDict(PAIRS).getall("z", None) is MultiDict(PAIRS).getall("z", None)


def test_multidict_pop_takes_one_value_where_ours_takes_every_value() -> None:
    multidict = pytest.importorskip("multidict")
    theirs, ours = multidict.MultiDict(PAIRS), MultiDict(PAIRS)
    assert theirs.pop("a") == ours.pop("a") == "1"
    assert theirs.getall("a") == ["3"]
    assert ours.getall("a") == []


def test_werkzeug_update_appends_where_ours_replaces() -> None:
    datastructures = pytest.importorskip("werkzeug.datastructures")
    theirs, ours = datastructures.MultiDict(PAIRS), MultiDict(PAIRS)
    theirs.update([("a", "9")])
    ours.update([("a", "9")])
    assert theirs.getlist("a") == ["1", "3", "9"]
    assert ours.getall("a") == ["9"]


def test_werkzeug_popitem_takes_a_whole_key_where_ours_takes_the_last_pair() -> None:
    datastructures = pytest.importorskip("werkzeug.datastructures")
    theirs, ours = datastructures.MultiDict(PAIRS), MultiDict(PAIRS)
    assert theirs.popitem() == ("b", "2") or theirs.getlist("a") == []
    assert ours.popitem() == ("a", "3")
    assert ours.getall("a") == ["1"]


def test_werkzeug_headers_update_keeps_one_value_per_incoming_pair_list() -> None:
    datastructures = pytest.importorskip("werkzeug.datastructures")
    start = [("A", "1"), ("b", "2"), ("a", "3"), ("c", "4")]
    theirs, ours = datastructures.Headers(start), CIMultiDict(start)
    theirs.update([("a", "7"), ("a", "8")])
    ours.update([("a", "7"), ("a", "8")])
    # Each incoming pair replaces the name again, so only the last value survives there.
    assert list(theirs.items()) == [("a", "8"), ("b", "2"), ("c", "4")]
    assert list(ours.allitems()) == [("a", "7"), ("b", "2"), ("a", "8"), ("c", "4")]


def test_email_item_assignment_appends_where_ours_replaces() -> None:
    message = email.message.Message()
    message["X-A"] = "1"
    message["x-a"] = "2"
    ours: CIMultiDict[str] = CIMultiDict([("X-A", "1")])
    ours["x-a"] = "2"
    assert message.get_all("X-A") == ["1", "2"]
    assert ours.getall("X-A") == ["2"]


def test_email_and_wsgiref_ignore_deleting_a_missing_name_where_we_raise() -> None:
    message = email.message.Message()
    del message["x-missing"]
    headers = wsgiref.headers.Headers([])
    del headers["x-missing"]
    with pytest.raises(KeyError):
        del CIMultiDict[str]()["x-missing"]


def test_wsgiref_assignment_moves_the_name_to_the_end_where_ours_keeps_its_place() -> None:
    start = [("A", "1"), ("b", "2"), ("a", "3")]
    theirs, ours = wsgiref.headers.Headers(list(start)), CIMultiDict(start)
    theirs["a"] = "9"
    ours["a"] = "9"
    assert theirs.items() == [("b", "2"), ("a", "9")]
    assert list(ours.allitems()) == [("a", "9"), ("b", "2")]


def test_requests_keeps_one_value_per_name() -> None:
    structures = pytest.importorskip("requests.structures")
    theirs = structures.CaseInsensitiveDict([("A", "1"), ("a", "2")])
    assert list(theirs.items()) == [("a", "2")]
    assert CIMultiDict([("A", "1"), ("a", "2")]).getall("A") == ["1", "2"]
