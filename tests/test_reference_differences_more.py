"""The remaining rows of the guide's table of differences, each run live.

Third-party references skip when they are not installed.
"""

from __future__ import annotations

import email.message
import wsgiref.headers
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict

NAME: Any = 5


def test_multidict_refuses_non_str_keys_where_a_plain_multi_dict_accepts_them() -> None:
    multidict = pytest.importorskip("multidict")
    with pytest.raises(TypeError):
        multidict.MultiDict([(NAME, 1)])
    assert MultiDict([(5, 1)])[5] == 1


def test_multidict_ci_lookups_of_non_str_names_raise_where_ours_are_absent() -> None:
    multidict = pytest.importorskip("multidict")
    theirs, ours = multidict.CIMultiDict([("a", 1)]), CIMultiDict([("a", 1)])
    assert (NAME in theirs) is False and (NAME in ours) is False
    with pytest.raises(TypeError):
        theirs.get(NAME)
    with pytest.raises(TypeError):
        theirs.getall(NAME, None)
    assert ours.get(NAME) is None and ours.getall(NAME, None) is None


def test_other_references_raise_even_for_in_with_a_non_str_name() -> None:
    message = email.message.Message()
    message["a"] = "1"
    others: list[Any] = [message, wsgiref.headers.Headers([("a", "1")])]
    for name in ("werkzeug.datastructures", "requests.structures"):
        module = pytest.importorskip(name)
        maker = getattr(module, "Headers", None) or module.CaseInsensitiveDict
        others.append(maker([("a", "1")]))
    for other in others:
        with pytest.raises(AttributeError):
            NAME in other  # noqa: B015
    assert NAME not in CIMultiDict([("a", "1")])


def test_header_containers_count_field_lines_where_we_count_names() -> None:
    message = email.message.Message()
    message["a"] = "1"
    message["A"] = "2"
    lines = [("a", "1"), ("A", "2")]
    assert len(message) == len(wsgiref.headers.Headers(list(lines))) == 2
    datastructures = pytest.importorskip("werkzeug.datastructures")
    assert len(datastructures.Headers(lines)) == 2
    assert len(CIMultiDict(lines)) == 1


def test_werkzeug_headers_empty_popitem_missing_delete_and_str_values() -> None:
    datastructures = pytest.importorskip("werkzeug.datastructures")
    headers = datastructures.Headers()
    with pytest.raises(IndexError):
        headers.popitem()
    del headers["x-missing"]
    headers.add("n", 5)
    assert headers["n"] == "5"
    ours: CIMultiDict[int] = CIMultiDict()
    with pytest.raises(KeyError):
        ours.popitem()
    with pytest.raises(KeyError):
        del ours["x-missing"]
    ours.add("n", 5)
    assert ours["n"] == 5


def test_email_get_all_of_a_missing_name_is_none_where_ours_is_empty() -> None:
    assert email.message.Message().get_all("x") is None
    assert CIMultiDict[str]().getall("x") == []


def test_multidict_compares_key_spellings_exactly_across_kinds() -> None:
    multidict = pytest.importorskip("multidict")
    assert multidict.MultiDict([("a", 1)]) == multidict.CIMultiDict([("a", 1)])
    assert multidict.MultiDict([("A", 1)]) != multidict.CIMultiDict([("a", 1)])
    assert MultiDict([("a", 1)]) == CIMultiDict([("a", 1)])
    assert MultiDict([("A", 1)]) == CIMultiDict([("a", 1)])
