import functools
import warnings
from typing import Any, Callable, Optional, TypeVar

from typing_extensions import ParamSpec

Params = ParamSpec("Params")
ReturnType = TypeVar("ReturnType")  # pylint: disable=invalid-name


class deprecated_property(property):  # pylint: disable=invalid-name
    """
    A decorator to mark property methods that are deprecated.

    This decorator is meant to be used in place of '@property', if
    it's meant to be deprecated.

    Note that the `deprecated` decorator works only on functions and
    doesn't work on top of the `@property` decorator.
    """

    __deprecated__ = True

    def __init__(self, fget: Callable[Params, ReturnType]) -> None:
        super().__init__(fget)
        self._fget = fget

    def __get__(self, instance: Any, owner: Optional[type] = None) -> Any:
        warnings.warn(
            f"{self._fget.__name__} is deprecated and will be removed in a future version.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return super().__get__(instance, owner)


def deprecated(func: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
    """
    A decorator to mark methods as deprecated.
    It will raise a warning when the decorated function is called.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """

    @functools.wraps(func)
    def decorator(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
        warnings.warn(
            f"{func.__name__} is deprecated and will be removed in a future version.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    decorator.__deprecated__ = True  # type: ignore

    return decorator
