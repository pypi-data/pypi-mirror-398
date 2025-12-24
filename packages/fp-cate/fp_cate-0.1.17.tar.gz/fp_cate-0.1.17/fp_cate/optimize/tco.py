__all__ = ["TailCall", "tco"]


class TailCall:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def tco(func):
    """
    Tail Call Optimization decorator.
    Makes a function support tail call optimization by using the `TailCall` class.

    Example:
    ```py
    fib = tco(lambda n, acc=1: 1 if n <= 2 else TailCall(n - 1, acc + n))
    ```
    """

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        while isinstance(result, TailCall):
            result = func(*result.args, **result.kwargs)
        return result

    return wrapper
