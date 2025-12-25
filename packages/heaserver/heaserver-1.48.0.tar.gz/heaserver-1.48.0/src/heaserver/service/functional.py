from functools import reduce, partial
from typing import Tuple, Callable, TypeVar


T = TypeVar('T')


def compose(*functions: Callable[[T], T]) -> Callable[[T], T]:
    """
    Returns the composition of the given functions. Each function must take only one argument.

    The composition of N functions f1, f2, f3, ..., fN-1, fN is f1(f2(f3(...fN-1(fN(x))...))).

    For example, the function ``func`` below adds 10 to the given number and then multiplies the result by 10
    (i.e. it's equivalent to f(x) = (x + 10) * 2):
    >>> func = compose(lambda x: x * 2, lambda y: y + 10)
    >>> func(1)
    22
    >>> func(-5)
    10
    """
    def compose2(f, g):
        return lambda x: f(g(x))
    return reduce(compose2, functions, lambda x: x)
