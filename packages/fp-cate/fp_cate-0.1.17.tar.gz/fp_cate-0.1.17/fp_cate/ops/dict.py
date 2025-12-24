"""
Functional style wrappers for dict operations that allow for in-place or out-of-place modifications.
"""

from typing import TypeVar

__all__ = ["insert", "remove", "update"]

K = TypeVar("K")
V = TypeVar("V")

_inplace_dict = lambda d, inplace=False: d if inplace else d.copy()  # noqa: E731


def insert(d: dict[K, V], key: K, value: V, inplace=False) -> dict[K, V]:
    d = _inplace_dict(d, inplace)
    d[key] = value
    return d


def remove(d: dict[K, V], key: K, inplace=False) -> dict[K, V]:
    d = _inplace_dict(d, inplace)
    d.pop(key, None)
    return d


def update(d: dict[K, V], other: dict[K, V], inplace=False) -> dict[K, V]:
    d = _inplace_dict(d, inplace)
    d.update(other)
    return d
