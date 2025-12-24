"""
Example of pattern matching.

```py
# works with any iterables
a = "test"
print(
    matchV(a)(
        case("tes") >> (lambda x: "one"),
        case(["a", _rest]) >> (lambda x, xs: f"list starts with a, rest is {xs}"),
        default >> "good",
    )
)
# works with dicts
pipe(
    {"test": 1, "other": 2},
    match(
        case({"test": _any}) >> (lambda x: f"test is {x}"),
        case({"other": 2}) >> (lambda x: "other two"),
    ),
    print,
)

# works with dataclasses as well
@dataclass
class Test:
    a: int
    b: bool
pipe(
    Test(1, True),
    match(
        case({"a": 1}) >> "this is a good match",
        case({"b": False}) >> "this won't match",
        default >> "all other matches failed",
    ),
    print,
)
```
"""

from collections.abc import Callable, Iterable
from typing import Any

__all__ = ["case", "default", "matchV", "match", "switch", "_any", "_rest"]


# special symbols for pattern matching
_any = lambda *_: True  # noqa: E731
_rest = object()


class _InternalMatchError(Exception): ...


def _get_obj_property(obj: Any, key: str) -> Any:
    try:
        try:
            return obj[key]
        except (KeyError, TypeError):
            return getattr(obj, key)
    except AttributeError:
        raise _InternalMatchError()


class case:
    def __init__(self, pattern: Any, expr: Callable | Any | None = None):
        self._pattern = pattern
        self.expr: Callable = expr if callable(expr) else (lambda *_: expr)

    def __rshift__(self, expr: Callable | Any):
        self.expr = expr if callable(expr) else (lambda *_: expr)
        return self

    def match(self, value: Any) -> tuple | bool:
        return self._match(self._pattern, value)

    def _match(self, pattern: Any, value: Any) -> tuple | bool:
        if isinstance(pattern, dict) and self._match_dict(pattern, value):
            # match itemgetter or object property with dict
            return True
        elif isinstance(pattern, list) and isinstance(value, Iterable):
            # match iterable with list
            if (res := self._match_iter(pattern, value)) is not False:
                return res
        elif callable(pattern):
            # pattern is a predicate function
            res = pattern(value)
            if isinstance(res, bool) and res:
                return True
            elif isinstance(res, tuple):
                return res

        return pattern == value

    def _match_dict(self, pattern: dict, value: Any) -> bool:
        """use dict to match properties of an object"""
        keys = pattern.keys()
        try:
            if all(self._match(pattern[k], _get_obj_property(value, k)) for k in keys):
                return True
        except _InternalMatchError:
            pass

        return False

    def _match_iter(self, pattern: list, value: Iterable) -> tuple | bool:
        """use list to match elements of an iterable"""
        res = ()

        v_list = list(value)

        if len(pattern) > len(v_list):
            # pattern longer than value, directly fail
            return False

        for p, v in zip(pattern, value):
            if p is _rest:
                res += (v_list[len(res) :],)
                return res
            m = self._match(p, v)
            if m is False:
                return False

            # discard nested tuples for simplicity of usage now
            # res += (m,) if isinstance(m, tuple) else (v,)
            res += (v,)

        return res


default = case(_any)


def _match(value: Any, cases: Iterable[case]) -> Any:
    for c in cases:
        if (res := c.match(value)) is not False:
            return c.expr(*res) if isinstance(res, tuple) else c.expr(value)
    raise ValueError("no matching case found")


def matchV(value: Any):
    return lambda *args: _match(value, args)


switch = matchV(...)
"""
Simplified version of matchV for switch-case style usage.
"""


def match(*cases: case) -> Callable[[Any], Any]:
    return lambda v: _match(v, cases)
