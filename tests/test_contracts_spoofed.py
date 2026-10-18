"""An object that only pretends to be a str (a mock, a proxy) is not a case-insensitive key."""

from __future__ import annotations

from typing import Any
from unittest import mock

import pytest

from typedmultidict import CIMultiDict, MultiDict


def _fake() -> Any:
    fake = mock.Mock(spec=str)
    assert isinstance(fake, str) and not issubclass(type(fake), str)
    return fake


def test_looking_up_a_fake_str_finds_nothing() -> None:
    headers = CIMultiDict([("A", 1)])
    fake = _fake()
    assert fake not in headers
    assert headers.get(fake) is None and headers.getall(fake) == []
    assert headers.getone(fake, 0) == 0 and headers.popall(fake, None) is None
    assert (fake, 1) not in headers.allitems()
    with pytest.raises(KeyError):
        headers[fake]
    assert list(headers.allitems()) == [("A", 1)]


def test_adding_a_fake_str_gives_the_documented_error() -> None:
    headers = CIMultiDict([("A", 1)])
    with pytest.raises(TypeError, match=r"^CIMultiDict keys must be str, not \w+$"):
        headers.add(_fake(), 1)
    assert list(headers.allitems()) == [("A", 1)]


def test_a_fake_str_key_compares_unequal_instead_of_raising() -> None:
    fake = _fake()
    assert MultiDict([(fake, 1)]) != CIMultiDict([("a", 1)])
    assert CIMultiDict([("a", 1)]) != MultiDict([(fake, 1)])


def test_a_fake_tuple_is_not_a_pair_in_a_view() -> None:
    fake = mock.Mock(spec=tuple)
    assert fake not in MultiDict([("a", 1)]).allitems()


def _type_with_a_fake_str_name() -> type:
    class FakeStr:
        __class__ = str  # type: ignore[assignment]

    class Meta(type):
        @property
        def __name__(cls) -> Any:  # type: ignore[override]
            return FakeStr()

    return Meta("Odd", (), {})


def test_a_type_name_that_only_pretends_to_be_a_str_prints_as_a_question_mark() -> None:
    odd = _type_with_a_fake_str_name()
    with pytest.raises(TypeError, match=r"^CIMultiDict keys must be str, not \?$"):
        CIMultiDict[int]().add(odd(), 1)
    with pytest.raises(TypeError, match=r"^element #0 is not a \(key, value\) pair: \?$"):
        MultiDict([odd()])
