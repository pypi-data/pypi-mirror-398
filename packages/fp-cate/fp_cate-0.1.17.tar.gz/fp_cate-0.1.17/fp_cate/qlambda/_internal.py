from collections.abc import Callable
from typing import Any

__all__ = ["_1", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9"]


def _proc_o(o, args):
    return o(*args) if isinstance(o, _Placeholder) else o


class _Placeholder:
    __slots__ = ("_expr",)

    def __init__(self, expr: Callable):
        self._expr = expr

    def __call__(self, *args: Any):
        return self._expr(*args)

    def __add__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) + _proc_o(o, args))

    def __radd__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) + self(*args))

    def __sub__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) - _proc_o(o, args))

    def __rsub__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) - self(*args))

    def __mul__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) * _proc_o(o, args))

    def __rmul__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) * self(*args))

    def __contains__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) in self(*args))

    def __truediv__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) / _proc_o(o, args))

    def __rtruediv__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) / self(*args))

    def __floordiv__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) // _proc_o(o, args))

    def __rfloordiv__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) // self(*args))

    def __and__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) & _proc_o(o, args))

    def __rand__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) & self(*args))

    def __xor__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) ^ _proc_o(o, args))

    def __rxor__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) ^ self(*args))

    def __invert__(self) -> "_Placeholder":
        return _Placeholder(lambda *args: ~self(*args))

    def __or__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) | _proc_o(o, args))

    def __ror__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) | self(*args))

    def __pow__(self, o: Any, modulo: Any = None) -> "_Placeholder":
        return _Placeholder(lambda *args: pow(self(*args), _proc_o(o, args), modulo))

    def __rpow__(self, o: Any, modulo: Any = None) -> "_Placeholder":
        return _Placeholder(lambda *args: pow(_proc_o(o, args), self(*args), modulo))

    def __getitem__(self, key: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args)[_proc_o(key, args)])

    def __lshift__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) << _proc_o(o, args))

    def __rlshift__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) << self(*args))

    def __rshift__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) >> _proc_o(o, args))

    def __rrshift__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) >> self(*args))

    def __mod__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) % _proc_o(o, args))

    def __rmod__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) % self(*args))

    def __matmul__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) @ _proc_o(o, args))

    def __rmatmul__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: _proc_o(o, args) @ self(*args))

    def __neg__(self) -> "_Placeholder":
        return _Placeholder(lambda *args: -self(*args))

    def __not__(self) -> "_Placeholder":
        return _Placeholder(lambda *args: not self(*args))

    def __pos__(self) -> "_Placeholder":
        return _Placeholder(lambda *args: +self(*args))

    def __abs__(self) -> "_Placeholder":
        return _Placeholder(lambda *args: abs(self(*args)))

    def __lt__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) < _proc_o(o, args))

    def __le__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) <= _proc_o(o, args))

    def __eq__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, o: Any
    ) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) == _proc_o(o, args))

    def __ne__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, o: Any
    ) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) != _proc_o(o, args))

    def __gt__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) > _proc_o(o, args))

    def __ge__(self, o: Any) -> "_Placeholder":
        return _Placeholder(lambda *args: self(*args) >= _proc_o(o, args))

    def __repr__(self) -> str:
        return f"<Placeholder {hex(id(self))}>"


# lambda *args, i=i: args[i] here i is captured by default argument
# so that a copy is created
_1, _2, _3, _4, _5, _6, _7, _8, _9 = [
    _Placeholder(lambda *args, i=i: args[i]) for i in range(0, 9)
]
