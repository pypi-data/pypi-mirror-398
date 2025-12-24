"""
Functional style wrappers for list operations that allow for in-place or out-of-place modifications.
"""

from typing import TypeVar

__all__ = ["insert", "remove", "append", "extend", "swap"]


T = TypeVar("T")


_inplace_list = lambda arr, inplace: arr if inplace else arr[:]  # noqa: E731


def insert(arr: list[T], index: int, value: T, inplace=False) -> list[T]:
    arr = _inplace_list(arr, inplace)
    arr.insert(index, value)
    return arr


def update(arr: list[T], index: int, value: T, inplace=False) -> list[T]:
    arr = _inplace_list(arr, inplace)
    arr[index] = value
    return arr


def remove(arr: list[T], index: int, inplace=False) -> list[T]:
    """Remove the element at the specified index from the list."""
    arr = _inplace_list(arr, inplace)
    arr.pop(index)
    return arr


def append(arr: list[T], value: T, inplace=False) -> list[T]:
    arr = _inplace_list(arr, inplace)
    arr.append(value)
    return arr


def extend(arr: list[T], values: list[T], inplace=False) -> list[T]:
    arr = _inplace_list(arr, inplace)
    arr.extend(values)
    return arr


def swap(arr: list[T], i: int, j: int, inplace=False) -> list[T]:
    """Swap the elements at index i and j in the list."""
    arr = _inplace_list(arr, inplace)
    arr[i], arr[j] = arr[j], arr[i]
    return arr
