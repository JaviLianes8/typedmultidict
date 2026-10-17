"""Every public class and method carries a docstring whose examples run and pass."""

from __future__ import annotations

import doctest
import inspect

import pytest

import typedmultidict

PUBLIC = [getattr(typedmultidict, name) for name in typedmultidict.__all__]
MEMBERS = [
    (cls.__name__, name, member)
    for cls in PUBLIC
    for name, member in inspect.getmembers(cls)
    if not name.startswith("_") and callable(member)
]


def _run(name: str, doc: str | None) -> int:
    assert doc, f"{name} has no docstring"
    parser = doctest.DocTestParser()
    test = parser.get_doctest(doc, {}, name, None, 0)
    examples = [example for example in test.examples if "import" not in example.source]
    assert examples, f"{name} has no example beyond an import"
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    runner.run(test, clear_globs=True)
    assert runner.failures == 0, name
    return len(test.examples)


@pytest.mark.parametrize("cls", PUBLIC, ids=lambda cls: cls.__name__)
def test_every_public_class_has_a_passing_example(cls: type) -> None:
    assert _run(cls.__name__, cls.__doc__) >= 2


@pytest.mark.parametrize(("owner", "name", "member"), MEMBERS, ids=lambda x: str(x))
def test_every_public_method_has_a_passing_example(owner: str, name: str, member: object) -> None:
    assert _run(f"{owner}.{name}", inspect.getdoc(member)) >= 2


def test_the_module_docstring_names_the_package() -> None:
    assert typedmultidict.__doc__
    assert "multi-value" in typedmultidict.__doc__


def test_a_failing_example_is_reported() -> None:
    with pytest.raises(AssertionError):
        _run("broken", ">>> 1 + 1\n3\n")
