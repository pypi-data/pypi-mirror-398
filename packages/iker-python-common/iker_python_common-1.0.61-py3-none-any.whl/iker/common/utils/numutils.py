import math
from collections.abc import Callable, Sequence
from decimal import Decimal
from numbers import Real
from typing import Any

import numpy as np

__all__ = [
    "to_decimal",
    "is_nan",
    "is_real",
    "is_normal_real",
    "real_abs",
    "real_greater",
    "real_smaller",
    "real_max",
    "real_min",
    "real_mean",
    "real_std",
    "real_nan_greater",
    "real_nan_smaller",
    "real_nan_max",
    "real_nan_min",
    "real_nan_mean",
    "real_nan_std",
]


def to_decimal(x: float | str | None) -> Decimal | None:
    """
    Converts a float or string to a ``Decimal``, or returns ``None`` if the input is ``None``.

    :param x: The value to convert, as a float, string, or ``None``.
    :return: The ``Decimal`` representation of ``x``, or ``None`` if ``x`` is ``None``.
    """
    return None if x is None else Decimal(str(x))


def is_nan(v: Any) -> bool | None:
    """
    Checks if the given value is ``NaN`` (not a number).

    :param v: The value to check.
    :return: ``True`` if ``v`` is ``NaN``, ``False`` if not, or ``None`` if the check is not applicable.
    """
    try:
        return math.isnan(v)
    except TypeError:
        return None


def is_real(v: Any) -> bool:
    """
    Checks if the given value is a real number (an instance of ``numbers.Real``).

    :param v: The value to check.
    :return: ``True`` if ``v`` is a real number, ``False`` otherwise.
    """
    return isinstance(v, Real)


def is_normal_real(v: Any) -> bool:
    """
    Checks if the value is a real number and is neither ``NaN`` nor infinite.

    :param v: The value to check.
    :return: ``True`` if ``v`` is a normal real number, ``False`` otherwise.
    """
    return is_real(v) and not math.isnan(v) and not math.isinf(v)


def make_real_unary[T: Real](op: Callable[[T], T], fb: T | None = None) -> Callable[[T], T | None]:
    """
    Creates a unary function that applies the given operation to a real number, returning a fallback if not real.

    :param op: The unary operation to apply.
    :param fb: The fallback value to return if input is not real.
    :return: A function that applies ``op`` to a real number or returns ``fb``.
    """

    def func(x: T) -> T | None:
        if not is_real(x):
            return fb
        return op(x)

    return func


def make_real_binary[T: Real](op: Callable[[T, T], T], fb: T | None = None) -> Callable[[T, T], T | None]:
    """
    Creates a binary function that applies the given operation to two real numbers, with fallback logic.

    :param op: The binary operation to apply.
    :param fb: The fallback value to return if neither input is real.
    :return: A function that applies ``op`` to two real numbers or returns ``fb``.
    """

    def func(a: T, b: T) -> T | None:
        if not is_real(a) and not is_real(b):
            return fb
        if not is_real(a):
            return b
        if not is_real(b):
            return a
        return op(a, b)

    return func


def make_real_reducer[T: Real](
    op: Callable[[Sequence[T], ...], T],
    fb: T | None = None,
) -> Callable[[Sequence[T], ...], T | None]:
    """
    Creates a reducer function that applies the given operation to a sequence of real numbers, filtering out non-reals.

    :param op: The reduction operation to apply.
    :param fb: The fallback value to return if no real numbers are present.
    :return: A function that reduces a sequence of real numbers or returns ``fb``.
    """

    def func(xs: Sequence[T], *args, **kwargs) -> T | None:
        xs_new = list(filter(is_real, xs))
        return op(xs_new, *args, **kwargs) if len(xs_new) > 0 else fb

    return func


real_abs = make_real_unary(np.abs)
real_greater = make_real_binary(lambda x, y: np.max((x, y)))
real_smaller = make_real_binary(lambda x, y: np.min((x, y)))
real_max = make_real_reducer(np.max)
real_min = make_real_reducer(np.min)
real_mean = make_real_reducer(np.mean)
real_std = make_real_reducer(np.std)
real_nan_greater = make_real_binary(lambda x, y: np.nanmax((x, y)))
real_nan_smaller = make_real_binary(lambda x, y: np.nanmin((x, y)))
real_nan_max = make_real_reducer(np.nanmax)
real_nan_min = make_real_reducer(np.nanmin)
real_nan_mean = make_real_reducer(np.nanmean)
real_nan_std = make_real_reducer(np.nanstd)
