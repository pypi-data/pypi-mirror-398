import dataclasses
import unittest

import ddt

from iker.common.utils.funcutils import composable, identity
from iker.common.utils.funcutils import const, first, packed, second
from iker.common.utils.funcutils import lazy, memorized, singleton, unique_returns
from iker.common.utils.randutils import randomizer


@dataclasses.dataclass
class Counter(object):
    value: int = 0

    def call(self):
        self.value += 1


@ddt.ddt
class FuncUtilsTest(unittest.TestCase):

    def test_const(self):
        self.assertEqual(5, const(5)())
        self.assertEqual(5, const(5)(1, 2, 3))
        self.assertEqual(5, const(5)(a=1, b=2))

        self.assertEqual("hello", const("hello")())
        self.assertEqual("hello", const("hello")(1, 2, 3))
        self.assertEqual("hello", const("hello")(a=1, b=2))

    def test_first(self):
        self.assertEqual(1, first()((1, "a")))
        self.assertEqual("key", first()(("key", 12)))
        self.assertEqual((1, 2), first()(((1, 2), "value")))

        with self.assertRaises(ValueError):
            first()((1, 2, 3))
        with self.assertRaises(ValueError):
            first()(123)

    def test_second(self):
        self.assertEqual("a", second()((1, "a")))
        self.assertEqual(12, second()(("key", 12)))
        self.assertEqual("value", second()(((1, 2), "value")))

        with self.assertRaises(ValueError):
            second()((1, 2, 3))
        with self.assertRaises(ValueError):
            second()(123)

    def test_packed(self):
        self.assertEqual(3, packed(lambda x, y: x + y)((1, 2)))
        self.assertEqual(12, packed(lambda x, y, z: x + y + z)((3, 4, 5)))
        self.assertEqual("aab", packed(lambda a, b, x, y: a * x + b * y)(("a", "b", 2, 1)))

        with self.assertRaises(TypeError):
            packed(lambda x, y, z: x ** y ** z)((2, 3, 4, 5))
        with self.assertRaises(TypeError):
            packed(lambda x, y, z: x ** y ** z)((2, 3))

    def test_identity(self):
        self.assertEqual(1, identity(1))
        self.assertEqual("test", identity("test"))
        self.assertEqual([1, 2, 3], identity([1, 2, 3]))
        self.assertEqual({"key": "value"}, identity({"key": "value"}))

    def test_composable(self):
        calls = []

        @composable
        def add_one(x: int) -> int:
            calls.append(("add_one", x))
            return x + 1

        @composable
        def time_two(x: int) -> int:
            calls.append(("time_two", x))
            return x * 2

        @composable
        def to_str(x: int) -> str:
            calls.append(("to_str", x))
            return str(x)

        @composable
        def repeat(x: str) -> str:
            calls.append(("repeat", x))
            return x + x

        @composable
        def to_int(x: str) -> int:
            calls.append(("to_int", x))
            return int(x)

        self.assertEqual(add_one.compose(add_one)(1), 3)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("add_one", 2),
                         ])
        calls.clear()

        self.assertEqual(add_one.compose(time_two)(1), 3)
        self.assertEqual(calls,
                         [
                             ("time_two", 1),
                             ("add_one", 2),
                         ])
        calls.clear()

        self.assertEqual(add_one.and_then(add_one)(1), 3)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("add_one", 2),
                         ])
        calls.clear()

        self.assertEqual(add_one.and_then(time_two)(1), 4)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                         ])
        calls.clear()

        self.assertEqual(add_one.compose(time_two.compose(add_one))(1), 5)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                             ("add_one", 4),
                         ])
        calls.clear()

        self.assertEqual(add_one.and_then(time_two.and_then(add_one))(1), 5)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                             ("add_one", 4),
                         ])
        calls.clear()

        self.assertEqual(time_two.compose(time_two)(1), 4)
        self.assertEqual(calls,
                         [
                             ("time_two", 1),
                             ("time_two", 2),
                         ])
        calls.clear()

        self.assertEqual(time_two.compose(add_one)(1), 4)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                         ])
        calls.clear()

        self.assertEqual(time_two.and_then(time_two)(1), 4)
        self.assertEqual(calls,
                         [
                             ("time_two", 1),
                             ("time_two", 2),
                         ])
        calls.clear()

        self.assertEqual(time_two.and_then(add_one)(1), 3)
        self.assertEqual(calls,
                         [
                             ("time_two", 1),
                             ("add_one", 2),
                         ])
        calls.clear()

        self.assertEqual(time_two.compose(add_one.compose(time_two))(1), 6)
        self.assertEqual(calls,
                         [
                             ("time_two", 1),
                             ("add_one", 2),
                             ("time_two", 3),
                         ])
        calls.clear()

        self.assertEqual(time_two.and_then(add_one.and_then(time_two))(1), 6)
        self.assertEqual(calls,
                         [
                             ("time_two", 1),
                             ("add_one", 2),
                             ("time_two", 3),
                         ])
        calls.clear()

        self.assertEqual(add_one
                         .compose(time_two)
                         .compose(to_int)
                         .compose(repeat)
                         .compose(to_str)
                         .compose(time_two)
                         .compose(add_one)
                         (1),
                         89)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                             ("to_str", 4),
                             ("repeat", "4"),
                             ("to_int", "44"),
                             ("time_two", 44),
                             ("add_one", 88),
                         ])
        calls.clear()

        self.assertEqual(add_one
                         .compose(time_two)
                         .compose(to_int)
                         .compose(repeat)
                         .compose(repeat)
                         .compose(repeat)
                         .compose(to_str)
                         .compose(time_two)
                         .compose(add_one)
                         (1),
                         88888889)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                             ("to_str", 4),
                             ("repeat", "4"),
                             ("repeat", "44"),
                             ("repeat", "4444"),
                             ("to_int", "44444444"),
                             ("time_two", 44444444),
                             ("add_one", 88888888),
                         ])
        calls.clear()

        self.assertEqual(add_one
                         .and_then(time_two)
                         .and_then(to_str)
                         .and_then(repeat)
                         .and_then(to_int)
                         .and_then(time_two)
                         .and_then(add_one)
                         (1),
                         89)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                             ("to_str", 4),
                             ("repeat", "4"),
                             ("to_int", "44"),
                             ("time_two", 44),
                             ("add_one", 88),
                         ])
        calls.clear()

        self.assertEqual(add_one
                         .and_then(time_two)
                         .and_then(to_str)
                         .and_then(repeat)
                         .and_then(repeat)
                         .and_then(repeat)
                         .and_then(to_int)
                         .and_then(time_two)
                         .and_then(add_one)
                         (1),
                         88888889)
        self.assertEqual(calls,
                         [
                             ("add_one", 1),
                             ("time_two", 2),
                             ("to_str", 4),
                             ("repeat", "4"),
                             ("repeat", "44"),
                             ("repeat", "4444"),
                             ("to_int", "44444444"),
                             ("time_two", 44444444),
                             ("add_one", 88888888),
                         ])
        calls.clear()

    def test_composable__identity(self):
        for _ in range(0, 100):
            add_operand = randomizer().next_int(1, 10)
            times_operand = randomizer().next_int(1, 10)

            @composable
            def add(x: int) -> int:
                return x + add_operand

            @composable
            def times(x: int) -> int:
                return x * times_operand

            for _ in range(1000):
                v = randomizer().next_int(1, 10)
                self.assertEqual(add.and_then(times)(v), times.compose(add)(v))
                self.assertEqual(add.compose(times)(v), times.and_then(add)(v))
                self.assertEqual(add.and_then(times).and_then(add).and_then(times)(v),
                                 times.compose(add).compose(times).compose(add)(v))
                self.assertEqual(times.and_then(add).and_then(times).and_then(add)(v),
                                 add.compose(times).compose(add).compose(times)(v))
                self.assertEqual(add.and_then(times).and_then(add)(v),
                                 add.and_then(times.and_then(add))(v))
                self.assertEqual(times.and_then(add).and_then(times)(v),
                                 times.and_then(add.and_then(times))(v))
                self.assertEqual(add.compose(times).compose(add)(v),
                                 add.compose(times.compose(add))(v))
                self.assertEqual(times.compose(add).compose(times)(v),
                                 times.compose(add.compose(times))(v))
                self.assertEqual(add.compose(times).and_then(add)(v),
                                 times.and_then(add).and_then(add)(v))
                self.assertEqual(add.and_then(times).compose(add)(v),
                                 times.compose(add).compose(add)(v))

    def test_singleton__class(self):
        @singleton
        class DummySingleton(object):
            counter = Counter()

            def __init__(self, value):
                self.counter = Counter()
                self.counter.value = value
                DummySingleton.counter.call()

        self.assertEqual(1, DummySingleton(1).counter.value)
        self.assertEqual(1, DummySingleton.counter.value)

        # Invoked exactly once
        self.assertEqual(1, DummySingleton(2).counter.value)
        self.assertEqual(1, DummySingleton.counter.value)
        self.assertEqual(1, DummySingleton(3).counter.value)
        self.assertEqual(1, DummySingleton.counter.value)

    def test_singleton__function(self):
        @singleton
        def func(num):
            return num

        self.assertEqual(1, func(1))

        # Invoked exactly once
        self.assertEqual(1, func(2))
        self.assertEqual(1, func(3))

    def test_singleton__class_function(self):
        class DummySingleton(object):
            counter = Counter()

            def __init__(self, counter):
                self.counter = counter

            @staticmethod
            @singleton
            def get():
                DummySingleton.counter.call()
                return DummySingleton(DummySingleton.counter)

        self.assertEqual(1, DummySingleton.get().counter.value)
        self.assertEqual(1, DummySingleton.counter.value)

        # Invoked exactly once
        self.assertEqual(1, DummySingleton.get().counter.value)
        self.assertEqual(1, DummySingleton.counter.value)
        self.assertEqual(1, DummySingleton.get().counter.value)
        self.assertEqual(1, DummySingleton.counter.value)

    def test_memorized(self):
        counter = Counter()

        @memorized
        def func(a, b):
            counter.call()
            return a + b

        # Original call
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))

        self.assertEqual(1, counter.value)

        # New call
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))

        self.assertEqual(2, counter.value)

        # Another new call
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))

        self.assertEqual(3, counter.value)

        # Another new call with kwarg
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))

        self.assertEqual(4, counter.value)

        # Another new call with the same kwarg but different order
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))

        self.assertEqual(4, counter.value)

        # Another new call with the same kwarg but different type
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))

        self.assertEqual(4, counter.value)

        # Another new call with the same kwarg but different order and type
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))

        self.assertEqual(4, counter.value)

    def test_memorized__ordered(self):
        counter = Counter()

        @memorized(ordered=True)
        def func(a, b):
            counter.call()
            return a + b

        # Original call
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))

        self.assertEqual(1, counter.value)

        # New call
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))

        self.assertEqual(2, counter.value)

        # Another new call
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))

        self.assertEqual(3, counter.value)

        # Another new call with kwarg
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))

        self.assertEqual(4, counter.value)

        # Another new call with the same kwarg but different order
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))

        self.assertEqual(5, counter.value)

        # Another new call with the same kwarg but different type
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))

        self.assertEqual(5, counter.value)

        # Another new call with the same kwarg but different order and type
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))

        self.assertEqual(5, counter.value)

    def test_memorized__typed(self):
        counter = Counter()

        @memorized(typed=True)
        def func(a, b):
            counter.call()
            return a + b

        # Original call
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))

        self.assertEqual(1, counter.value)

        # New call
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))

        self.assertEqual(2, counter.value)

        # Another new call
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))

        self.assertEqual(3, counter.value)

        # Another new call with kwarg
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))

        self.assertEqual(4, counter.value)

        # Another new call with the same kwarg but different order
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))

        self.assertEqual(4, counter.value)

        # Another new call with the same kwarg but different type
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))

        self.assertEqual(5, counter.value)

        # Another new call with the same kwarg but different order and type
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))

        self.assertEqual(5, counter.value)

    def test_memorized__ordered_typed(self):
        counter = Counter()

        @memorized(ordered=True, typed=True)
        def func(a, b):
            counter.call()
            return a + b

        # Original call
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))
        self.assertEqual(3, func(1, 2))

        self.assertEqual(1, counter.value)

        # New call
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))
        self.assertEqual(3, func(2, 1))

        self.assertEqual(2, counter.value)

        # Another new call
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))
        self.assertEqual(4, func(1, 3))

        self.assertEqual(3, counter.value)

        # Another new call with kwarg
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))
        self.assertEqual(3, func(a=1, b=2))

        self.assertEqual(4, counter.value)

        # Another new call with the same kwarg but different order
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))
        self.assertEqual(3, func(b=2, a=1))

        self.assertEqual(5, counter.value)

        # Another new call with the same kwarg but different type
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))
        self.assertEqual(3, func(a=1.0, b=2.0))

        self.assertEqual(6, counter.value)

        # Another new call with the same kwarg but different order and type
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))
        self.assertEqual(3, func(b=2.0, a=1.0))

        self.assertEqual(7, counter.value)

    def test_lazy(self):
        counter = Counter()

        @lazy
        def func(a, b):
            counter.call()
            return a + b

        lazy_call = func(1, 2)

        self.assertEqual(0, counter.value)

        self.assertEqual(3, lazy_call())
        self.assertEqual(3, lazy_call())
        self.assertEqual(3, lazy_call())

        self.assertEqual(3, counter.value)

    def test_lazy__with_memorized(self):
        counter = Counter()

        @lazy
        @memorized
        def func(a, b):
            counter.call()
            return a + b

        lazy_call = func(1, 2)

        self.assertEqual(0, counter.value)

        # Original call
        self.assertEqual(3, lazy_call())
        self.assertEqual(3, lazy_call())
        self.assertEqual(3, lazy_call())

        self.assertEqual(1, counter.value)

        # A new call
        self.assertEqual(3, func(2, 1)())
        self.assertEqual(3, func(2, 1)())
        self.assertEqual(3, func(2, 1)())

        self.assertEqual(2, counter.value)

        # Another new call
        self.assertEqual(4, func(1, 3)())
        self.assertEqual(4, func(1, 3)())
        self.assertEqual(4, func(1, 3)())

        self.assertEqual(3, counter.value)

    def test_unique_returns(self):
        for _ in range(0, 100000):
            rng = randomizer()

            @unique_returns
            def func(a, b):
                return rng.next_int(a, b)

            lo = rng.next_int(0, 100)
            hi = rng.next_int(100, 200)

            result = [func(lo, hi) for _ in range(hi, lo)]
            self.assertEqual(set(result), set(range(hi, lo)))

    def test_unique_returns__mex_trial_exceeded(self):
        rng = randomizer()

        def func(a, b):
            return rng.next_int(a, b)

        decorated_func = unique_returns(func, max_trials=10)

        with self.assertRaises(ValueError):
            [decorated_func(0, 10) for _ in range(11)]
