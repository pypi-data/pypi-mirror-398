import datetime
import math
import random
import string
import sys
from collections.abc import Callable, Sequence
from typing import overload

from iker.common.utils.dtutils import dt_utc_max, dt_utc_min
from iker.common.utils.funcutils import memorized, singleton
from iker.common.utils.jsonutils import JsonType
from iker.common.utils.sequtils import head_or_none

__all__ = [
    "max_int",
    "max_float",
    "Randomizer",
    "randomizer",
]


@singleton
def max_int() -> int:
    """
    Returns the maximum integer value supported by the system.

    :return: The maximum integer value (``sys.maxsize``).
    """
    return sys.maxsize


@singleton
def max_float() -> float:
    """
    Returns the maximum float value supported by the system.

    :return: The maximum float value (``sys.float_info.max``).
    """
    return sys.float_info.max


class Randomizer(object):
    """
    Provides a suite of randomization utilities, including random numbers, strings, dates, and JSON objects. Uses a
    system random generator for improved randomness.

    :param seed: The seed for the random number generator.
    """

    def __init__(self, seed: int = 0):
        self.random = random.SystemRandom(seed)

    def next_bool(self) -> bool:
        """
        Returns a random boolean value.

        :return: ``True`` or ``False``, chosen at random.
        """
        return self.random.getrandbits(1) == 1

    def next_int(self, lo: int = 0, hi: int = max_int()) -> int:
        """
        Returns a random integer in the range [``lo``, ``hi``).

        :param lo: The inclusive lower bound.
        :param hi: The exclusive upper bound.
        :return: A random integer between ``lo`` (inclusive) and ``hi`` (exclusive).
        """
        assert lo < hi, "the lower bound must be smaller than the upper bound"
        return self.random.randrange(lo, hi)

    def next_float(self, lo: float = 0.0, hi: float = 1.0) -> float:
        """
        Returns a random float in the range [``lo``, ``hi``].

        :param lo: The inclusive lower bound.
        :param hi: The inclusive upper bound.
        :return: A random float between ``lo`` and ``hi``.
        """
        assert lo <= hi, "the lower bound must be not greater than the upper bound"
        assert not math.isinf(hi - lo), "the range between the lower bound and the upper bound exceeded the float range"
        return lo + (hi - lo) * self.random.random()

    def next_fixed(self, precision: int = 7) -> float:
        """
        Returns a random float in [0, 1) with the specified number of bits of ``precision``.

        :param precision: The number of bits of precision.
        :return: A random float in [0, 1) with the given ``precision``.
        """
        assert precision >= 0, "the precision must be non-negative"
        width = 2 ** precision
        return self.next_int(0, width) / width

    def next_gaussian(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """
        Returns a random float sampled from a Gaussian distribution with mean ``mu`` and standard deviation ``sigma``.

        :param mu: The mean of the distribution.
        :param sigma: The standard deviation of the distribution.
        :return: A random float sampled from the specified Gaussian distribution.
        """
        return self.random.gauss(mu, sigma)

    def random_string(self, chars: str, length: int) -> str:
        """
        Returns a random string of the specified ``length``, using the provided ``chars``.

        :param chars: The characters to use for the string.
        :param length: The length of the string.
        :return: A random string of the given ``length``.
        """
        assert length >= 0, "length of the random string must be non-negative"
        if length == 0:
            return ""
        return "".join(self.random.choices(chars, k=length))

    def random_ascii(self, length: int) -> str:
        """
        Returns a random ASCII string of the specified ``length``.

        :param length: The length of the string.
        :return: A random ASCII string.
        """
        return self.random_string(string.ascii_letters, length)

    def random_alphanumeric(self, length: int) -> str:
        """
        Returns a random alphanumeric string of the specified ``length``.

        :param length: The length of the string.
        :return: A random alphanumeric string.
        """
        return self.random_string(string.digits + string.ascii_letters, length)

    def random_hex(self, length: int) -> str:
        """
        Returns a random hexadecimal string of the specified ``length`` (uppercase).

        :param length: The length of the string.
        :return: A random hexadecimal string in uppercase.
        """
        # Since ``string.hexdigits`` contains both lower and upper case,
        # to balance the possibility we need double the digits
        return self.random_string(string.digits + string.hexdigits, length).upper()

    def random_oct(self, length: int) -> str:
        """
        Returns a random octal string of the specified ``length`` (uppercase).

        :param length: The length of the string.
        :return: A random octal string in uppercase.
        """
        return self.random_string(string.octdigits, length).upper()

    def random_unit_vector(self, length: int) -> list[float]:
        """
        Returns a random unit vector of the specified ``length``.

        :param length: The length of the vector.
        :return: A list of floats representing a unit vector.
        """
        assert length > 0, "length of the random unit vector must be positive"
        while True:
            v = [self.next_gaussian() for _ in range(length)]
            n = sum(x * x for x in v) ** 0.5
            if n < 1.0e-9:
                continue
            return [x / n for x in v]
        return [1.0]

    def random_datetime(
        self,
        begin: datetime.datetime = dt_utc_min(),
        end: datetime.datetime = dt_utc_max(),
    ) -> datetime.datetime:
        """
        Returns a random ``datetime`` between the specified ``begin`` and ``end``.

        :param begin: The earliest datetime.
        :param end: The latest datetime.
        :return: A random ``datetime`` between ``begin`` and ``end``.
        """
        return begin + datetime.timedelta(seconds=self.next_float(0.0, (end - begin).total_seconds()))

    def random_date(
        self,
        begin: datetime.date = dt_utc_min().date(),
        end: datetime.date = dt_utc_max().date(),
    ) -> datetime.date:
        """
        Returns a random ``date`` between the specified ``begin`` and ``end``.

        :param begin: The earliest date.
        :param end: The latest date.
        :return: A random ``date`` between ``begin`` and ``end``.
        """
        dt = self.random_datetime(datetime.datetime.combine(begin, dt_utc_min().timetz()),
                                  datetime.datetime.combine(end, dt_utc_min().timetz()))
        return dt.date()

    def random_time(
        self,
        begin: datetime.time = dt_utc_min().timetz(),
        end: datetime.time = dt_utc_max().timetz(),
    ) -> datetime.time:
        """
        Returns a random ``time`` between the specified ``begin`` and ``end``.

        :param begin: The earliest time.
        :param end: The latest time.
        :return: A random ``time`` between ``begin`` and ``end``.
        """
        dt = self.random_datetime(datetime.datetime.combine(dt_utc_min().date(), begin),
                                  datetime.datetime.combine(dt_utc_min().date(), end))
        return dt.timetz()

    def random_json_object(
        self,
        max_depth: int = 1,
        max_elems: int = 5,
        key_chars: str = string.ascii_letters,
        key_length: int = 5,
        value_chars: str = string.ascii_letters,
        value_length: int = 5,
    ) -> JsonType:
        """
        Generates a random JSON-compatible object with configurable depth, element count, and key/value characteristics.

        :param max_depth: The maximum depth of nested objects or arrays.
        :param max_elems: The maximum number of elements in arrays or keys in objects.
        :param key_chars: The characters to use for object keys.
        :param key_length: The length of each object key.
        :param value_chars: The characters to use for string values.
        :param value_length: The length of each string value.
        :return: A randomly generated JSON-compatible object.
        """
        choices = [list, dict, int, float, bool, str, None]
        root_choices = [list, dict]
        leaf_choices = [int, float, bool, str, None]

        def generate_json_object(depth: int):
            choice = self.random.choice(choices)
            if depth == 0:
                choice = self.random.choice(root_choices)
            if depth == max_depth:
                choice = self.random.choice(leaf_choices)

            if choice == list:
                return list(generate_json_object(depth + 1) for _ in range(self.next_int(0, max_elems + 1)))
            if choice == dict:
                return dict((self.random_string(key_chars, key_length), generate_json_object(depth + 1))
                            for _ in range(self.next_int(0, max_elems + 1)))
            if choice == int:
                return self.next_int()
            if choice == float:
                return self.next_float()
            if choice == bool:
                return self.next_bool()
            if choice == str:
                return self.random_string(value_chars, value_length)

            return None

        return generate_json_object(0)

    @overload
    def sample[T](self, population: Sequence[T], count_func: Callable[[T], int], k: int) -> list[T]:
        ...

    @overload
    def sample[T](self, population: Sequence[T], k: int) -> list[T]:
        ...

    @overload
    def sample[T](self, population: Sequence[T], count_func: Callable[[T], int], k: None = None) -> T:
        ...

    @overload
    def sample[T](self, population: Sequence[T], k: None = None) -> T:
        ...

    def sample[T](self, population: Sequence[T], count_func: Callable[[T], int] = None, k: int = None) -> list[T] | T:
        """
        Returns a random sample from the population, optionally weighted by a count function.

        :param population: The sequence to sample from.
        :param count_func: Optional function to determine the count/weight for each item.
        :param k: The number of items to sample. If ``None``, returns a single item.
        :return: A list of sampled items, or a single item if ``k`` is ``None``.
        """
        counts = list(map(count_func, population)) if callable(count_func) else None
        result = self.random.sample(population, counts=counts, k=k or 1)
        return result if k is not None else head_or_none(result)

    @overload
    def choose[T](self, population: Sequence[T], weight_func: Callable[[T], float], k: int) -> list[T]:
        ...

    @overload
    def choose[T](self, population: Sequence[T], k: int) -> list[T]:
        ...

    @overload
    def choose[T](self, population: Sequence[T], weight_func: Callable[[T], float], k: None = None) -> T:
        ...

    @overload
    def choose[T](self, population: Sequence[T], k: None = None) -> T:
        ...

    def choose[T](
        self,
        population: Sequence[T],
        weight_func: Callable[[T], float] = None,
        k: int = None,
    ) -> list[T] | T:
        """
        Returns a random selection from the population, optionally weighted by a weight function.

        :param population: The sequence to choose from.
        :param weight_func: Optional function to determine the weight for each item.
        :param k: The number of items to choose. If ``None``, returns a single item.
        :return: A list of chosen items, or a single item if ``k`` is ``None``.
        """
        weights = list(map(weight_func, population)) if callable(weight_func) else None
        result = self.random.choices(population, weights=weights, k=k or 1)
        return result if k is not None else head_or_none(result)

    def shuffle[T](self, data: Sequence[T]) -> list[T]:
        """
        Returns a shuffled copy of the input ``data`` sequence.

        :param data: The sequence to shuffle.
        :return: A new list containing the shuffled elements.
        """
        clone = list(item for item in data)
        self.random.shuffle(clone)
        return clone


@memorized
def randomizer(seed: int = 0) -> Randomizer:
    """
    Returns a memorized ``Randomizer`` instance for the given ``seed``.

    :param seed: The seed for the random number generator.
    :return: A ``Randomizer`` instance.
    """
    return Randomizer(seed)
