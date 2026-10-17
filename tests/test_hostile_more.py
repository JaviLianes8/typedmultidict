"""More writes from key comparisons: popitem, a re-run of __init__ and __setstate__, views."""

from __future__ import annotations

import pickle
from typing import Any

import pytest
from test_hostile import TARGET, _consistent, _Meddler

from typedmultidict import CIMultiDict, MultiDict


@pytest.mark.parametrize("nth", [1, 2])
@pytest.mark.parametrize("meddle", ["add", "init", "setstate"])
def test_popitem_refuses_a_write_from_its_key_comparisons(nth: int, meddle: str) -> None:
    md: MultiDict[Any, Any] = MultiDict([(_Meddler(1), 1), (_Meddler(2), 2)])
    calls = {
        "add": lambda: md.add("y", 1),
        "init": lambda: md.__init__([("z", 0)]),  # type: ignore[misc]
        "setstate": lambda: md.__setstate__(([("z", 0)], None, None)),
    }
    TARGET["write"] = calls[meddle]
    before = list(md.allitems())
    _Meddler.armed = nth
    try:
        md.popitem()
    except RuntimeError as error:
        assert "while one of its writes was running" in str(error)
        assert list(md.allitems()) == before
    else:
        assert _Meddler.armed, "popitem ran although the comparison wrote"
    _Meddler.armed = 0
    _consistent(md)


def test_rerunning_init_or_setstate_from_a_comparison_is_refused() -> None:
    md: MultiDict[Any, Any] = MultiDict([(_Meddler(1), 1), ("x", 0)])
    for write in (lambda: md.__init__([("z", 0)]), lambda: md.__setstate__(([], None, None))):  # type: ignore[misc]
        TARGET["write"] = write
        _Meddler.armed = 1
        with pytest.raises(RuntimeError):
            md.add(_Meddler(2), 2)
        _Meddler.armed = 0
        assert len(md.allitems()) == 2
        _consistent(md)


def test_mapping_views_keep_the_standard_names_and_pickle() -> None:
    md: MultiDict[str, int] = MultiDict([("a", 1)])
    assert repr(md.keys()) == "KeysView(MultiDict([('a', 1)]))"
    assert repr(md.items()) == "ItemsView(MultiDict([('a', 1)]))"
    assert repr(md.values()) == "ValuesView(MultiDict([('a', 1)]))"
    for view in (md.keys(), md.items(), md.values()):
        assert list(pickle.loads(pickle.dumps(view))) == list(view)


def test_the_constructor_goes_through_extend_so_subclass_hooks_see_its_input() -> None:
    class Checked(MultiDict[str, int]):
        def extend(self, other: Any) -> None:
            pairs = list(other)
            if any(value < 0 for _, value in pairs):
                raise ValueError("negative")
            super().extend(pairs)

    with pytest.raises(ValueError, match="negative"):
        Checked([("a", -1)])
    assert list(Checked([("a", 1)]).allitems()) == [("a", 1)]


def test_a_falsy_non_none_initial_is_still_read() -> None:
    for cls in (MultiDict, CIMultiDict):
        with pytest.raises(TypeError):
            cls(_loose(0))

    class Falsy(list[tuple[str, int]]):
        def __bool__(self) -> bool:
            raise RuntimeError("never asked")

    assert list(MultiDict(Falsy([("a", 1)])).allitems()) == [("a", 1)]


def _loose(value: object) -> Any:
    return value
