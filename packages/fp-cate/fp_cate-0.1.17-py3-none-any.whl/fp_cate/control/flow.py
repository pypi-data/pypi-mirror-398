"""
Functional style control flow
"""

from collections.abc import Callable
from typing import TypeVar


__all__ = ["Break", "While"]


class _Break: ...


Break = _Break()


T = TypeVar("T")


def While(func: Callable[[T], T | _Break], initial: T) -> T:
    prev = initial
    while not isinstance(res := func(prev), _Break):
        prev = res
    return prev
