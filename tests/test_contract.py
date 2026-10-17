"""The public surface: names, signatures, module paths and shipped type information."""

from __future__ import annotations

import importlib.resources
import inspect

import pytest

import typedmultidict
from typedmultidict import AllItemsView, AllValuesView, CIMultiDict, MultiDict

# The public API. This list is the contract: the tests below fail the moment it drifts.
PUBLIC_API: list[str] = ["AllItemsView", "AllValuesView", "CIMultiDict", "MultiDict"]

KEY_DEFAULT = "(self, key: 'K', default: 'Any' = <missing>) -> 'Any'"
SIGNATURES: dict[str, str] = {
    "__init__": "(self, initial: 'MultiDictInput[K, V] | None' = None) -> 'None'",
    "add": "(self, key: 'K', value: 'V') -> 'None'",
    "allitems": "(self) -> 'AllItemsView[K, V]'",
    "allvalues": "(self) -> 'AllValuesView[V]'",
    "clear": "(self) -> 'None'",
    "copy": "(self: 'Self') -> 'Self'",
    "extend": "(self, other: 'MultiDictInput[K, V]') -> 'None'",
    "get": "(self, key: 'K', default: 'Any' = None) -> 'Any'",
    "getall": KEY_DEFAULT,
    "getone": KEY_DEFAULT,
    "items": "(self) -> 'ItemsView[K, V]'",
    "keys": "(self) -> 'KeysView[K]'",
    "merge": "(self, other: 'MultiDictInput[K, V]') -> 'None'",
    "pop": KEY_DEFAULT,
    "popall": KEY_DEFAULT,
    "popitem": "(self) -> 'tuple[K, V]'",
    "popone": KEY_DEFAULT,
    "setdefault": "(self, key: 'K', default: 'Any' = None) -> 'Any'",
    "to_dict": "(self) -> 'dict[K, list[V]]'",
    "update": "(self, other: 'Any' = (), /, **kwargs: 'Any') -> 'None'",
    "values": "(self) -> 'ValuesView[V]'",
}


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(typedmultidict.__all__) == sorted(PUBLIC_API)


def test_nothing_else_is_public() -> None:
    public = {name for name in vars(typedmultidict) if not name.startswith("_")}
    assert public == set(PUBLIC_API)


def test_every_exported_name_resolves_and_names_its_public_module() -> None:
    for name in typedmultidict.__all__:
        obj = getattr(typedmultidict, name)
        assert obj.__module__ == "typedmultidict"
        assert obj.__qualname__ == name


def test_version_is_a_three_part_string() -> None:
    parts = typedmultidict.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("typedmultidict").joinpath("py.typed").is_file()


@pytest.mark.parametrize("cls", [MultiDict, CIMultiDict])
def test_every_public_method_keeps_its_signature(cls: type) -> None:
    methods = {name for name in dir(cls) if not name.startswith("_")}
    assert methods == set(SIGNATURES) - {"__init__"}
    for name, signature in SIGNATURES.items():
        assert str(inspect.signature(getattr(cls, name))) == signature, name


def test_the_classes_form_one_hierarchy() -> None:
    assert issubclass(CIMultiDict, MultiDict)
    for view in (AllItemsView, AllValuesView):
        assert {name for name in dir(view) if not name.startswith("_")} == set()


def test_the_missing_marker_reads_as_such_in_help() -> None:
    assert "<missing>" in str(inspect.signature(MultiDict.getone))
