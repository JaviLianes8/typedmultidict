"""Hostile and huge input: no hang, no quadratic blow-up, bounded error messages."""

from __future__ import annotations

import itertools
import time
from collections.abc import Callable
from typing import Any

import pytest

from typedmultidict import CIMultiDict, MultiDict


def _loose(value: object) -> Any:
    # Deliberately ill-typed input, as an untyped caller would pass it.
    return value


def _best_of_three(work: Callable[[], None]) -> float:
    times = []
    for _ in range(3):
        start = time.perf_counter()
        work()
        times.append(time.perf_counter() - start)
    return min(times)


def _delete_every_key(n: int) -> Callable[[], None]:
    def work() -> None:
        md = MultiDict((i, i) for i in range(n))
        for i in range(n):
            del md[i]
        assert not md

    return work


def _popone_every_value(n: int) -> Callable[[], None]:
    def work() -> None:
        md = CIMultiDict(("Via", i) for i in range(n))
        for i in range(n):
            assert md.popone("via") == i

    return work


def _pop_the_last_pairs(n: int) -> Callable[[], None]:
    def work() -> None:
        md = MultiDict((i % 7, i) for i in range(n))
        for i in range(0, n, 2):
            md.popone(i % 7, None)
        while md:
            md.popitem()

    return work


@pytest.mark.parametrize("make", [_delete_every_key, _popone_every_value, _pop_the_last_pairs])
def test_removing_everything_one_by_one_is_linear(make: Callable[[int], Any]) -> None:
    small, large = _best_of_three(make(4_000)), _best_of_three(make(64_000))
    # Linear work grows 16 times; the quadratic storage of 0.2.0 grew about 256 times.
    assert large < max(small, 1e-3) * 64, (small, large)


def test_a_large_multi_dict_answers_every_query_quickly() -> None:
    md: CIMultiDict[int] = CIMultiDict((f"X-Header-{i % 5000}", i) for i in range(200_000))
    start = time.perf_counter()
    for i in range(5000):
        assert md.getone(f"x-header-{i}") == i
        assert len(md.getall(f"X-HEADER-{i}")) == 40
    assert time.perf_counter() - start < 5


def test_an_endless_element_fails_at_once_instead_of_hanging() -> None:
    with pytest.raises(ValueError, match=r"element #1 has length 3 or more; 2 is required"):
        MultiDict(_loose([("a", 1), itertools.count()]))


def test_a_long_tuple_reports_its_exact_length() -> None:
    with pytest.raises(ValueError, match=r"element #0 has length 50000; 2 is required"):
        MultiDict(_loose([tuple(range(50_000))]))


def test_type_names_in_messages_are_bounded() -> None:
    long_type = type("N" * 5000, (), {})
    with pytest.raises(TypeError) as caught:
        MultiDict(_loose([long_type()]))
    assert len(str(caught.value)) < 100
    assert str(caught.value).endswith("N" * 37 + "...")
    with pytest.raises(TypeError) as caught:
        CIMultiDict[int]().add(_loose(long_type()), 1)
    assert len(str(caught.value)) < 120


def test_a_metaclass_with_a_strange_name_does_not_break_the_message() -> None:
    class Meta(type):
        @property
        def __name__(cls) -> Any:  # type: ignore[override]
            return 12345

    odd: Any = Meta("Odd", (), {})
    with pytest.raises(TypeError, match=r"element #0 is not a \(key, value\) pair: \?$"):
        MultiDict(_loose([odd()]))


def test_values_never_appear_in_error_messages() -> None:
    secret = "s3cr3t-token"
    with pytest.raises(ValueError) as caught:
        MultiDict(_loose([("Authorization", secret, "x")]))
    assert secret not in str(caught.value)
    with pytest.raises(TypeError) as wrong_key:
        CIMultiDict[str]().add(_loose(12345), secret)
    assert secret not in str(wrong_key.value) and "12345" not in str(wrong_key.value)


class _HashBomb:
    def __hash__(self) -> int:
        raise RuntimeError("no hash")


def test_a_key_whose_hash_raises_leaves_the_mapping_unchanged() -> None:
    md: MultiDict[Any, int] = MultiDict([("a", 1)])
    calls: list[Callable[[], object]] = [
        lambda: md.add(_HashBomb(), 2),
        lambda: md.extend([("b", 2), (_HashBomb(), 3)]),
        lambda: md.update([("a", 5), (_HashBomb(), 3)]),
        lambda: md.merge([("c", 2), (_HashBomb(), 3)]),
        lambda: md.__setitem__(_HashBomb(), 3),
    ]
    for call in calls:
        with pytest.raises(RuntimeError, match="no hash"):
            call()
        assert list(md.allitems()) == [("a", 1)]
        assert len(md) == 1 and "b" not in md and "c" not in md
