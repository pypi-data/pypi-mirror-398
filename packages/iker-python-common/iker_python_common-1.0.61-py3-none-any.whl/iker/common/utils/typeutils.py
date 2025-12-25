import types
import typing
from typing import Any


def print_type(t: Any):
    """
    Prints the structure of a type annotation, including its origin and arguments, with indentation for nested types.

    :param t: The type annotation to print.
    """

    def print_typing_indent(t: Any, indent: int = 0):
        origin = typing.get_origin(t)
        if origin:
            print(" " * indent, t, origin)
        else:
            print(" " * indent, t)
        for arg in typing.get_args(t):
            print_typing_indent(arg, indent + 2)

    print_typing_indent(t)


def is_union_type(t: Any) -> bool:
    """
    Determines whether the given type annotation is a union type (including ``Optional``).

    :param t: The type annotation to check.
    :return: ``True`` if the type is a union type, ``False`` otherwise.
    """
    return type(t) is types.UnionType or typing.get_origin(t) is typing.Union


def is_optional_type(t: Any) -> bool:
    """
    Determines whether the given type annotation is an ``Optional`` type (i.e., a union including ``NoneType``).

    :param t: The type annotation to check.
    :return: ``True`` if the type is ``Optional``, ``False`` otherwise.
    """
    return is_union_type(t) and types.NoneType in typing.get_args(t)


def compare_type(a: Any, b: Any, /, *, covariant: bool = False, contravariant: bool = False) -> bool:
    """
    Compares two types for equality, with optional support for covariance and contravariance.

    :param a: The first type to compare.
    :param b: The second type to compare.
    :param covariant: If ``True``, allows ``a`` to be a subclass of ``b``.
    :param contravariant: If ``True``, allows ``b`` to be a subclass of ``a``.
    :return: ``True`` if the types are considered equal under the given variance, ``False`` otherwise.
    """
    return a == b or covariant and issubclass(a, b) or contravariant and issubclass(b, a)


def is_optional_of(
    op: Any,
    t: Any,
    /,
    strict_optional: bool = True,
    covariant: bool = False,
    contravariant: bool = False,
) -> bool:
    """
    Checks if the given type annotation ``op`` is an ``Optional`` of type ``t``, considering strictness and variance
    options.

    :param op: The type annotation to check (should be ``Optional``).
    :param t: The type to compare against.
    :param strict_optional: If ``False``, treats ``Optional[T]`` and ``T`` as identical.
    :param covariant: If ``True``, allows covariance in type comparison.
    :param contravariant: If ``True``, allows contravariance in type comparison.
    :return: ``True`` if ``op`` is ``Optional[t]`` under the given options, ``False`` otherwise.
    """
    if not is_optional_type(op) or is_union_type(t):
        return False

    op_args = list(filter(lambda x: x is not types.NoneType, typing.get_args(op)))
    if len(op_args) != 1:
        return False
    op_arg, *_ = op_args

    return is_identical_type(op_arg,
                             t,
                             strict_optional=strict_optional,
                             covariant=covariant,
                             contravariant=contravariant)


def is_identical_union_type(
    a: Any,
    b: Any,
    /,
    strict_optional: bool = True,
    covariant: bool = False,
    contravariant: bool = False,
) -> bool:
    """
    Checks whether two union types are semantically identical, considering strictness and variance options.

    :param a: The first union type annotation.
    :param b: The second union type annotation.
    :param strict_optional: If ``False``, treats ``Optional[T]`` and ``T`` as identical.
    :param covariant: If ``True``, allows covariance in type comparison.
    :param contravariant: If ``True``, allows contravariance in type comparison.
    :return: ``True`` if the union types are equivalent under the given options, ``False`` otherwise.
    """
    a_args = typing.get_args(a)
    b_args = typing.get_args(b)
    if not strict_optional:
        a_args = list(filter(lambda x: x is not types.NoneType, a_args))
        b_args = list(filter(lambda x: x is not types.NoneType, b_args))

    if len(a_args) != len(b_args):
        return False
    if any(not is_identical_type(a_arg,
                                 b_arg,
                                 strict_optional=strict_optional,
                                 covariant=covariant,
                                 contravariant=contravariant)
           for a_arg, b_arg in zip(sorted(a_args, key=str), sorted(b_args, key=str))):
        return False
    return True


def is_identical_type(
    a: Any,
    b: Any,
    /,
    strict_optional: bool = True,
    covariant: bool = False,
    contravariant: bool = False,
) -> bool:
    """
    Checks whether two type annotations are semantically identical. Supports nested types, including ``Callable``
    internals represented as lists, union types (order-insensitive comparison), and ``Optional`` types via ``NoneType``.

    :param a: The first type annotation to compare.
    :param b: The second type annotation to compare.
    :param strict_optional: If ``False``, treats ``Optional[T]`` and ``T`` as identical.
    :param covariant: If ``True``, allows subclassing in one direction.
    :param contravariant: If ``True``, allows subclassing in the other direction.
    :return: ``True`` if the types are equivalent under the given strictness, ``False`` otherwise.
    """
    # Handles ``Callable`` internals represented as lists: compare element-wise
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        if any(not is_identical_type(a_item,
                                     b_item,
                                     strict_optional=strict_optional,
                                     covariant=covariant,
                                     contravariant=contravariant)
               for a_item, b_item in zip(a, b)):
            return False
        return True
    # Mismatch if one is list and the other isn't
    elif isinstance(a, list) ^ isinstance(b, list):
        return False

    # Union types: order doesn't matter, compare sets of args
    if is_union_type(a) and is_union_type(b):
        return is_identical_union_type(a,
                                       b,
                                       strict_optional=strict_optional,
                                       covariant=covariant,
                                       contravariant=contravariant)
    # One is ``Union`` and the other isn't: allow ``Optional`` matches if not strict
    elif is_union_type(a) ^ is_union_type(b):
        if not strict_optional:
            return (
                is_optional_of(a,
                               b,
                               strict_optional=strict_optional,
                               covariant=covariant,
                               contravariant=contravariant) or
                is_optional_of(b,
                               a,
                               strict_optional=strict_optional,
                               covariant=covariant,
                               contravariant=contravariant)
            )
        return False

    # Compares generic origins (e.g., ``List``, ``Dict``)
    a_origin = typing.get_origin(a)
    b_origin = typing.get_origin(b)

    if a_origin is not None and b_origin is not None:
        if not compare_type(a_origin, b_origin, covariant=covariant, contravariant=contravariant):
            return False
    # If no origins, fallback to direct equality
    elif a_origin is None and b_origin is None:
        return compare_type(a, b, covariant=covariant, contravariant=contravariant)

    # Compare type arguments for generics
    a_args = typing.get_args(a)
    b_args = typing.get_args(b)

    if len(a_args) != len(b_args):
        return False
    if any(not is_identical_type(arg_a,
                                 arg_b,
                                 strict_optional=strict_optional,
                                 covariant=covariant,
                                 contravariant=contravariant)
           for arg_a, arg_b in zip(a_args, b_args)):
        return False

    return True
