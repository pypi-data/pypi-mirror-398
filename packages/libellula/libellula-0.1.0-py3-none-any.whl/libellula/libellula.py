from collections.abc import Iterable, Callable
from collections import defaultdict
from functools import wraps
from inspect import signature


def argmax[T, V](it: Iterable[T], f: Callable[[T], V] = lambda x: x) -> int:
    """Return index of maximum element. Example: argmax([1, 5, 3]) → 1"""
    it = iter(it)
    try:
        best = 0
        val = f(next(it))
    except StopIteration:
        raise ValueError("argmax cannot be requested for an empty iterator")

    for i, elem in enumerate(it, start=1):
        new_val = f(elem)
        best, val = (i, new_val) if new_val > val else (best, val)

    return best


def group_by[T, V](it: Iterable[T], f: Callable[[T], V]) -> dict[V, list[T]]:
    """Group elements by key function. Example: group_by([1,2,3,4], lambda x: x % 2) → {1: [1,3], 0: [2,4]}"""
    it = list(it)
    groups: defaultdict[V, list[T]] = defaultdict(list)
    for elem in it:
        groups[f(elem)].append(elem)
    return dict(groups)


def flatmap[T, V](it: Iterable[T], f: Callable[[T], Iterable[V]]) -> Iterable[V]:
    """Map and flatten in one step. Example: flatmap([1,2,3], lambda x: [x, x*10]) → [1,10,2,20,3,30]"""
    for elem in it:
        yield from f(elem)


def flatten[T](it: Iterable[Iterable[T]]) -> Iterable[T]:
    """Flatten one level of nesting. Example: flatten([[1,2],[3,4]]) → [1,2,3,4]"""
    for elem in it:
        yield from elem


def get_only[T](it: Iterable[T]) -> T:
    """Extract single element, error if not exactly one. Example: get_only([42]) → 42"""
    lit: list[T] = list(it)
    if len(lit) != 1:
        raise ValueError("get_only cannot be requested for an empty iterator")
    return lit[0]


def get_any[T](it: Iterable[T]) -> T:
    """Return first element. Example: get_any([1,2,3]) → 1"""
    try:
        return next(iter(it))
    except StopIteration:
        raise ValueError("get_any cannot be requested for an empty iterator")


def argmin[T, V](it: Iterable[T], f: Callable[[T], V] = lambda x: x) -> int:
    """Return index of minimum element. Example: argmin([5, 1, 3]) → 1"""
    it = iter(it)
    try:
        best = 0
        val = f(next(it))
    except StopIteration:
        raise ValueError("argmin cannot be requested for an empty iterator")

    for i, elem in enumerate(it, start=1):
        new_val = f(elem)
        best, val = (i, new_val) if new_val < val else (best, val)

    return best


def compose[**P, R](*funcs: Callable) -> Callable[P, R]:
    """Compose functions right-to-left. Example: compose(lambda x: x+1, lambda x: x*2)(3) → 7"""
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        result = funcs[-1](*args, **kwargs)
        for func in reversed(funcs[:-1]):
            result = func(result)
        return result

    return inner


def batch[T](it: Iterable[T], n: int) -> Iterable[list[T]]:
    """Split iterable into fixed-size chunks. Example: batch([1,2,3,4,5], 2) → [[1,2],[3,4],[5]]"""
    if n < 1:
        raise ValueError("batch size must be at least 1")
    
    it = iter(it)
    while chunk := [elem for _, elem in zip(range(n), it)]:
        yield chunk


def compact[T](it: Iterable[T | None]) -> Iterable[T]:
    """Remove None values, keep all others. Example: compact([1, None, 2, None]) → [1, 2]"""
    for elem in it:
        if elem is not None:
            yield elem


def typecheck(func: Callable):
    """Decorator to validate function argument and return types at runtime."""
    sig = signature(func)

    @wraps(func)
    def inner(*args, **kwargs):
        binds = sig.bind(*args, **kwargs)
        binds.apply_defaults()
        for name, value in binds.arguments.items():
            tp = sig.parameters[name].annotation
            if not isinstance(value, tp):
                raise TypeError(
                    f"In function {func.__name__}, argument {name} has type {type(value)} but expected {tp}"
                )
        out = func(*args, **kwargs)
        if not isinstance(out, sig.return_annotation):
            raise TypeError(
                f"In function {func.__name__}, return value has type {type(out)} but expected {sig.return_annotation}"
            )
        return out

    return inner

