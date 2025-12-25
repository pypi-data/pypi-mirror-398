import functools
import inspect
import types
from typing import *

__all__ = ["funccomp"]


def funccomp(
    outmost: Callable,
    *inners: Callable,
) -> types.FunctionType:
    funcs: tuple[Callable]
    funcs = (outmost,) + inners

    @functools.wraps(outmost)
    def ans(*args: Any, **kwargs: Any) -> Any:
        ans_: Any
        func: Callable
        ans_ = funcs[-1](*args, **kwargs)
        for func in funcs[-2::-1]:
            ans_ = func(ans_)
        return ans_

    return ans
