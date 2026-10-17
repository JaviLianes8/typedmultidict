"""Pickling and copying state: plain pairs plus whatever a subclass adds."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._storage import _Storage

# Rebuilt from the pairs, never copied as they are.
_OWN = frozenset({"_entries", "_holes", "_index", "_version"})


def state_of(obj: _Storage[Any, Any]) -> tuple[Any, ...]:
    """The pairs, the instance attributes and any subclass slots, in that order."""
    pairs = [(entry.key, entry.value) for entry in obj._live()]
    attrs = {name: value for name, value in vars(obj).items() if name not in _OWN}
    slots = {name: getattr(obj, name) for name in _slot_names(type(obj)) if hasattr(obj, name)}
    return pairs, attrs or None, slots or None


def restore(obj: _Storage[Any, Any], state: Any) -> None:
    """Fill an object made with ``__new__`` from ``state_of`` output or a 0.1.0 pickle."""
    if isinstance(state, dict):
        # 0.1.0 pickled the instance dictionary, with every pair under "_items".
        attrs = {name: value for name, value in state.items() if name != "_items"}
        pairs, slots = state.get("_items", []), None
    else:
        pairs, attrs, slots = state
    vars(obj).update(attrs or {})
    for name, value in (slots or {}).items():
        object.__setattr__(obj, name, value)
    # Attributes first: a subclass may need them to normalise its keys.
    obj._setup()
    obj._append([(obj._token(key), key, value) for key, value in pairs])


def _slot_names(cls: type) -> list[str]:
    names: list[str] = []
    for klass in cls.__mro__:
        declared = klass.__dict__.get("__slots__", ())
        for name in [declared] if isinstance(declared, str) else declared:
            if name in ("__dict__", "__weakref__"):
                continue
            if name.startswith("__") and not name.endswith("__"):
                name = f"_{klass.__name__.lstrip('_')}{name}"
            names.append(name)
    return names
