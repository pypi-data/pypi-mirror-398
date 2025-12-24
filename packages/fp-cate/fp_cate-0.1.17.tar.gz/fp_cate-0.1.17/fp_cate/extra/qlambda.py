import ast

from types import FrameType
from typing import Any

from .macro import macro, MacroLevel
from ._internal.placeholder import __Placeholder

__all__ = ["f", "_", "_1", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9"]


class __f:
    @staticmethod
    @macro(level=MacroLevel.AST)
    def __getitem__(args_src: ast.expr, frame: FrameType):
        placeholders = set()
        for node in ast.walk(args_src):
            if isinstance(node, ast.Name) and node.id in [
                "_",
                *(f"_{i}" for i in range(1, 10)),
            ]:
                placeholders.add(node.id)

        if "_" in placeholders and placeholders - {"_"}:
            raise ValueError(
                "A quick lambda should use either _ or _1, _2, ..., but not both."
            )

        if "_" in placeholders:
            args = ["_"]
        else:
            args = sorted(placeholders, key=lambda x: int(x[1:]))

        args = map(lambda x: ast.arg(arg=x, annotation=None), args)
        ast_func = ast.Lambda(
            args=ast.arguments(
                list(args), [], kwonlyargs=[], kw_defaults=[], defaults=[]
            ),
            body=args_src,
        )
        return eval(
            ast.unparse(ast_func),
            frame.f_globals,
            frame.f_locals,
        )


f = __f()
"""
```py
# one argument
func = f[_ + 1]  # equivalent to: func = lambda _: _ + 1
# multiple arguments
func = f[_1 + _2 + _3]  # equivalent to: func = lambda _1, _2, _3: _1 + _2 + _3
```
"""


_: Any = __Placeholder()
_1, _2, _3, _4, _5, _6, _7, _8, _9 = [_] * 9
