from abc import ABC
from collections.abc import Callable
from functools import singledispatch
from typing import NoReturn
from typing_extensions import Unpack

__all__ = [
    "_not_implemented",
    "create_cate",
]


def _not_implemented(cate: str, t: type) -> NoReturn:
    raise NotImplementedError(f"{cate} not implemented for type {t}")


def create_cate(
    cate_name: str, *methods: str
) -> tuple[type, Unpack[tuple[Callable, ...]]]:
    class _Internal(ABC): ...

    _Internal.__name__ = cate_name

    registers = []
    reg_dict = {}
    for mname in methods:
        _cate_func = lambda *args: _not_implemented(mname, type(args[0]))  # noqa: E731
        _cate_func.__name__ = f"_{mname}"
        cate_func = singledispatch(_cate_func)

        registers.append(cate_func)
        reg_dict[mname] = cate_func

    def register_cate(t: type, /, **method_impls: Callable) -> None:
        _Internal.register(t)
        for mname, impl in method_impls.items():
            reg_dict[mname].register(t, impl)

    return (_Internal, register_cate, *registers)
