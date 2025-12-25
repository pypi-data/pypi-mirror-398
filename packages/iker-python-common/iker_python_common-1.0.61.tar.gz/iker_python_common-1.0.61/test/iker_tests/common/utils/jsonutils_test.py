import dataclasses
import datetime
import math
import unittest
from collections.abc import Mapping, Sequence
from typing import SupportsFloat, SupportsInt

import ddt

from iker.common.utils.jsonutils import asterisk, json_get, json_set
from iker.common.utils.jsonutils import json_compare, json_difference, json_equals
from iker.common.utils.jsonutils import json_reformat, json_sanitize, json_traverse
from iker.common.utils.randutils import randomizer


@dataclasses.dataclass(eq=True, frozen=True)
class PrefixedStr(object):
    prefix: str
    value: str

    def __str__(self):
        return self.prefix + "::" + self.value


@dataclasses.dataclass(eq=True, frozen=True)
class MultipliedInt(SupportsInt):
    value: int
    multiplier: int = 1

    def __int__(self):
        return self.value * self.multiplier


@dataclasses.dataclass(eq=True, frozen=True)
class MultipliedFloat(SupportsFloat):
    value: float
    multiplier: float = 1

    def __float__(self):
        return self.value * self.multiplier


@dataclasses.dataclass(frozen=True)
class WrappedList(Sequence):
    value: list

    def __len__(self):
        return len(self.value)

    def __getitem__(self, index):
        return self.value[index]


@dataclasses.dataclass(frozen=True)
class WrappedDict(Mapping):
    value: dict

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __getitem__(self, index):
        return self.value[index]


