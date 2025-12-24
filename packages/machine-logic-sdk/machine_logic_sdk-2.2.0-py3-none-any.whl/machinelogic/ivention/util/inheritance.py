# type: ignore
"""Inheritance utiltiies"""

from inspect import getmembers, isfunction


def is_an_object_to_generate_documentation(obj):
    """
    Predicate to check if an object should be documented.

    Args:
        obj: The object to check
    """
    return isfunction(obj) or isinstance(obj, property)


def inherit_docstrings(cls):
    """Inherit docstrings. Intended to be used as a decorator

    Returns:
        The class with docstrings inherited
    """
    cls.__doc__ = ""
    for parent in cls.__mro__[1:]:
        cls.__doc__ += parent.__doc__
        break  # Only get the first docstrings

    for name, func in getmembers(cls, is_an_object_to_generate_documentation):
        if func.__doc__:
            continue
        for parent in cls.__mro__[1:]:
            if hasattr(parent, name):
                func.__doc__ = getattr(parent, name).__doc__
    return cls
