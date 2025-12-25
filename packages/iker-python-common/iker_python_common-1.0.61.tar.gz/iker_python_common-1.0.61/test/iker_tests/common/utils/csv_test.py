import datetime
import itertools
import math
import os.path
import unittest

import ddt

from iker.common.utils import csv
from iker.common.utils.dtutils import dt_format_iso, dt_parse_iso
from iker.common.utils.jsonutils import json_compare
from iker.common.utils.strutils import make_params_string, parse_params_string
from iker.common.utils.strutils import parse_bool
from iker_tests import resources_directory


@ddt.ddt
class CSVTest(unittest.TestCase):

    def test_lines(self):
        view = csv.view(
            [
                csv.column("dummy_str", loader=str, dumper=str, null_str=r"\N"),
                csv.column("dummy_bool", loader=parse_bool, dumper=str, null_str=r"\N"),
                csv.column("dummy_int", loader=int, dumper=str, null_str=r"\N"),
                csv.column("dummy_float", loader=float, dumper=str, null_str=r"\N"),
                csv.column("dummy_datetime",
                           loader=lambda x: dt_parse_iso(x).timestamp(),
                           dumper=lambda x: dt_format_iso(datetime.datetime.fromtimestamp(x, tz=datetime.timezone.utc)),
                           null_str=r"\N"),
                csv.column("dummy_params",
                           loader=lambda x: parse_params_string(x, delim=";", kv_delim="=", neg_prefix="!"),
                           dumper=lambda x: make_params_string(x, delim=";", kv_delim="=", neg_prefix="!"),
                           null_str=r"\N"),
            ],
        )

        lines = [
            r"dummy_str,dummy_bool,dummy_int,dummy_float,dummy_datetime,dummy_params",
            r"foo,True,1,1.0,2020-01-01T00:00:00,",
            r"bar,False,-1,-1.0,2020-01-01T00:00:00,key_1=value_1;key_2;!key_3",
            r"baz,\N,100,inf,2020-01-01T00:00:00,\N",
            r",\N,-100,-inf,2020-01-01T00:00:00,",
            r"\N,\N,0,nan,2020-01-01T00:00:00,\N",
            r"\N,\N,\N,\N,\N,\N",
        ]

        lines_no_header = [
            r"foo,True,1,1.0,2020-01-01T00:00:00,",
            r"bar,False,-1,-1.0,2020-01-01T00:00:00,key_1=value_1;key_2;!key_3",
            r"baz,\N,100,inf,2020-01-01T00:00:00,\N",
            r",\N,-100,-inf,2020-01-01T00:00:00,",
            r"\N,\N,0,nan,2020-01-01T00:00:00,\N",
            r"\N,\N,\N,\N,\N,\N",
        ]

        time = dt_parse_iso("2020-01-01T00:00:00").timestamp()

        list_data = [
            ["foo", True, 1, 1.0, time, {}],
            ["bar", False, -1, -1.0, time, {"key_1": "value_1", "key_2": True, "key_3": False}],
            ["baz", None, 100, math.inf, time, None],
            ["", None, -100, -math.inf, time, {}],
            [None, None, 0, math.nan, time, None],
            [None, None, None, None, None, None],
        ]

        dict_data = [
            {
                "dummy_str": "foo",
                "dummy_bool": True,
                "dummy_int": 1,
                "dummy_float": 1.0,
                "dummy_datetime": time,
                "dummy_params": {},
            },
            {
                "dummy_str": "bar",
                "dummy_bool": False,
                "dummy_int": -1,
                "dummy_float": -1.0,
                "dummy_datetime": time,
                "dummy_params": {"key_1": "value_1", "key_2": True, "key_3": False},
            },
            {
                "dummy_str": "baz",
                "dummy_bool": None,
                "dummy_int": 100,
                "dummy_float": math.inf,
                "dummy_datetime": time,
                "dummy_params": None,
            },
            {
                "dummy_str": "",
                "dummy_bool": None,
                "dummy_int": -100,
                "dummy_float": -math.inf,
                "dummy_datetime": time,
                "dummy_params": {},
            },
            {
                "dummy_str": None,
                "dummy_bool": None,
                "dummy_int": 0,
                "dummy_float": math.nan,
                "dummy_datetime": time,
                "dummy_params": None,
            },
            {
                "dummy_str": None,
                "dummy_bool": None,
                "dummy_int": None,
                "dummy_float": None,
                "dummy_datetime": None,
                "dummy_params": None,
            },
        ]

        for a, e in zip(view.load_lines(lines, has_header=True), list_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.load_lines(lines, has_header=True, ret_dict=True), dict_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.dump_lines(list_data, has_header=True), lines):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.dump_lines(dict_data, has_header=True), lines):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.load_lines(lines_no_header, has_header=False), list_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.load_lines(lines_no_header, has_header=False, ret_dict=True), dict_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.dump_lines(list_data, has_header=False), lines_no_header):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.dump_lines(dict_data, has_header=False), lines_no_header):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.dump_lines(view.load_lines(lines, has_header=True, ret_dict=True), has_header=True),
                        lines):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.load_lines(view.dump_lines(list_data, has_header=True), has_header=True, ret_dict=True),
                        dict_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.dump_lines(view.load_lines(lines_no_header, has_header=False, ret_dict=True),
                                        has_header=False),
                        lines_no_header):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(view.load_lines(view.dump_lines(list_data, has_header=False), has_header=False, ret_dict=True),
                        dict_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(itertools.chain(view.load_lines(lines, has_header=True),
                                        view.load_lines(lines, has_header=True, ret_dict=True)),
                        list_data + dict_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(itertools.chain(view.dump_lines(list_data, has_header=True),
                                        view.dump_lines(dict_data, has_header=True)),
                        lines + lines):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(itertools.chain(view.load_lines(lines, has_header=True),
                                        view.load_lines(lines, has_header=True, ret_dict=True),
                                        view.load_lines(lines_no_header, has_header=False),
                                        view.load_lines(lines_no_header, has_header=False, ret_dict=True)),
                        list_data + dict_data + list_data + dict_data):
            self.assertTrue(json_compare(a, e))

        for a, e in zip(itertools.chain(view.dump_lines(list_data, has_header=True),
                                        view.dump_lines(dict_data, has_header=True),
                                        view.dump_lines(list_data, has_header=False),
                                        view.dump_lines(dict_data, has_header=False)),
                        lines + lines + lines_no_header + lines_no_header):
            self.assertTrue(json_compare(a, e))

    def test_file(self):
        view_csv = csv.view(
            [
                csv.column("dummy_str", loader=str, dumper=str, null_str=r"\N"),
                csv.column("dummy_bool", loader=parse_bool, dumper=str, null_str=r"\N"),
                csv.column("dummy_int", loader=int, dumper=str, null_str=r"\N"),
                csv.column("dummy_float", loader=float, dumper=str, null_str=r"\N"),
                csv.column("dummy_datetime",
                           loader=lambda x: dt_parse_iso(x).timestamp(),
                           dumper=lambda x: dt_format_iso(datetime.datetime.fromtimestamp(x, tz=datetime.timezone.utc)),
                           null_str=r"\N"),
                csv.column("dummy_params",
                           loader=lambda x: parse_params_string(x, delim=";", kv_delim="=", neg_prefix="!"),
                           dumper=lambda x: make_params_string(x, delim=";", kv_delim="=", neg_prefix="!"),
                           null_str=r"\N"),
            ],
        )

        view_tsv = csv.view(
            [
                csv.column("dummy_str", loader=str, dumper=str, null_str=r"<null>"),
                csv.column("dummy_bool", loader=parse_bool, dumper=str, null_str=r"<null>"),
                csv.column("dummy_int", loader=int, dumper=str, null_str=r"<null>"),
                csv.column("dummy_float", loader=float, dumper=str, null_str=r"<null>"),
                csv.column("dummy_datetime",
                           loader=lambda x: dt_parse_iso(x).timestamp(),
                           dumper=lambda x: dt_format_iso(datetime.datetime.fromtimestamp(x, tz=datetime.timezone.utc)),
                           null_str=r"<null>"),
                csv.column("dummy_params",
                           loader=lambda x: parse_params_string(x, delim="#", kv_delim=":", neg_prefix="-"),
                           dumper=lambda x: make_params_string(x, delim="#", kv_delim=":", neg_prefix="-"),
                           null_str=r"<null>"),
            ],
            col_delim="\t",
        )

        time = dt_parse_iso("2020-01-01T00:00:00").timestamp()

        data = [
            ["foo", True, 1, 1.0, time, {}],
            ["bar", False, -1, -1.0, time, {"key_1": "value_1", "key_2": True, "key_3": False}],
            ["baz", None, 100, math.inf, time, None],
            ["", None, -100, -math.inf, time, {}],
            [None, None, 0, math.nan, time, None],
            [None, None, None, None, None, None],
        ]

        for c, t, d in zip(view_csv.load_file(os.path.join(resources_directory, "unittest/csv/data.csv"),
                                              has_header=True,
                                              encoding="utf-8"),
                           view_tsv.load_file(os.path.join(resources_directory, "unittest/csv/data.tsv"),
                                              has_header=True,
                                              encoding="utf-8"),
                           data):
            self.assertTrue(json_compare(c, d))
            self.assertTrue(json_compare(t, d))
            self.assertTrue(json_compare(c, t))