@ddt.ddt
class JsonUtilsTest(unittest.TestCase):
    data_json_get = [
        (None, [], None),
        (True, [], True),
        (False, [], False),
        (1, [], 1),
        (-1, [], -1),
        (0, [], 0),
        (1.0, [], 1.0),
        (-1.0, [], -1.0),
        (0.0, [], 0.0),
        (1.0e9, [], 1.0e9),
        (-1.0e-9, [], -1.0e-9),
        (math.nan, [], math.nan),
        (math.inf, [], math.inf),
        (-math.inf, [], -math.inf),
        ("", [], ""),
        ("dummy", [], "dummy"),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [0], None),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [1], True),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [2], 1),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [3], 1.0),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [4], math.nan),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [5], math.inf),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [6], "dummy"),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [7], None),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-8], None),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-7], None),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-6], True),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-5], 1),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-4], 1.0),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-3], math.nan),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-2], math.inf),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [-1], "dummy"),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [], [None, True, 1, 1.0, math.nan, math.inf, "dummy"]),
        ([None, True, 1, 1.0, math.nan, math.inf, "dummy"], [""], None),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            ["none"],
            None,
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            ["bool"],
            True,
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            ["int"],
            1,
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            ["float"],
            1.0,
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            ["nan"],
            math.nan,
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            ["inf"],
            math.inf,
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            ["str"],
            "dummy",
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            [""],
            None,
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            [],
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
        ),
        (
            {"none": None, "bool": True, "int": 1, "float": 1.0, "nan": math.nan, "inf": math.inf, "str": "dummy"},
            [0],
            None,
        ),
    ]

    @ddt.idata(data_json_get)
    @ddt.unpack
    def test_json_get(self, data, node_path, expect):
        self.assertTrue(json_compare(json_get(data, *node_path), expect))

    data_json_get__comprehensive = [
        (
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list": [None, True, 1, 1.0, math.nan, math.inf, "dummy"],
            },
            [
                (["none"], None),
                (
                    ["bool"],
                    {
                        "bool_true": True,
                        "bool_false": False,
                    },
                ),
                (["bool", "bool_true"], True),
                (["bool", "bool_false"], False),
                (["bool", ""], None),
                (
                    ["int"],
                    {
                        "int_one": 1,
                        "int_minus_one": -1,
                        "int_zero": 0,
                    },
                ),
                (["int", "int_one"], 1),
                (["int", "int_minus_one"], -1),
                (["int", "int_zero"], 0),
                (["int", ""], None),
                (
                    ["float"],
                    {
                        "float_one": 1.0,
                        "float_minus_one": -1.0,
                        "float_zero": 0.0,
                        "float_one_e_nine": 1.0e9,
                        "float_minus_one_e_minus_nine": -1.0e-9,
                        "float_nan": math.nan,
                        "float_inf": math.inf,
                        "float_minus_inf": -math.inf,
                    },
                ),
                (["float", "float_one"], 1.0),
                (["float", "float_minus_one"], -1.0),
                (["float", "float_zero"], 0.0),
                (["float", "float_one_e_nine"], 1.0e9),
                (["float", "float_minus_one_e_minus_nine"], -1.0e-9),
                (["float", "float_nan"], math.nan),
                (["float", "float_inf"], math.inf),
                (["float", "float_minus_inf"], -math.inf),
                (["float", ""], None),
                (
                    ["str"],
                    {
                        "str_empty": "",
                        "str": "dummy",
                    },
                ),
                (["str", "str_empty"], ""),
                (["str", "str"], "dummy"),
                (["str", ""], None),
                (["list"], [None, True, 1, 1.0, math.nan, math.inf, "dummy"]),
                (["list", 0], None),
                (["list", 1], True),
                (["list", 2], 1),
                (["list", 3], 1.0),
                (["list", 4], math.nan),
                (["list", 5], math.inf),
                (["list", 6], "dummy"),
                (["list", 7], None),
                (["list", -8], None),
                (["list", -7], None),
                (["list", -6], True),
                (["list", -5], 1),
                (["list", -4], 1.0),
                (["list", -3], math.nan),
                (["list", -2], math.inf),
                (["list", -1], "dummy"),
                ([""], None),
                (["", 0], None),
                ([0, ""], None),
                (
                    [],
                    {
                        "none": None,
                        "bool": {
                            "bool_true": True,
                            "bool_false": False,
                        },
                        "int": {
                            "int_one": 1,
                            "int_minus_one": -1,
                            "int_zero": 0,
                        },
                        "float": {
                            "float_one": 1.0,
                            "float_minus_one": -1.0,
                            "float_zero": 0.0,
                            "float_one_e_nine": 1.0e9,
                            "float_minus_one_e_minus_nine": -1.0e-9,
                            "float_nan": math.nan,
                            "float_inf": math.inf,
                            "float_minus_inf": -math.inf,
                        },
                        "str": {
                            "str_empty": "",
                            "str": "dummy",
                        },
                        "list": [None, True, 1, 1.0, math.nan, math.inf, "dummy"],
                    },
                ),
            ],
        ),
    ]

    @ddt.idata(data_json_get__comprehensive)
    @ddt.unpack
    def test_json_get__comprehensive(self, data, queries):
        for node_path, expect in queries:
            self.assertTrue(json_compare(json_get(data, *node_path), expect))

    def test_json_set(self):
        queries = [
            (["none"], None),
            (
                ["bool"],
                {
                    "bool_true": True,
                    "bool_false": False,
                },
            ),
            (["bool", "bool_true"], True),
            (["bool", "bool_false"], False),
            (
                ["int"],
                {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                },
            ),
            (["int", "int_one"], 1),
            (["int", "int_minus_one"], -1),
            (["int", "int_zero"], 0),
            (
                ["float"],
                {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                },
            ),
            (["float", "float_one"], 1.0),
            (["float", "float_minus_one"], -1.0),
            (["float", "float_zero"], 0.0),
            (["float", "float_one_e_nine"], 1.0e9),
            (["float", "float_minus_one_e_minus_nine"], -1.0e-9),
            (["float", "float_nan"], math.nan),
            (["float", "float_inf"], math.inf),
            (["float", "float_minus_inf"], -math.inf),
            (
                ["str"],
                {
                    "str_empty": "",
                    "str": "dummy",
                },
            ),
            (["str", "str_empty"], ""),
            (["str", "str"], "dummy"),
            (["list"], [None, True, 1, 1.0, math.nan, math.inf, "dummy"]),
            (["list", 0], None),
            (["list", 1], True),
            (["list", 2], 1),
            (["list", 3], 1.0),
            (["list", 4], math.nan),
            (["list", 5], math.inf),
            (["list", 6], "dummy"),
            (["list_list"], [[None], [True], [1], [1.0], [math.nan], [math.inf], ["dummy"]]),
            (["list_list", 0], [None]),
            (["list_list", 1], [True]),
            (["list_list", 2], [1]),
            (["list_list", 3], [1.0]),
            (["list_list", 4], [math.nan]),
            (["list_list", 5], [math.inf]),
            (["list_list", 6], ["dummy"]),
            (["list_list", 0, 0], None),
            (["list_list", 1, 0], True),
            (["list_list", 2, 0], 1),
            (["list_list", 3, 0], 1.0),
            (["list_list", 4, 0], math.nan),
            (["list_list", 5, 0], math.inf),
            (["list_list", 6, 0], "dummy"),
            (
                ["list_dict"],
                [{"v": None}, {"v": True}, {"v": 1}, {"v": 1.0}, {"v": math.nan}, {"v": math.inf}, {"v": "dummy"}],
            ),
            (["list_dict", 0], {"v": None}),
            (["list_dict", 1], {"v": True}),
            (["list_dict", 2], {"v": 1}),
            (["list_dict", 3], {"v": 1.0}),
            (["list_dict", 4], {"v": math.nan}),
            (["list_dict", 5], {"v": math.inf}),
            (["list_dict", 6], {"v": "dummy"}),
            (["list_dict", 0, "v"], None),
            (["list_dict", 1, "v"], True),
            (["list_dict", 2, "v"], 1),
            (["list_dict", 3, "v"], 1.0),
            (["list_dict", 4, "v"], math.nan),
            (["list_dict", 5, "v"], math.inf),
            (["list_dict", 6, "v"], "dummy"),
        ]

        expect = {
            "none": None,
            "bool": {
                "bool_true": True,
                "bool_false": False,
            },
            "int": {
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
            },
            "float": {
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
            },
            "str": {
                "str_empty": "",
                "str": "dummy",
            },
            "list": [None, True, 1, 1.0, math.nan, math.inf, "dummy"],
            "list_list": [[None], [True], [1], [1.0], [math.nan], [math.inf], ["dummy"]],
            "list_dict":
                [{"v": None}, {"v": True}, {"v": 1}, {"v": 1.0}, {"v": math.nan}, {"v": math.inf}, {"v": "dummy"}],
        }

        for _ in range(1000):
            obj = {}
            for _, (node_path, value) in sorted((randomizer().next_float(), query) for query in queries):
                self.assertTrue(json_set(obj, value, *node_path))
            self.assertTrue(json_compare(obj, expect))

    def test_json_set__asterisk(self):
        obj = []
        for v in range(1000):
            self.assertTrue(json_set(obj, v, asterisk))
        self.assertTrue(json_compare(obj, list(range(1000))))

    data_json_traverse = [
        (None, None),
        (True, True),
        (False, False),
        (1, 1),
        (-1, -1),
        (0, 0),
        (MultipliedInt(-1, 100), -100),
        (MultipliedInt(1, 100), 100),
        (1.0, 1.0),
        (-1.0, -1.0),
        (0.0, 0.0),
        (1.0e9, 1.0e9),
        (-1.0e-9, -1.0e-9),
        (math.nan, math.nan),
        (math.inf, math.inf),
        (-math.inf, -math.inf),
        (MultipliedFloat(1.0, 100.0), 100.0),
        (MultipliedFloat(-1.0, 100.0), -100.0),
        ("", ""),
        ("dummy", "dummy"),
        (
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"],
        ),
        (
            (None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"),
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"],
        ),
        (
            {
                "none": None,
                "bool_true": True,
                "bool_false": False,
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": MultipliedInt(1, -1000),
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
                "float_wrapped": MultipliedFloat(1.0, -1000.0),
                "str_empty": "",
                "str": "dummy",
            },
            {
                "none": None,
                "bool_true": True,
                "bool_false": False,
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": -1000,
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
                "float_wrapped": -1000.0,
                "str_empty": "",
                "str": "dummy",
            },
        ),
        (
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": MultipliedInt(1, -1000),
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": MultipliedFloat(1.0, -1000.0),
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple":
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
            },
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": -1000,
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": -1000.0,
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            },
        ),
        (
            WrappedDict({
                PrefixedStr("key", "none"): None,
                PrefixedStr("key", "bool"): WrappedDict({
                    PrefixedStr("key", "bool_true"): True,
                    PrefixedStr("key", "bool_false"): False,
                }),
                PrefixedStr("key", "int"): WrappedDict({
                    PrefixedStr("key", "int_one"): 1,
                    PrefixedStr("key", "int_minus_one"): -1,
                    PrefixedStr("key", "int_zero"): 0,
                    PrefixedStr("key", "int_wrapped"): MultipliedInt(1, -1000),
                }),
                PrefixedStr("key", "float"): WrappedDict({
                    PrefixedStr("key", "float_one"): 1.0,
                    PrefixedStr("key", "float_minus_one"): -1.0,
                    PrefixedStr("key", "float_zero"): 0.0,
                    PrefixedStr("key", "float_one_e_nine"): 1.0e9,
                    PrefixedStr("key", "float_minus_one_e_minus_nine"): -1.0e-9,
                    PrefixedStr("key", "float_nan"): math.nan,
                    PrefixedStr("key", "float_inf"): math.inf,
                    PrefixedStr("key", "float_minus_inf"): -math.inf,
                    PrefixedStr("key", "float_wrapped"): MultipliedFloat(1.0, -1000.0),
                }),
                PrefixedStr("key", "str"): WrappedDict({
                    PrefixedStr("key", "str_empty"): "",
                    PrefixedStr("key", "str"): "dummy",
                }),
                PrefixedStr("key", "list"): WrappedList(
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"]),
                PrefixedStr("key", "tuple"):
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
            }),
            {
                "key::none": None,
                "key::bool": {
                    "key::bool_true": True,
                    "key::bool_false": False,
                },
                "key::int": {
                    "key::int_one": 1,
                    "key::int_minus_one": -1,
                    "key::int_zero": 0,
                    "key::int_wrapped": -1000,
                },
                "key::float": {
                    "key::float_one": 1.0,
                    "key::float_minus_one": -1.0,
                    "key::float_zero": 0.0,
                    "key::float_one_e_nine": 1.0e9,
                    "key::float_minus_one_e_minus_nine": -1.0e-9,
                    "key::float_nan": math.nan,
                    "key::float_inf": math.inf,
                    "key::float_minus_inf": -math.inf,
                    "key::float_wrapped": -1000.0,
                },
                "key::str": {
                    "key::str_empty": "",
                    "key::str": "dummy",
                },
                "key::list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "key::tuple":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            },
        ),
    ]

    @ddt.idata(data_json_traverse)
    @ddt.unpack
    def test_json_traverse(self, data, expect):
        self.assertTrue(json_compare(json_traverse(data), expect))

    def test_json_traverse__object_array_visitor(self):
        data = {
            "none": None,
            "bool": {
                "bool_true": True,
                "bool_false": False,
            },
            "int": {
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": MultipliedInt(1, -1000),
            },
            "float": {
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
                "float_wrapped": MultipliedFloat(1.0, -1000.0),
            },
            "str": {
                "str_empty": "",
                "str": "dummy",
            },
            "list":
                [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            "tuple":
                (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
        }

        expect = {
            "none": None,
            "bool": {
                "bool_true": True,
                "bool_false": False,
            },
            "int": {
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": None,
            },
            "float": {
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
                "float_wrapped": None,
            },
            "str": [
                ["str_empty", ""],
                ["str", "dummy"],
            ],
            "list":
                [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"]
                + [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, None, math.inf, -math.inf, "", "dummy"],
            "tuple":
                [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"]
                + [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, None, math.inf, -math.inf, "", "dummy"],
        }

        def object_visitor(node_path, old_object, new_object):
            if node_path == ["str"]:
                return [[key, value] for key, value in new_object.items()]
            return new_object

        def array_visitor(node_path, old_array, new_array):
            return list(old_array) + list(new_array)

        def stop_func(node_path) -> bool:
            return node_path in (
                ["int", "int_wrapped"],
                ["float", "float_wrapped"],
                ["list", 11],
                ["tuple", 11],
                [0],
                ["dummy"],
            )

        self.assertTrue(json_compare(json_traverse(data,
                                                   object_visitor=object_visitor,
                                                   array_visitor=array_visitor,
                                                   stop_func=stop_func),
                                     expect))

    data_json_reformat = [
        (None, None),
        (True, True),
        (False, False),
        (1, 1),
        (-1, -1),
        (0, 0),
        (MultipliedInt(-1, 100), -100),
        (MultipliedInt(1, 100), 100),
        (1.0, 1.0),
        (-1.0, -1.0),
        (0.0, 0.0),
        (1.0e9, 1.0e9),
        (-1.0e-9, -1.0e-9),
        (math.nan, math.nan),
        (math.inf, math.inf),
        (-math.inf, -math.inf),
        (MultipliedFloat(1.0, 100.0), 100.0),
        (MultipliedFloat(-1.0, 100.0), -100.0),
        ("", ""),
        ("dummy", "dummy"),
        (
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"],
        ),
        (
            (None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"),
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"],
        ),
        (
            {
                "none": None,
                "bool_true": True,
                "bool_false": False,
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": MultipliedInt(1, -1000),
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
                "float_wrapped": MultipliedFloat(1.0, -1000.0),
                "str_empty": "",
                "str": "dummy",
            },
            {
                "none": None,
                "bool_true": True,
                "bool_false": False,
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": -1000,
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
                "float_wrapped": -1000.0,
                "str_empty": "",
                "str": "dummy",
            },
        ),
        (
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": MultipliedInt(1, -1000),
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": MultipliedFloat(1.0, -1000.0),
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple":
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
            },
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": -1000,
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": -1000.0,
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            },
        ),
        (
            WrappedDict({
                PrefixedStr("key", "none"): None,
                PrefixedStr("key", "bool"): WrappedDict({
                    PrefixedStr("key", "bool_true"): True,
                    PrefixedStr("key", "bool_false"): False,
                }),
                PrefixedStr("key", "int"): WrappedDict({
                    PrefixedStr("key", "int_one"): 1,
                    PrefixedStr("key", "int_minus_one"): -1,
                    PrefixedStr("key", "int_zero"): 0,
                    PrefixedStr("key", "int_wrapped"): MultipliedInt(1, -1000),
                }),
                PrefixedStr("key", "float"): WrappedDict({
                    PrefixedStr("key", "float_one"): 1.0,
                    PrefixedStr("key", "float_minus_one"): -1.0,
                    PrefixedStr("key", "float_zero"): 0.0,
                    PrefixedStr("key", "float_one_e_nine"): 1.0e9,
                    PrefixedStr("key", "float_minus_one_e_minus_nine"): -1.0e-9,
                    PrefixedStr("key", "float_nan"): math.nan,
                    PrefixedStr("key", "float_inf"): math.inf,
                    PrefixedStr("key", "float_minus_inf"): -math.inf,
                    PrefixedStr("key", "float_wrapped"): MultipliedFloat(1.0, -1000.0),
                }),
                PrefixedStr("key", "str"): WrappedDict({
                    PrefixedStr("key", "str_empty"): "",
                    PrefixedStr("key", "str"): "dummy",
                }),
                PrefixedStr("key", "list"): WrappedList(
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"]),
                PrefixedStr("key", "tuple"):
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
            }),
            {
                "key::none": None,
                "key::bool": {
                    "key::bool_true": True,
                    "key::bool_false": False,
                },
                "key::int": {
                    "key::int_one": 1,
                    "key::int_minus_one": -1,
                    "key::int_zero": 0,
                    "key::int_wrapped": -1000,
                },
                "key::float": {
                    "key::float_one": 1.0,
                    "key::float_minus_one": -1.0,
                    "key::float_zero": 0.0,
                    "key::float_one_e_nine": 1.0e9,
                    "key::float_minus_one_e_minus_nine": -1.0e-9,
                    "key::float_nan": math.nan,
                    "key::float_inf": math.inf,
                    "key::float_minus_inf": -math.inf,
                    "key::float_wrapped": -1000.0,
                },
                "key::str": {
                    "key::str_empty": "",
                    "key::str": "dummy",
                },
                "key::list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "key::tuple":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            },
        ),
    ]

    @ddt.idata(data_json_reformat)
    @ddt.unpack
    def test_json_reformat(self, data, expect):
        self.assertTrue(json_compare(json_reformat(data), expect))

    data_json_reformat__unregistered_type = [
        (set(),),
        (object(),),
        ([set(), object()],),
        ({"set": set(), "object": object()},),
    ]

    @ddt.idata(data_json_reformat__unregistered_type)
    @ddt.unpack
    def test_json_reformat__unregistered_type(self, data):
        with self.assertRaises(ValueError):
            json_reformat(data)

    data_json_sanitize = [
        (None, None),
        (True, True),
        (False, False),
        (1, 1),
        (-1, -1),
        (0, 0),
        (MultipliedInt(-1, 100), -100),
        (MultipliedInt(1, 100), 100),
        (1.0, 1.0),
        (-1.0, -1.0),
        (0.0, 0.0),
        (1.0e9, 1.0e9),
        (-1.0e-9, -1.0e-9),
        (math.nan, "nan"),
        (math.inf, "inf"),
        (-math.inf, "-inf"),
        (MultipliedFloat(1.0, 100.0), 100.0),
        (MultipliedFloat(-1.0, 100.0), -100.0),
        ("", ""),
        ("dummy", "dummy"),
        (
            datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            "2000-01-01 00:00:00+00:00",
        ),
        (
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"],
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, "nan", "inf", "-inf", "", "dummy"],
        ),
        (
            (None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, math.nan, math.inf, -math.inf, "", "dummy"),
            [None, True, False, 1, -1, 0, 1.0, -1.0, 0.0, 1.0e9, -1.0e-9, "nan", "inf", "-inf", "", "dummy"],
        ),
        ({1, 2, 3, 4, 5, 6, 7}, [1, 2, 3, 4, 5, 6, 7]),
        (
            {
                "none": None,
                "bool_true": True,
                "bool_false": False,
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": MultipliedInt(1, -1000),
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": math.nan,
                "float_inf": math.inf,
                "float_minus_inf": -math.inf,
                "float_wrapped": MultipliedFloat(1.0, -1000.0),
                "str_empty": "",
                "str": "dummy",
                "datetime": datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            },
            {
                "none": None,
                "bool_true": True,
                "bool_false": False,
                "int_one": 1,
                "int_minus_one": -1,
                "int_zero": 0,
                "int_wrapped": -1000,
                "float_one": 1.0,
                "float_minus_one": -1.0,
                "float_zero": 0.0,
                "float_one_e_nine": 1.0e9,
                "float_minus_one_e_minus_nine": -1.0e-9,
                "float_nan": "nan",
                "float_inf": "inf",
                "float_minus_inf": "-inf",
                "float_wrapped": -1000.0,
                "str_empty": "",
                "str": "dummy",
                "datetime": "2000-01-01 00:00:00+00:00",
            },
        ),
        (
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": MultipliedInt(1, -1000),
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": MultipliedFloat(1.0, -1000.0),
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "datetime": datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
                "list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple":
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                "set": {1, 2, 3, 4, 5, 6, 7},
            },
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": -1000,
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": "nan",
                    "float_inf": "inf",
                    "float_minus_inf": "-inf",
                    "float_wrapped": -1000.0,
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "datetime": "2000-01-01 00:00:00+00:00",
                "list": [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, "nan", "inf", "-inf", "", "dummy"],
                "tuple": [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, "nan", "inf", "-inf", "", "dummy"],
                "set": [1, 2, 3, 4, 5, 6, 7],
            },
        ),
        (
            WrappedDict({
                PrefixedStr("key", "none"): None,
                PrefixedStr("key", "bool"): WrappedDict({
                    PrefixedStr("key", "bool_true"): True,
                    PrefixedStr("key", "bool_false"): False,
                }),
                PrefixedStr("key", "int"): WrappedDict({
                    PrefixedStr("key", "int_one"): 1,
                    PrefixedStr("key", "int_minus_one"): -1,
                    PrefixedStr("key", "int_zero"): 0,
                    PrefixedStr("key", "int_wrapped"): MultipliedInt(1, -1000),
                }),
                PrefixedStr("key", "float"): WrappedDict({
                    PrefixedStr("key", "float_one"): 1.0,
                    PrefixedStr("key", "float_minus_one"): -1.0,
                    PrefixedStr("key", "float_zero"): 0.0,
                    PrefixedStr("key", "float_one_e_nine"): 1.0e9,
                    PrefixedStr("key", "float_minus_one_e_minus_nine"): -1.0e-9,
                    PrefixedStr("key", "float_nan"): math.nan,
                    PrefixedStr("key", "float_inf"): math.inf,
                    PrefixedStr("key", "float_minus_inf"): -math.inf,
                    PrefixedStr("key", "float_wrapped"): MultipliedFloat(1.0, -1000.0),
                }),
                PrefixedStr("key", "str"): WrappedDict({
                    PrefixedStr("key", "str_empty"): "",
                    PrefixedStr("key", "str"): "dummy",
                }),
                PrefixedStr("key", "datetime"): datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
                PrefixedStr("key", "list"): WrappedList(
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"]),
                PrefixedStr("key", "tuple"):
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                PrefixedStr("key", "set"): {1, 2, 3, 4, 5, 6, 7},
            }),
            {
                "key::none": None,
                "key::bool": {
                    "key::bool_true": True,
                    "key::bool_false": False,
                },
                "key::int": {
                    "key::int_one": 1,
                    "key::int_minus_one": -1,
                    "key::int_zero": 0,
                    "key::int_wrapped": -1000,
                },
                "key::float": {
                    "key::float_one": 1.0,
                    "key::float_minus_one": -1.0,
                    "key::float_zero": 0.0,
                    "key::float_one_e_nine": 1.0e9,
                    "key::float_minus_one_e_minus_nine": -1.0e-9,
                    "key::float_nan": "nan",
                    "key::float_inf": "inf",
                    "key::float_minus_inf": "-inf",
                    "key::float_wrapped": -1000.0,
                },
                "key::str": {
                    "key::str_empty": "",
                    "key::str": "dummy",
                },
                "key::datetime": "2000-01-01 00:00:00+00:00",
                "key::list": [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, "nan", "inf", "-inf", "", "dummy"],
                "key::tuple": [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, "nan", "inf", "-inf", "", "dummy"],
                "key::set": [1, 2, 3, 4, 5, 6, 7],
            },
        ),
    ]

    @ddt.idata(data_json_sanitize)
    @ddt.unpack
    def test_json_sanitize(self, data, expect):
        self.assertTrue(json_compare(json_sanitize(data), expect))

    data_json_difference = [
        (
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": MultipliedInt(1, -1000),
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": MultipliedFloat(1.0, -1000.0),
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple":
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                "none_not_none": None,
                "bool_negated": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int_negated": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_wrapped": MultipliedInt(1, -1000),
                },
                "float_negated": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": MultipliedFloat(1.0, -1000.0),
                },
                "num_type_mismatched": {
                    "int_as_float": 1,
                    "float_as_int": 1.0,
                },
                "str_unidentical": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list_size_unidentical":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "list_order_changed":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "list_first_item_mismatched":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple_size_unidentical":
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                "tuple_order_changed":
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                "tuple_first_item_mismatched":
                    (None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                "dict_size_unidentical": {
                    "none": None,
                    "bool_true": True,
                    "bool_false": False,
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": "nan",
                    "float_inf": "inf",
                    "float_minus_inf": "-inf",
                    "str_empty": "",
                    "str": "dummy",
                },
                "dict_keys_unidentical": {
                    "none": None,
                    "bool_true": True,
                    "bool_false": False,
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": "nan",
                    "float_inf": "inf",
                    "float_minus_inf": "-inf",
                    "str_empty": "",
                    "str": "dummy",
                },
            },
            {
                "none": None,
                "bool": {
                    "bool_true": True,
                    "bool_false": False,
                },
                "int": {
                    "int_one": 1,
                    "int_minus_one": -1,
                    "int_zero": 0,
                    "int_wrapped": -1000,
                },
                "float": {
                    "float_one": 1.0,
                    "float_minus_one": -1.0,
                    "float_zero": 0.0,
                    "float_one_e_nine": 1.0e9,
                    "float_minus_one_e_minus_nine": -1.0e-9,
                    "float_nan": math.nan,
                    "float_inf": math.inf,
                    "float_minus_inf": -math.inf,
                    "float_wrapped": -1000.0,
                },
                "str": {
                    "str_empty": "",
                    "str": "dummy",
                },
                "list":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple":
                    [None, True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "none_not_none": "",  # ["none_not_none"]
                "bool_negated": {
                    "bool_true": False,  # ["bool_negated", "bool_true"]
                    "bool_false": True,  # ["bool_negated", "bool_false"]
                },
                "int_negated": {
                    "int_one": -1,  # ["int_negated", "int_one"]
                    "int_minus_one": 1,  # ["int_negated", "int_minus_one"]
                    "int_wrapped": 1000,  # ["int_negated", "int_wrapped"]
                },
                "float_negated": {
                    "float_one": -1.0,  # ["float_negated", "float_one"]
                    "float_minus_one": 1.0,  # ["float_negated", "float_minus_one"]
                    "float_one_e_nine": -1.0e9,  # ["float_negated", "float_one_e_nine"]
                    "float_minus_one_e_minus_nine": 1.0e-9,  # Passes the equality check w.r.t. float tolerance
                    "float_inf": -math.inf,  # ["float_negated", "float_inf"]
                    "float_minus_inf": math.inf,  # ["float_negated", "float_minus_inf"]
                    "float_wrapped": 1000.0,  # ["float_negated", "float_wrapped"]
                },
                "num_type_mismatched": {
                    "int_as_float": 1.0,  # ["num_type_mismatched", "int_as_float"]
                    "float_as_int": 1,  # ["num_type_mismatched", "float_as_int"]
                },
                "str_unidentical": {
                    "str_empty": "dummy",  # ["str_unidentical", "str_empty"]
                    "str": "",  # ["str_unidentical", "str"]
                },
                "list_size_unidentical":  # ["list_size_unidentical"]
                    [True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "list_order_changed":  # ["list_order_changed", 0...15], 16 mismatches caused by left shift by one
                    [True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy", None],
                "list_first_item_mismatched":  # ["list_first_item_mismatched", 0]
                    ["", True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"],
                "tuple_size_unidentical":  # ["tuple_size_unidentical"]
                    (True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                "tuple_order_changed":  # ["tuple_order_changed", 0...15], 16 mismatches caused by left shift by one
                    (True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy", None),
                "tuple_first_item_mismatched":  # ["tuple_first_item_mismatched", 0]
                    ("", True, False, 1, -1, 0, 1., -1., 0., 1e9, -1e-9, math.nan, math.inf, -math.inf, "", "dummy"),
                "dict_size_unidentical":  # ["dict_size_unidentical"]
                    {
                        "bool_true": True,
                        "bool_false": False,
                        "int_one": 1,
                        "int_minus_one": -1,
                        "int_zero": 0,
                        "float_one": 1.0,
                        "float_minus_one": -1.0,
                        "float_zero": 0.0,
                        "float_one_e_nine": 1.0e9,
                        "float_minus_one_e_minus_nine": -1.0e-9,
                        "float_nan": "nan",
                        "float_inf": "inf",
                        "float_minus_inf": "-inf",
                        "str_empty": "",
                        "str": "dummy",
                    },
                "dict_keys_unidentical":  # ["dict_keys_unidentical"]
                    {
                        "another_none": None,
                        "another_bool_true": True,
                        "another_bool_false": False,
                        "another_int_one": 1,
                        "another_int_minus_one": -1,
                        "another_int_zero": 0,
                        "another_float_one": 1.0,
                        "another_float_minus_one": -1.0,
                        "another_float_zero": 0.0,
                        "another_float_one_e_nine": 1.0e9,
                        "another_float_minus_one_e_minus_nine": -1.0e-9,
                        "another_float_nan": "nan",
                        "another_float_inf": "inf",
                        "another_float_minus_inf": "-inf",
                        "another_str_empty": "",
                        "another_str": "dummy",
                    },
            },
            [
                ["none_not_none"],
                ["bool_negated", "bool_true"],
                ["bool_negated", "bool_false"],
                ["int_negated", "int_one"],
                ["int_negated", "int_minus_one"],
                ["int_negated", "int_wrapped"],
                ["float_negated", "float_one"],
                ["float_negated", "float_minus_one"],
                ["float_negated", "float_one_e_nine"],
                ["float_negated", "float_inf"],
                ["float_negated", "float_minus_inf"],
                ["float_negated", "float_wrapped"],
                ["num_type_mismatched", "int_as_float"],
                ["num_type_mismatched", "float_as_int"],
                ["str_unidentical", "str_empty"],
                ["str_unidentical", "str"],
                ["list_size_unidentical"],
                ["list_order_changed", 0],
                ["list_order_changed", 1],
                ["list_order_changed", 2],
                ["list_order_changed", 3],
                ["list_order_changed", 4],
                ["list_order_changed", 5],
                ["list_order_changed", 6],
                ["list_order_changed", 7],
                ["list_order_changed", 8],
                ["list_order_changed", 9],
                ["list_order_changed", 10],
                ["list_order_changed", 11],
                ["list_order_changed", 12],
                ["list_order_changed", 13],
                ["list_order_changed", 14],
                ["list_order_changed", 15],
                ["list_first_item_mismatched", 0],
                ["tuple_size_unidentical"],
                ["tuple_order_changed", 0],
                ["tuple_order_changed", 1],
                ["tuple_order_changed", 2],
                ["tuple_order_changed", 3],
                ["tuple_order_changed", 4],
                ["tuple_order_changed", 5],
                ["tuple_order_changed", 6],
                ["tuple_order_changed", 7],
                ["tuple_order_changed", 8],
                ["tuple_order_changed", 9],
                ["tuple_order_changed", 10],
                ["tuple_order_changed", 11],
                ["tuple_order_changed", 12],
                ["tuple_order_changed", 13],
                ["tuple_order_changed", 14],
                ["tuple_order_changed", 15],
                ["tuple_first_item_mismatched", 0],
                ["dict_size_unidentical"],
                ["dict_keys_unidentical"],
            ]
        )
    ]

    @ddt.idata(data_json_difference)
    @ddt.unpack
    def test_json_difference(self, a, b, expect_diffs):
        diffs = list(node_path for node_path, _ in json_difference(a, b, int_strict=True))
        for diff, expect_diff in zip(sorted(diffs), sorted(expect_diffs)):
            self.assertTrue(json_equals(diff, expect_diff))
