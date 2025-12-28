from __future__ import annotations

from . import StructMeta


def is_struct(obj: object) -> bool:
    """Check whether ``obj`` is a `hyperspec.Struct`-like instance.

    Parameters
    ----------
    obj:
        Object to check.

    Returns
    -------
    bool
        `True` if ``obj`` is an instance of a class whose metaclass is
        `hyperspec.StructMeta` (or a subclass of it), and `False` otherwise.
        Static type checkers treat a successful ``is_struct(obj)`` check as
        narrowing ``obj`` to `hyperspec.Struct` within the true branch, even if
        the runtime class does not literally inherit `hyperspec.Struct`.
    """
    return isinstance(type(obj), StructMeta)


def is_struct_type(tp: object) -> bool:
    """Check whether ``tp`` is a `hyperspec.Struct`-like class.

    Parameters
    ----------
    tp:
        Object to check, typically a class object.

    Returns
    -------
    bool
        `True` if ``tp`` is a class whose metaclass is `hyperspec.StructMeta`
        (or a subclass of it), and `False` otherwise. Static type checkers
        treat a successful ``is_struct_type(tp)`` check as narrowing
        ``tp`` to `type[hyperspec.Struct]` within the true branch.
    """
    return isinstance(tp, StructMeta)
