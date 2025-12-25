import abc
import os
from decimal import Decimal
from typing import Any, Protocol

import pytest
from _pytest.python_api import ApproxBase, ApproxDecimal, ApproxMapping, ApproxScalar, ApproxSequenceLike

from iker.common.utils.numutils import to_decimal

__all__ = [
    "norm_path",
    "nested_approx",
    "MockedCallable",
    "CalleeMock",
    "return_callee",
    "throw_callee",
]


def norm_path(s: str) -> str:
    _, path = os.path.splitdrive(os.path.normpath(s))
    return path


class ApproxNestedMixin(ApproxBase):
    def __repr__(self) -> str:

        def recur_repr_helper(obj):
            if isinstance(obj, dict):
                return dict((k, recur_repr_helper(v)) for k, v in obj.items())
            elif isinstance(obj, tuple):
                return tuple(recur_repr_helper(o) for o in obj)
            elif isinstance(obj, list):
                return list(recur_repr_helper(o) for o in obj)
            else:
                return self._approx_scalar(obj)

        return "approx({!r})".format(recur_repr_helper(self.expected))

    def _approx_scalar(self, x) -> ApproxScalar:
        if isinstance(x, Decimal):
            return ApproxDecimal(x, to_decimal(self.rel), to_decimal(self.abs), self.nan_ok)
        return ApproxScalar(x, self.rel, self.abs, self.nan_ok)

    def _check_type(self):
        pass


class ApproxNestedSequenceLike(ApproxNestedMixin, ApproxSequenceLike):

    def _yield_comparisons(self, actual):
        for k in range(len(self.expected)):
            mapping = nested_approx(self.expected[k], self.rel, self.abs, self.nan_ok)
            if isinstance(mapping, ApproxScalar):
                yield actual[k], self.expected[k]
            else:
                yield from mapping._yield_comparisons(actual[k])


class ApproxNestedMapping(ApproxNestedMixin, ApproxMapping):

    def _yield_comparisons(self, actual):
        for k in self.expected.keys():
            mapping = nested_approx(self.expected[k], self.rel, self.abs, self.nan_ok)
            if isinstance(mapping, ApproxScalar):
                yield actual[k], self.expected[k]
            else:
                yield from mapping._yield_comparisons(actual[k])


def nested_approx(expected, rel: float = None, abs: float = None, nan_ok: bool = False) -> ApproxBase:
    if isinstance(expected, dict):
        return ApproxNestedMapping(expected, rel, abs, nan_ok)
    if isinstance(expected, (tuple, list)):
        return ApproxNestedSequenceLike(expected, rel, abs, nan_ok)
    if isinstance(expected, Decimal):
        return ApproxDecimal(expected, to_decimal(rel), to_decimal(abs), nan_ok)
    return pytest.approx(expected, rel, abs, nan_ok)


class MockedCallable(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...


class CalleeMock(abc.ABC):

    def __init__(self, valuer: MockedCallable | Any):
        self.calls = []
        self.valuer = valuer

    def __call__(self, *args, **kwargs):
        try:
            return self.execute(*args, **kwargs)
        except Exception:
            raise
        finally:
            self.calls.append((args, kwargs))

    def count_calls(self) -> int:
        return len(self.calls)

    def count_calls_with(self, call: tuple[tuple, dict]) -> int:
        return sum(1 for c in self.calls if c == call)

    def find_first_call(self, call: tuple[tuple, dict]) -> int:
        return next((index for index, c in enumerate(self.calls) if c == call), -1)

    def find_last_call(self, call: tuple[tuple, dict]) -> int:
        return next((self.count_calls() - index - 1 for index, c in enumerate(reversed(self.calls)) if c == call), -1)

    def find_calls(self, call: tuple[tuple, dict]) -> list[int]:
        return list(index for index, c in enumerate(self.calls) if c == call)

    def assert_not_called(self):
        assert self.count_calls() == 0, "failed not called"

    def assert_called(self):
        assert self.count_calls() > 0, "failed called"

    def assert_called_once(self):
        assert self.count_calls() == 1, "failed called once"

    def assert_called_times(self, count: int):
        assert self.count_calls() == count, f"failed called {count} times"

    def assert_not_called_with(self):
        def assertion(*args, **kwargs):
            call = (args, kwargs)
            assert self.count_calls_with(call) == 0, f"failed not called with {call}"

        return assertion

    def assert_called_with(self):
        def assertion(*args, **kwargs):
            call = (args, kwargs)
            assert self.count_calls_with(call) > 0, f"failed called with {call}"

        return assertion

    def assert_called_once_with(self):
        def assertion(*args, **kwargs):
            call = (args, kwargs)
            assert self.count_calls_with(call) == 1, f"failed called once with {call}"

        return assertion

    def assert_called_times_with(self, count: int):
        def assertion(*args, **kwargs):
            call = (args, kwargs)
            assert self.count_calls_with(call) == count, f"failed called {count} times with {call}"

        return assertion

    def execute(self, *args, **kwargs):
        if self.valuer is None:
            return
        if callable(self.valuer):
            return self.valuer(*args, **kwargs)
        return self.valuer


def return_callee(return_valuer=None) -> CalleeMock:
    return CalleeMock(return_valuer)


def throw_callee(clazz, *error_args, **error_kwargs) -> CalleeMock:
    def valuer(*args, **kwargs):
        raise clazz(*error_args, **error_kwargs)

    return CalleeMock(valuer)
