import dataclasses
import datetime
import math
import unittest
from decimal import Decimal

import ddt

from iker.common.utils.testutils import nested_approx, return_callee, throw_callee


@dataclasses.dataclass(eq=True, frozen=True)
class DummyDataclass(object):
    dummy_bool: bool
    dummy_int: int
    dummy_str: str


@ddt.ddt
class TestUtilsTest(unittest.TestCase):
    data_nested_approx = [
        None,
        True,
        1,
        -1,
        1.0,
        -1.0,
        math.inf,
        -math.inf,
        math.nan,
        "dummy",
        Decimal("1.000000000000000000001"),
        Decimal("-1.000000000000000000001"),
        Decimal("inf"),
        Decimal("-inf"),
        Decimal("nan"),
        datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
        DummyDataclass(True, 1, "dummy"),
        (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
        (-0.001, -0.01, -0.1, -1.0, -10.0, -100.0, -1000.0),
        [
            None,
            True,
            1,
            1.0,
            "dummy",
            Decimal("1.000000000000000000001"),
            datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
        ],
        {
            "none": None,
            "bool": True,
            "int": 1,
            "float": 1.0,
            "str": "dummy",
            "decimal": Decimal("1.000000000000000000001"),
            "tuple": (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
            "list": [
                None,
                True,
                1,
                1.0,
                "dummy",
                Decimal("1.000000000000000000001"),
                datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            ],
        },
    ]

    @ddt.idata(data_nested_approx)
    def test_nested_approx(self, data):
        assert data == nested_approx(data, nan_ok=True)

    def test_nested_approx__comprehensive(self):
        expect = [
            None,
            True,
            1,
            1.0,
            "dummy",
            Decimal("1.000000000000000000001"),
            datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
            [
                None,
                True,
                1,
                1.0,
                "dummy",
                Decimal("1.000000000000000000001"),
                datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            ],
            {
                "none": None,
                "bool": True,
                "int": 1,
                "float": 1.0,
                "str": "dummy",
                "decimal": Decimal("1.000000000000000000001"),
                "tuple": (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
                "list": [
                    None,
                    True,
                    1,
                    1.0,
                    "dummy",
                    Decimal("1.000000000000000000001"),
                    datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
                ],
            },
        ]

        actual = [
            None,
            True,
            1,
            1.0,
            "dummy",
            Decimal("1.000000000000000000001"),
            datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
            [
                None,
                True,
                1,
                1.0,
                "dummy",
                Decimal("1.000000000000000000001"),
                datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            ],
            {
                "none": None,
                "bool": True,
                "int": 1,
                "float": 1.0,
                "str": "dummy",
                "decimal": Decimal("1.000000000000000000001"),
                "tuple": (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
                "list": [
                    None,
                    True,
                    1,
                    1.0,
                    "dummy",
                    Decimal("1.000000000000000000001"),
                    datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
                ],
            },
        ]

        assert expect == nested_approx(actual)
        assert actual == nested_approx(expect)

    def test_nested_approx__comprehensive_relative_tolerance(self):
        expect = [
            None,
            True,
            1,
            1.0,
            "dummy",
            Decimal("1.000000000000000000001"),
            datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
            [
                None,
                True,
                1,
                1.0,
                "dummy",
                Decimal("1.000000000000000000001"),
                datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            ],
            {
                "none": None,
                "bool": True,
                "int": 1,
                "float": 1.0,
                "str": "dummy",
                "decimal": Decimal("1.000000000000000000001"),
                "tuple": (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
                "list": [
                    None,
                    True,
                    1,
                    1.0,
                    "dummy",
                    Decimal("1.000000000000000000001"),
                    datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
                ],
            },
        ]

        actual = [
            None,
            True,
            1,
            1.0 + 1e-6,
            "dummy",
            Decimal("1.000000000000000000001") * Decimal(1.0 + 1e-6),
            datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            (0.001 + 1e-9, 0.01 + 1e-8, 0.1 + 1e-7, 1.0 + 1e-6, 10.0 + 1e-5, 100.0 + 1e-4, 1000.0 + 1e-3),
            [
                None,
                True,
                1,
                1.0 + 1e-6,
                "dummy",
                Decimal("1.000000000000000000001") * Decimal(1.0 + 1e-6),
                datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            ],
            {
                "none": None,
                "bool": True,
                "int": 1,
                "float": 1.0 - 1e-6,
                "str": "dummy",
                "decimal": Decimal("1.000000000000000000001") * Decimal(1.0 - 1e-6),
                "tuple": (0.001 - 1e-9, 0.01 - 1e-8, 0.1 - 1e-7, 1.0 - 1e-6, 10.0 - 1e-5, 100.0 - 1e-4, 1000.0 - 1e-3),
                "list": [
                    None,
                    True,
                    1,
                    1.0 - 1e-6,
                    "dummy",
                    Decimal("1.000000000000000000001") * Decimal(1.0 - 1e-6),
                    datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
                ],
            },
        ]

        assert expect == nested_approx(actual, rel=1.00001e-6)
        assert actual == nested_approx(expect, rel=1.00001e-6)

    def test_nested_approx__comprehensive_absolute_tolerance(self):
        expect = [
            None,
            True,
            1,
            1.0,
            "dummy",
            Decimal("1.000000000000000000001"),
            datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
            [
                None,
                True,
                1,
                1.0,
                "dummy",
                Decimal("1.000000000000000000001"),
                datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            ],
            {
                "none": None,
                "bool": True,
                "int": 1,
                "float": 1.0,
                "str": "dummy",
                "decimal": Decimal("1.000000000000000000001"),
                "tuple": (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
                "list": [
                    None,
                    True,
                    1,
                    1.0,
                    "dummy",
                    Decimal("1.000000000000000000001"),
                    datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
                ],
            },
        ]

        actual = [
            None,
            True,
            1,
            1.0 + 1e-6,
            "dummy",
            Decimal("1.000000000000000000001") + Decimal(1e-6),
            datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            (0.001 + 1e-6, 0.01 + 1e-6, 0.1 + 1e-6, 1.0 + 1e-6, 10.0 + 1e-6, 100.0 + 1e-6, 1000.0 + 1e-6),
            [
                None,
                True,
                1,
                1.0 + 1e-6,
                "dummy",
                Decimal("1.000000000000000000001") + Decimal(1e-6),
                datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
            ],
            {
                "none": None,
                "bool": True,
                "int": 1,
                "float": 1.0 - 1e-6,
                "str": "dummy",
                "decimal": Decimal("1.000000000000000000001") - Decimal(1e-6),
                "tuple": (0.001 - 1e-6, 0.01 - 1e-6, 0.1 - 1e-6, 1.0 - 1e-6, 10.0 - 1e-6, 100.0 - 1e-6, 1000.0 - 1e-6),
                "list": [
                    None,
                    True,
                    1,
                    1.0 - 1e-6,
                    "dummy",
                    Decimal("1.000000000000000000001") - Decimal(1e-6),
                    datetime.datetime(2000, 12, 31, 12, 30, 59, 123456),
                ],
            },
        ]

        assert expect == nested_approx(actual, abs=1.00001e-6)
        assert actual == nested_approx(expect, abs=1.00001e-6)

    def test_return_callee(self):
        callee = return_callee()

        self.assertIsNone(callee())
        self.assertIsNone(callee(None))
        self.assertIsNone(callee(1.0))
        self.assertIsNone(callee("dummy_string"))
        self.assertIsNone(callee(True, 1, 1.0, "dummy_string"))
        self.assertIsNone(callee(dummy_none=None))
        self.assertIsNone(callee(dummy_bool=True))
        self.assertIsNone(callee(dummy_int=1))
        self.assertIsNone(callee(dummy_float=1.0))
        self.assertIsNone(callee(dummy_str="dummy_string"))
        self.assertIsNone(callee(None,
                                 True,
                                 1,
                                 1.0,
                                 "dummy_string",
                                 dummy_none=None,
                                 dummy_bool=True,
                                 dummy_int=1,
                                 dummy_float=1.0,
                                 dummy_str="dummy_string"))

        callee.assert_called_once_with()()
        callee.assert_called_once_with()(None)
        callee.assert_called_once_with()(True)
        callee.assert_called_once_with()(1)
        callee.assert_called_once_with()(1.0)
        callee.assert_called_once_with()("dummy_string")
        callee.assert_called_once_with()(True, 1, 1.0, "dummy_string")
        callee.assert_called_once_with()(dummy_none=None)
        callee.assert_called_once_with()(dummy_bool=True)
        callee.assert_called_once_with()(dummy_int=1)
        callee.assert_called_once_with()(dummy_float=1.0)
        callee.assert_called_once_with()(dummy_str="dummy_string")
        callee.assert_called_once_with()(None,
                                         True,
                                         1,
                                         1.0,
                                         "dummy_string",
                                         dummy_none=None,
                                         dummy_bool=True,
                                         dummy_int=1,
                                         dummy_float=1.0,
                                         dummy_str="dummy_string")

    def test_return_callee__multiple_calls(self):
        callee_0 = return_callee(0)
        callee_1 = return_callee(1)
        callee_2 = return_callee(4)
        callee_3 = return_callee(9)

        self.assertEqual(callee_1(1), 1)
        self.assertEqual(callee_2(2), 4)
        self.assertEqual(callee_2(2), 4)
        self.assertEqual(callee_3(3), 9)
        self.assertEqual(callee_3(3), 9)
        self.assertEqual(callee_3(3), 9)

        callee_0.assert_not_called()
        callee_0.assert_not_called_with()(1)
        callee_0.assert_not_called_with()(2)
        callee_0.assert_not_called_with()(3)

        callee_1.assert_called()
        callee_1.assert_called_with()(1)
        callee_1.assert_not_called_with()(2)
        callee_1.assert_not_called_with()(3)
        callee_1.assert_called_once()
        callee_1.assert_called_once_with()(1)
        callee_1.assert_called_times(1)
        callee_1.assert_called_times_with(1)(1)

        callee_2.assert_called()
        callee_2.assert_not_called_with()(1)
        callee_2.assert_called_with()(2)
        callee_2.assert_not_called_with()(3)
        callee_2.assert_called_times(2)
        callee_2.assert_called_times_with(2)(2)

        callee_3.assert_called()
        callee_3.assert_not_called_with()(1)
        callee_3.assert_not_called_with()(2)
        callee_3.assert_called_with()(3)
        callee_3.assert_called_times(3)
        callee_3.assert_called_times_with(3)(3)

    def test_throw_callee(self):
        callee = throw_callee(ValueError)

        with self.assertRaises(ValueError):
            callee(object())
