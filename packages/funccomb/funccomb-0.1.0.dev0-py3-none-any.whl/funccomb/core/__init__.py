import functools
from types import FunctionType
from typing import *

__all__ = ["funccomb"]


def funccomb(
    outer: Callable,
    *args: Callable,
    **kwargs: Callable,
) -> FunctionType:
    @functools.wraps(outer)
    def ans(*args_: Any, **kwargs_: Any) -> Any:
        i: int
        s: str
        x: Any
        y: Any
        args__: list
        kwargs__: dict[str, Any]
        args__ = list()
        for i, y in enumerate(args_):
            args__.append(args[i](y))
        for i in range(len(args_), len(args)):
            args__.append(args[i]())
        kwargs__ = dict()
        for x, y in kwargs_.items():
            s = str(x)
            kwargs__[s] = kwargs[s](y)
        for x in kwargs.keys():
            s = str(x)
            if s in kwargs__.keys():
                continue
            kwargs__[s] = kwargs[s]()
        return outer(*args__, **kwargs__)

    return ans
