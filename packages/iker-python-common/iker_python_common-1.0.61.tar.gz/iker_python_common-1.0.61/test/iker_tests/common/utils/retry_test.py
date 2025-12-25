import unittest

import ddt

from iker.common.utils import retry


@ddt.ddt
class RetryTest(unittest.TestCase):
    data_retry__ok = [
        ("dummy-content", 1, 0),
        ("dummy-content", 1, 3),
        ("Old MacDonald had a farm", 2, 4),
        ("Ee-i-ee-i-o", 1, 5),
    ]

    @ddt.idata(data_retry__ok)
    @ddt.unpack
    def test_retry__ok(self, content, wait, retrials):
        result = []

        @retry.retry(wait=wait, retrials=retrials)
        def callee(text):
            result.append(text)

        callee(content)
        self.assertEqual([content], result)

    data_retry__with_timeout = [
        ("dummy-content", 5, 3, 10),
        ("Old MacDonald had a farm", 2, 4, 6),
        ("Ee-i-ee-i-o", 1, 5, 3),
    ]

    @ddt.idata(data_retry__with_timeout)
    @ddt.unpack
    def test_retry__with_timeout(self, content, wait, retrials, timeout):
        result = []

        @retry.retry(wait=wait, retrials=retrials, timeout=timeout)
        def callee(text):
            result.append(text)
            raise ValueError("dummy value error")

        with self.assertRaises(RuntimeError):
            callee(content)

        self.assertTrue(len(result) < retrials + 1)

    data_retry__with_timeout_only = [
        ("dummy-content", 5, 10),
        ("Old MacDonald had a farm", 2, 6),
        ("Ee-i-ee-i-o", 1, 3),
    ]

    @ddt.idata(data_retry__with_timeout_only)
    @ddt.unpack
    def test_retry__with_timeout_only(self, content, wait, timeout):
        result = []

        @retry.retry(wait=wait, timeout=timeout)
        def callee(text):
            result.append(text)
            raise ValueError("dummy value error")

        with self.assertRaises(RuntimeError):
            callee(content)

    data_retry = [
        ("dummy-content", 1, 3),
        ("Old MacDonald had a farm", 2, 4),
        ("Ee-i-ee-i-o", 1, 5),
    ]

    @ddt.idata(data_retry)
    @ddt.unpack
    def test_retry(self, content, wait, retrials):
        result = []

        @retry.retry(wait=wait, retrials=retrials)
        def callee(text):
            result.append(text)
            raise ValueError("dummy value error")

        with self.assertRaises(RuntimeError):
            callee(content)

        self.assertEqual([content for _ in range(retrials + 1)], result)

    data_retry__on_retry_instance = [
        ("dummy-content", 1, 3),
        ("Old MacDonald had a farm", 2, 4),
        ("Ee-i-ee-i-o", 1, 5),
    ]

    @ddt.idata(data_retry__on_retry_instance)
    @ddt.unpack
    def test_retry__on_retry_instance(self, content, wait, retrials):
        result = []

        class Callee(retry.Retry):
            def __init__(self):
                self.attempts = []

            def on_attempt(self, attempt):
                self.attempts.append(attempt)

            def execute(self, *args, **kwargs):
                result.append(args[0])
                raise ValueError("dummy value error")

        callee = Callee()

        with self.assertRaises(RuntimeError):
            retry.retry(wait=wait, retrials=retrials)(callee)(content)

        self.assertEqual([content for _ in range(retrials + 1)], result)
        self.assertTrue(all(a.next_wait == wait for a in callee.attempts))

    data_retry_exponent = [
        ("dummy-content", 1, 4, 3),
        ("Old MacDonald had a farm", 2, 1, 4),
        ("Ee-i-ee-i-o", 1, 10, 5),
    ]

    @ddt.idata(data_retry_exponent)
    @ddt.unpack
    def test_retry_exponent(self, content, wait_exponent_init, wait_exponent_max, retrials):
        result = []

        @retry.retry_exponent(wait_exponent_init=wait_exponent_init, wait_exponent_max=wait_exponent_max,
                              retrials=retrials)
        def callee(text):
            result.append(text)
            raise ValueError("dummy value error")

        with self.assertRaises(RuntimeError):
            callee(content)

        self.assertEqual([content for _ in range(retrials + 1)], result)

    data_retry_exponent__on_retry_instance = [
        ("dummy-content", 1, 4, 3),
        ("Old MacDonald had a farm", 2, 1, 4),
        ("Ee-i-ee-i-o", 1, 10, 5),
    ]

    @ddt.idata(data_retry_exponent__on_retry_instance)
    @ddt.unpack
    def test_retry_exponent__on_retry_instance(self, content, wait_exponent_init, wait_exponent_max, retrials):
        result = []

        class Callee(retry.Retry):
            def __init__(self):
                self.attempts = []

            def on_attempt(self, attempt):
                self.attempts.append(attempt)

            def execute(self, *args, **kwargs):
                result.append(args[0])
                raise ValueError("dummy value error")

        callee = Callee()

        with self.assertRaises(RuntimeError):
            retry.retry_exponent(wait_exponent_init, wait_exponent_max, retrials)(callee)(content)

        self.assertEqual([content for _ in range(retrials + 1)], result)
        self.assertTrue(all(
            a.next_wait == min(wait_exponent_init * (2 ** (a.number - 1)), wait_exponent_max) for a in callee.attempts))

    data_retry_random = [
        ("dummy-content", 1, 4, 3),
        ("Old MacDonald had a farm", 2, 3, 4),
        ("Ee-i-ee-i-o", 1, 10, 5),
    ]

    @ddt.idata(data_retry_random)
    @ddt.unpack
    def test_retry_random(self, content, wait_random_min, wait_random_max, retrials):
        result = []

        @retry.retry_random(wait_random_min=wait_random_min, wait_random_max=wait_random_max, retrials=retrials)
        def callee(text):
            result.append(text)
            raise ValueError("dummy value error")

        with self.assertRaises(RuntimeError):
            callee(content)

        self.assertEqual([content for _ in range(retrials + 1)], result)

    data_retry_random__on_retry_instance = [
        ("dummy-content", 1, 4, 3),
        ("Old MacDonald had a farm", 2, 3, 4),
        ("Ee-i-ee-i-o", 1, 10, 5),
    ]

    @ddt.idata(data_retry_random__on_retry_instance)
    @ddt.unpack
    def test_retry_random__on_retry_instance(self, content, wait_random_min, wait_random_max, retrials):
        result = []

        class Callee(retry.Retry):
            def __init__(self):
                self.attempts = []

            def on_attempt(self, attempt):
                self.attempts.append(attempt)

            def execute(self, *args, **kwargs):
                result.append(args[0])
                raise ValueError("dummy value error")

        callee = Callee()

        with self.assertRaises(RuntimeError):
            retry.retry_random(wait_random_min, wait_random_max, retrials)(callee)(content)

        self.assertEqual([content for _ in range(retrials + 1)], result)
        self.assertTrue(all(wait_random_min <= a.next_wait <= wait_random_max for a in callee.attempts))
