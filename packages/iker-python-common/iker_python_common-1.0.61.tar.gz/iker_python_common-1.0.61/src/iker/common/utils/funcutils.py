import functools
from collections.abc import Callable
from typing import Any, Protocol

__all__ = [
    "const",
    "first",
    "second",
    "packed",
    "identity",
    "composable",
    "singleton",
    "memorized",
    "lazy",
    "unique_returns",
]


def const[T](value: T) -> Callable[..., T]:
    """
    Returns a function that always returns the specified ``value``, regardless of the input arguments.

    :param value: The constant value to return.
    :return: A function that takes any arguments and returns ``value``.
    """

    def getter(*args: Any, **kwargs: Any) -> T:
        return value

    return getter


def first[K]() -> Callable[[tuple[K, Any]], K]:
    """
    Returns a function that extracts the first element (key) from a 2-tuple.

    :return: A function that takes a 2-tuple and returns its first element.
    """

    def getter(item: tuple[K, Any]) -> K:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("item must be a 2-tuple")
        return item[0]

    return getter


def second[V]() -> Callable[[tuple[Any, V]], V]:
    """
    Returns a function that extracts the second element (value) from a 2-tuple.

    :return: A function that takes a 2-tuple and returns its second element.
    """

    def getter(item: tuple[Any, V]) -> V:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("item must be a 2-tuple")
        return item[1]

    return getter


def packed[R](func: Callable[..., R]) -> Callable[[tuple[Any, ...]], R]:
    """
    Wraps a function to accept its arguments as a single tuple, unpacking them when called. This is useful for
    scenarios where arguments are naturally grouped in tuples, such as when working with data structures like maps or
    lists of tuples, or when interfacing with APIs that provide arguments in tuple form.

    >>> data = [(1, 2), (3, 4), (5, 6)]
    >>> sums = map(packed(lambda x, y: x + y), data)

    :param func: The function to wrap.
    :return: A function that takes a tuple of arguments and calls the original function with them unpacked.
    """

    @functools.wraps(func)
    def wrapper(args: tuple[Any, ...]) -> R:
        return func(*args)

    return wrapper


def identity[T](instance: T) -> T:
    """
    Returns the input ``instance`` unchanged. This is a utility function often used as a default or placeholder.

    :param instance: The value to return.
    :return: The same value as provided in ``instance``.
    """
    return instance


class Composable[T, R](Protocol):
    """
    Protocol for composable callables, supporting composition and chaining with other callables.
    """

    def __call__(self, x: T) -> R: ...

    def compose[U](self, func: "Callable[[U], T] | Composable[U, T]") -> "Composable[U, R]": ...

    def and_then[U](self, func: "Callable[[R], U] | Composable[R, U]") -> "Composable[T, U]": ...


def composable[T, R](func: Callable[[T], R]) -> Composable[T, R]:
    """
    Wraps a function to make it composable, allowing chaining with compose and and_then methods.

    :param func: The function to wrap as composable.
    :return: A composable version of the function.
    """

    def compose[U](another_func: Callable[[U], T] | Composable[U, T]) -> Composable[U, R]:
        def chained(x: U) -> R:
            return func(another_func(x))

        return composable(chained)

    def and_then[U](another_func: Callable[[R], U] | Composable[R, U]) -> Composable[T, U]:
        def chained(x: T) -> U:
            return another_func(func(x))

        return composable(chained)

    func.compose = compose
    func.and_then = and_then
    return func


def singleton[R](tar: Callable[..., R] = None):
    """
    Decorator to ensure a function or class is only instantiated once. Subsequent calls return the same instance.

    :param tar: The target callable to decorate.
    :return: The singleton instance of the callable.
    """

    def decorator(target):
        if not callable(target):
            raise TypeError("expected a callable")

        instance = {}

        @functools.wraps(target)
        def wrapper(*args, **kwargs):
            if target not in instance:
                instance[target] = target(*args, **kwargs)
            return instance[target]

        return wrapper

    return decorator if tar is None else decorator(tar)


def memorized[R](tar: Callable[..., R] = None, *, ordered: bool = False, typed: bool = False):
    """
    Decorator to cache the results of a function based on its arguments. Supports options for argument order and type.

    :param tar: The target callable to decorate.
    :param ordered: If ``True``, keyword argument order is significant in the cache key.
    :param typed: If ``True``, argument types are included in the cache key.
    :return: The decorated function with memoization.
    """

    def decorator(target):
        if not callable(target):
            raise TypeError("expected a callable")

        memory = {}

        def make_key(*args, **kwargs):
            if typed:
                arg_hashes = list(hash(arg) for arg in args)
            else:
                arg_hashes = list(hash((arg, type(arg))) for arg in args)
            if ordered and typed:
                kwarg_hashes = list(hash((k, v, type(v))) for k, v in kwargs.items())
            elif ordered:
                kwarg_hashes = list(hash((k, v)) for k, v in kwargs.items())
            elif typed:
                kwarg_hashes = list(hash((k, v, type(v))) for k, v in sorted(kwargs.items()))
            else:
                kwarg_hashes = list(hash((k, v)) for k, v in sorted(kwargs.items()))
            return hash(tuple(arg_hashes + kwarg_hashes))

        @functools.wraps(target)
        def wrapper(*args, **kwargs):
            hash_key = make_key(*args, **kwargs)
            if hash_key not in memory:
                memory[hash_key] = target(*args, **kwargs)
            return memory[hash_key]

        return wrapper

    return decorator if tar is None else decorator(tar)


def lazy[R](tar: Callable[..., R] = None):
    """
    Decorator to defer the execution of a function until its result is explicitly requested.

    :param tar: The target callable to decorate.
    :return: A function that returns a callable to execute the original function.
    """

    def decorator(target):
        if not callable(target):
            raise TypeError("expected a callable")

        @functools.wraps(target)
        def wrapper(*args, **kwargs):
            return lambda: target(*args, **kwargs)

        return wrapper

    return decorator if tar is None else decorator(tar)


def unique_returns[R](tar: Callable[..., R] = None, *, max_trials: int | None = None):
    """
    Decorator to ensure a function produces unique return values. If no unique value is found within max_trials,
    raises an error.

    :param tar: The target callable to decorate.
    :param max_trials: The maximum number of attempts to find a unique return value. If ``None``,
    attempts are unlimited.
    :return: The decorated function that ensures unique return values.
    """

    def decorator(target):
        if not callable(target):
            raise TypeError("expected a callable")

        seen = set()

        @functools.wraps(target)
        def wrapper(*args, **kwargs):
            trials = 0
            while max_trials is None or trials < max_trials:
                result = target(*args, **kwargs)
                if result not in seen:
                    seen.add(result)
                    return result
                trials += 1

            raise ValueError("no unique return value found")

        return wrapper

    return decorator if tar is None else decorator(tar)
