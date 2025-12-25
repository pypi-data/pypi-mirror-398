import itertools
import unittest

import ddt

from iker.common.utils.dtutils import dt_utc_max, dt_utc_min
from iker.common.utils.randutils import max_float, max_int, randomizer


@ddt.ddt
class RandUtilsTest(unittest.TestCase):

    def test_next_bool(self):
        samples = [randomizer().next_bool() for _ in range(100)]
        self.assertTrue(any(s for s in samples))
        self.assertTrue(any(not s for s in samples))

    data_next_int = [
        (0, 1),
        (-1, 0),
        (-1, 1),
        (0, max_int()),
        (-max_int(), 0),
        (-max_int() // 2, max_int() // 2),
    ]

    @ddt.idata(data_next_int)
    @ddt.unpack
    def test_next_int(self, lo, hi):
        for _ in range(0, 100000):
            self.assertTrue(lo <= randomizer().next_int(lo, hi) < hi)

    data_next_float = [
        (0.0, 1.0),
        (-1.0, 0.0),
        (-1.0, 1.0),
        (0.0, max_float()),
        (-max_float(), 0.0),
        (-max_float() * 0.5, max_float() * 0.5),
    ]

    @ddt.idata(data_next_float)
    @ddt.unpack
    def test_next_float(self, lo, hi):
        for _ in range(0, 100000):
            self.assertTrue(lo <= randomizer().next_float(lo, hi) <= hi)

    def test_next_float__assertion_error(self):
        with self.assertRaises(AssertionError):
            randomizer().next_float(-max_float(), max_float())

    def test_random_string(self):
        for _ in range(1000):
            chars = "".join(sorted(set(randomizer().random_alphanumeric(50))))
            length = randomizer().next_int(1000, 2000)

            result = randomizer().random_string(chars, length)

            self.assertEqual(len(result), length)
            self.assertTrue(all(c in chars for c in result))

    def test_random_ascii(self):
        for _ in range(1000):
            length = randomizer().next_int(1000, 2000)

            result = randomizer().random_ascii(length)

            self.assertEqual(len(result), length)
            self.assertTrue(all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for c in result))

    def test_random_alphanumeric(self):
        for _ in range(1000):
            length = randomizer().next_int(1000, 2000)

            result = randomizer().random_alphanumeric(length)

            self.assertEqual(len(result), length)
            self.assertTrue(all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for c in result))

    def test_random_hex(self):
        for _ in range(1000):
            length = randomizer().next_int(1000, 2000)

            result = randomizer().random_hex(length)

            self.assertEqual(len(result), length)
            self.assertTrue(all(c in "0123456789ABCDEF" for c in result))

    def test_random_oct(self):
        for _ in range(1000):
            length = randomizer().next_int(1000, 2000)

            result = randomizer().random_oct(length)

            self.assertEqual(len(result), length)
            self.assertTrue(all(c in "01234567" for c in result))

    def test_random_unit_vector(self):
        for _ in range(1000):
            length = randomizer().next_int(1, 2000)

            result = randomizer().random_unit_vector(length)

            self.assertEqual(len(result), length)
            self.assertTrue(all(-1.0 <= x <= 1.0 for x in result))
            self.assertAlmostEqual(sum((x * x for x in result), 0.0), 1.0, delta=1.0e-9)

    def test_random_datetime(self):
        for _ in range(1000):
            a = randomizer().random_datetime()
            b = randomizer().random_datetime()
            begin = min(a, b)
            end = max(a, b)
            result = randomizer().random_datetime(begin, end)

            self.assertTrue(dt_utc_min() <= begin <= result <= end <= dt_utc_max())

    def test_random_date(self):
        for _ in range(1000):
            a = randomizer().random_date()
            b = randomizer().random_date()
            begin = min(a, b)
            end = max(a, b)
            result = randomizer().random_date(begin, end)

            self.assertTrue(dt_utc_min().date() <= begin <= result <= end <= dt_utc_max().date())

    def test_random_time(self):
        for _ in range(1000):
            a = randomizer().random_time()
            b = randomizer().random_time()
            begin = min(a, b)
            end = max(a, b)
            result = randomizer().random_time(begin, end)

            self.assertTrue(dt_utc_min().timetz() <= begin <= result <= end <= dt_utc_max().timetz())

    def test_sample(self):
        for _ in range(1000):
            population = list(itertools.accumulate(randomizer().next_int(1, 10)
                                                   for _ in range(randomizer().next_int(100, 200))))
            count_func = lambda x: 1 + x % 3
            k = randomizer().next_int(1, len(population))

            result = randomizer().sample(population, count_func, k)

            self.assertTrue(len(result), k)
            self.assertTrue(all(elem in population for elem in result))
            self.assertTrue(all(result.count(elem) <= count_func(elem) for elem in result))

    def test_sample__without_k(self):
        for _ in range(1000):
            population = list(itertools.accumulate(randomizer().next_int(1, 10)
                                                   for _ in range(randomizer().next_int(100, 200))))
            count_func = lambda x: 1 + x % 3

            result = randomizer().sample(population, count_func)

            self.assertIn(result, population)

    def test_choose(self):
        for _ in range(1000):
            population = list(itertools.accumulate(randomizer().next_int(1, 10)
                                                   for _ in range(randomizer().next_int(100, 200))))
            weight_func = lambda x: float(1 + x % 3)
            k = randomizer().next_int(1, len(population))

            result = randomizer().choose(population, weight_func, k)

            self.assertTrue(len(result), k)
            self.assertTrue(all(elem in population for elem in result))

    def test_choose__without_k(self):
        for _ in range(1000):
            population = list(itertools.accumulate(randomizer().next_int(1, 10)
                                                   for _ in range(randomizer().next_int(100, 200))))
            weight_func = lambda x: float(1 + x % 3)

            result = randomizer().choose(population, weight_func)

            self.assertIn(result, population)

    def test_shuffle(self):
        for _ in range(1000):
            data = list(itertools.accumulate(randomizer().next_int(1, 10)
                                             for _ in range(randomizer().next_int(100, 200))))

            result = randomizer().shuffle(data)

            self.assertIsNot(result, data)
            self.assertTrue(len(result), len(data))
            self.assertTrue(all(elem in data for elem in result))
