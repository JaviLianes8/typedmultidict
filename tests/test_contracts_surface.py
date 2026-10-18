"""Surface rules: writes from comparisons, lookup errors, equality, repr and view membership."""

from __future__ import annotations

import operator
from collections.abc import Callable, Iterator, Mapping

import pytest

from typedmultidict import CIMultiDict, MultiDict


def test_a_key_comparison_may_write_to_another_multi_dict() -> None:
    log: MultiDict[str, int] = MultiDict()

    class Logged:
        def __init__(self, n: int) -> None:
            self.n = n

        def __hash__(self) -> int:
            return 1

        def __eq__(self, other: object) -> bool:
            log.add("compared", self.n)  # a different multi-dict: allowed
            return isinstance(other, Logged) and other.n == self.n

    md: MultiDict[Logged, str] = MultiDict([(Logged(1), "a")])
    md.add(Logged(2), "b")
    md[Logged(1)] = "c"
    del md[Logged(2)]
    assert log.getall("compared") and list(md.values()) == ["c"]


class _Indexy(MultiDict[str, int]):
    def __getitem__(self, key: str) -> int:
        if key == "bad":
            raise IndexError("refused")  # a LookupError, but not a KeyError
        return super().__getitem__(key)


def test_a_lookup_error_that_is_not_a_key_error_does_not_mean_absent() -> None:
    md = _Indexy()
    calls: list[Callable[[], object]] = [
        lambda: md.get("bad"), lambda: md.pop("bad", 1), lambda: md.setdefault("bad", 1)
    ]  # fmt: skip
    for call in calls:
        with pytest.raises(IndexError):
            call()
    assert not md


class _ReadOnly(Mapping[str, int]):
    # A Mapping that is not a dict.
    def __init__(self, data: dict[str, int]) -> None:
        self._data = data

    def __getitem__(self, key: str) -> int:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


def test_any_mapping_is_compared_by_the_single_value_rule() -> None:
    assert MultiDict([("a", 1), ("b", 2)]) == _ReadOnly({"b": 2, "a": 1})
    repeated = MultiDict([("a", 1), ("a", 2)])
    assert repeated.__eq__(_ReadOnly({"a": 1})) is False
    assert repeated != _ReadOnly({"a": 1})


def test_repr_names_a_subclass_by_its_plain_name() -> None:
    class Local(MultiDict[str, int]):
        pass

    assert repr(Local([("a", 1)])) == "Local([('a', 1)])"


def test_pair_membership_hashes_the_key_like_dict_items() -> None:
    md = MultiDict([("a", 1)])
    for view in (md.allitems(), md.items(), {"a": 1}.items()):
        with pytest.raises(TypeError):
            operator.contains(view, ([], 1))
    unhashable: object = ([], 1)
    assert unhashable not in CIMultiDict([("a", 1)]).allitems()  # a non-str name: absent


def test_only_a_two_item_tuple_can_be_a_pair_like_dict_items() -> None:
    md = MultiDict([("a", 1)])
    assert ("a", 1) in md.allitems()
    as_list: object = ["a", 1]
    assert as_list not in md.allitems()
    assert not operator.contains({"a": 1}.items(), as_list)


def test_membership_skips_removed_pairs_before_they_are_swept() -> None:
    md = MultiDict([(f"k{i}", i) for i in range(10)])
    for i in range(3):
        del md[f"k{i}"]  # three holes: fewer than the sweep needs
    assert 5 in md.allvalues() and 0 not in md.allvalues()
    assert ("k5", 5) in md.allitems() and ("k0", 0) not in md.allitems()
    assert list(md.allvalues()) == list(range(3, 10))
