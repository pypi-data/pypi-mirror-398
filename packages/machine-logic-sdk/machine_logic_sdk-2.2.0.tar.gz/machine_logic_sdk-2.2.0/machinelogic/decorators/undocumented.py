import functools
from typing import Any, Callable, Optional, TypeVar

from typing_extensions import ParamSpec

Params = ParamSpec("Params")
ReturnType = TypeVar("ReturnType")  # pylint: disable=invalid-name


class undocumented_property(property):  # pylint: disable=invalid-name
    """
    A decorator to mark property methods that will not be documented.
    These getters will be skipped by the documentation generation script.

    This decorator is meant to be used in place of '@property', if
    it's meant to be undocumented.

    Note that the `undocumented` decorator works only on functions and
    doesn't work on top of the `@property` decorator.
    """

    __undocumented__ = True

    def __init__(self, fget: Callable[Params, ReturnType]) -> None:
        super().__init__(fget)

    def __get__(self, instance: Any, owner: Optional[type] = None) -> Any:
        return super().__get__(instance, owner)


def undocumented(func: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
    """
    A decorator to mark methods that will never be documented.
    These method will be skipped by the documentation generation script.

    Args:
        func: The function to decorate.

    Returns:
        The decorator.
    """

    @functools.wraps(func)
    def decorator(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
        return func(*args, **kwargs)

    decorator.__undocumented__ = True  # type: ignore

    return decorator
