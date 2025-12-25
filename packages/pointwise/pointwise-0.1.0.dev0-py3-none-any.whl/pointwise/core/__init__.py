import functools
from types import FunctionType
from typing import *

__all__ = ["pointwise"]


def pointwise(
    outer: Callable,
    *args: Callable,
    **kwargs: Callable,
) -> FunctionType:
    @functools.wraps(outer)
    def ans(*args_: Any, **kwargs_: Any) -> Any:
        x: Any
        y: Any
        args__: list
        kwargs__: dict[str, Any]
        args__ = list()
        for y in args:
            args__.append(y(*args_, **kwargs_))
        kwargs__ = dict()
        for x, y in kwargs.items():
            kwargs__[x] = y(*args_, **kwargs_)
        return outer(*args__, **kwargs__)

    return ans
