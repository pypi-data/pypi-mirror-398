import ast
import inspect
import linecache
import enum

from collections.abc import Callable
from typing import TypeVar, cast

from fp_cate.utils import pipe
from fp_cate.control.pattern_match import match, matchV, case, default


__all__ = ["MacroLevel", "macro"]


def _get_args_ast(frame_info: inspect.FrameInfo) -> ast.expr | list[ast.expr]:
    """
    Get the source code of the frame caller arguments

    ```py
    stack = inspect.stack()
    frame_info = stack[1]
    src = get_args_src(frame_info)
    ```
    """
    frame = frame_info.frame
    file = inspect.getsourcefile(frame)
    if not file:
        raise ValueError("Could not determine source file.")

    position = frame_info.positions
    if not (position and position.lineno and position.end_lineno):
        raise ValueError("Could not determine source code positions.")

    # get source code
    lines = map(
        lambda line: linecache.getline(file, line),
        range(position.lineno, position.end_lineno + 1),
    )
    lines = list(lines)
    if len(lines) > 1:
        lines[0] = lines[0][position.col_offset :]
        lines[-1] = lines[-1][: position.end_col_offset]
    else:
        # if only one line, slice once since col_offset and end_col_offset are relative to the same line
        lines[0] = lines[0][position.col_offset : position.end_col_offset]
    src = "".join(lines)

    # process AST
    ast_tree = ast.parse(src)
    expr = ast_tree.body[0]

    if not isinstance(expr, ast.Expr):
        raise ValueError("Could not get expression")

    expr = expr.value

    # TODO: currently only support Call and Subscript
    if isinstance(expr, ast.Call):
        return expr.args
    elif isinstance(expr, ast.Subscript):
        return expr.slice
    else:
        raise ValueError("Could not get arguments")


@enum.unique
class MacroLevel(enum.Enum):
    AST = 1
    STR = 2


# TODO: explicit typing for allowed arguments with type parameters list (>= 3.12)
def macro(*, level: MacroLevel = MacroLevel.AST):
    R = TypeVar("R")

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        def wrapper(*_, **__):
            stack = inspect.stack()
            frame_info = stack[1]
            args_ast = _get_args_ast(frame_info)

            # fmt: off
            args = pipe(
                level,
                match(
                    case(MacroLevel.AST) >> args_ast,
                    case(MacroLevel.STR) >> matchV(args_ast)(
                        case(lambda x: isinstance(x, list)) >> (lambda x: [ast.unparse(arg) for arg in x]),
                        default >> ast.unparse,
                    ),
                )
            )
            # fmt: on
            return func(args, frame_info.frame)

        return cast(Callable[..., R], wrapper)

    return decorator
