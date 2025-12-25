import inspect
import types
import unittest
from types import FunctionType
from typing import *

from funccomp.core import funccomp

__all__ = ["funccomp"]


def _double(x: int) -> int:
    return 2 * x


def _increment(x: int) -> int:
    return x + 1


def _square(x: int) -> int:
    return x * x


def _pack(*args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
    return args, kwargs


def _count_args_kwargs(packed: tuple[tuple[Any, ...], dict[str, Any]]) -> int:
    args, kwargs = packed
    return len(args) + len(kwargs)


class FuncCompTests(unittest.TestCase):
    def test_single_function_behaves_like_outmost(self) -> None:
        def out(x: int) -> int:
            return x * 10

        f: FunctionType

        f = funccomp(out)
        self.assertEqual(f(3), out(3))
        self.assertEqual(f(0), out(0))

    def test_simple_composition_order(self) -> None:
        # f(x) = square(double(increment(x))) = (2 * (x + 1)) ** 2
        f: FunctionType
        f = funccomp(_square, _double, _increment)
        self.assertEqual(f(3), (2 * (3 + 1)) ** 2)  # 64
        self.assertEqual(f(0), (2 * (0 + 1)) ** 2)  # 4

    def test_args_and_kwargs_passed_only_to_innermost(self) -> None:
        # innermost(_pack) receives args/kwargs; others receive previous result
        f: FunctionType
        f = funccomp(_count_args_kwargs, _pack)
        self.assertEqual(f(1, 2, a=3), 3)
        self.assertEqual(f(), 0)

    def test_metadata_copied_from_outmost(self) -> None:
        def out(x: int, y: str = "a") -> bool:
            """example docstring"""
            return bool(x and y)

        f: FunctionType
        f = funccomp(out)

        self.assertEqual(f.__name__, out.__name__)
        self.assertEqual(f.__doc__, out.__doc__)
        self.assertEqual(f.__module__, out.__module__)
        # signature should look like the outmost's thanks to functools.wraps
        self.assertEqual(inspect.signature(f), inspect.signature(out))

    def test_returns_function_type(self) -> None:
        f: FunctionType
        f = funccomp(_square, _increment)
        self.assertIsInstance(f, types.FunctionType)

    def test_exception_propagation_from_innermost(self) -> None:
        def inner(_: Any) -> Any:
            raise ValueError("boom")

        def out(x: Any) -> Any:
            return x

        f: FunctionType
        f = funccomp(out, inner)

        with self.assertRaises(ValueError):
            f(10)

    def test_exception_propagation_from_outer(self) -> None:
        def inner(x: int) -> int:
            return x + 1

        def out(_: Any) -> Any:
            raise RuntimeError("outer failed")

        f: FunctionType

        f = funccomp(out, inner)

        with self.assertRaises(RuntimeError):
            f(1)


if __name__ == "__main__":
    unittest.main()
