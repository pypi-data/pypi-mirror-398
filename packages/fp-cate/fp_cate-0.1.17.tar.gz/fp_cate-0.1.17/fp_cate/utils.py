from collections.abc import Callable
from functools import partial, reduce
from inspect import _empty, signature
from typing import TypeVar, overload

__all__ = [
    "identity",
    "assert_and",
    "expr",
    "compose",
    "curry",
    "pipe",
    "dbg",
    "flip",
    "Filter",
    "State",
]


def identity(x):
    return x


T = TypeVar("T")


def assert_and(cond: bool, expr: T, msg: str | None = "Assertion failed") -> T:
    """Works like assert but returns expr when cond is True"""
    assert cond, msg
    return expr


def expr(*args):
    """Evaluates and returns the last argument"""
    return args[-1]


def compose(*funcs):
    """Composes multiple functions into a single function"""
    return reduce(lambda f, g: lambda x: f(g(x)), funcs, identity)


# from https://stackoverflow.com/a/78149460
# TODO: since it uses inspect, it doesn't work with built-in functions
def curry(f):
    def inner(*args, **kwds):
        new_f = partial(f, *args, **kwds)
        params = signature(new_f, follow_wrapped=True).parameters
        if all(params[p].default != _empty for p in params):
            return new_f()
        else:
            return curry(new_f)

    return inner


def pipe(value, *funcs):
    return reduce(lambda v, f: f(v), funcs, value)


@overload
def dbg(value: T, *, formatter: Callable[[T], str]) -> T: ...


@overload
def dbg(msg: str, value: T, *, formatter: Callable[[T], str]) -> T: ...


def dbg(msg_or_value, value=None, *, formatter=identity):  # type: ignore
    if value is None:
        value = msg_or_value
        print(f"{formatter(value)}")
        return value
    else:
        msg = msg_or_value
        print(f"{msg} {formatter(value)}")
        return value


U = TypeVar("U")
V = TypeVar("V")


def flip(f: Callable[[U, V], T]) -> Callable[[V, U], T]:
    return lambda x, y: f(y, x)


class Filter:
    def __init__(self, func):
        self.func = func

    def __rmatmul__(self, iterable):
        return type(iterable)(filter(self.func, iterable))


class State:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def update(self, **kwargs) -> "State":
        new_state = self.__dict__.copy()
        return State(**{**new_state, **kwargs})

    def __repr__(self):
        return (
            "Ctx {\n"
            + "\n".join(f"  {k}={v}" for k, v in self.__dict__.items())
            + "\n}"
        )
