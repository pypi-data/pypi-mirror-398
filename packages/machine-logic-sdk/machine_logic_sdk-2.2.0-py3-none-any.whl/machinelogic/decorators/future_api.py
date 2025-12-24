import functools
from typing import Callable, TypeVar

from typing_extensions import ParamSpec

Params = ParamSpec("Params")
ReturnType = TypeVar("ReturnType")  # pylint: disable=invalid-name


def future_api(func: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
    """
    A decorator to mark methods that will be part of a future api.
    These method will be skipped by the documentation generation script.

    Args:
        func: The function to decorate

    Returns:
        The decorator
    """

    @functools.wraps(func)
    def decorator(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
        return func(*args, **kwargs)

    decorator.__future_api__ = True  # type: ignore

    return decorator
