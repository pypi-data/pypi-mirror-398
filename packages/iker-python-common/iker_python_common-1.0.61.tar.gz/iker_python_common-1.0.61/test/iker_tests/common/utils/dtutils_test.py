import datetime
import unittest

import ddt

from iker.common.utils.dtutils import basic_format, extended_format, iso_format
from iker.common.utils.dtutils import dt_format, dt_format_iso, dt_parse, dt_parse_iso
from iker.common.utils.dtutils import dt_from_ts, dt_from_ts_us, dt_to_ts, dt_to_ts_us
from iker.common.utils.dtutils import dt_utc
from iker.common.utils.dtutils import dt_utc_epoch, dt_utc_max, dt_utc_min
from iker.common.utils.dtutils import td_from_time, td_from_us, td_to_time, td_to_us


@ddt.ddt
class DtUtilsTest(unittest.TestCase):

    def test_dt_utc_min(self):
        self.assertEqual(dt_utc(1, 1, 1, 0, 0, 0, 0), dt_utc_min())
        self.assertEqual("0001-01-01T00:00:00.000000+00:00", dt_format(dt_utc_min(), iso_format(True, True)))
        self.assertEqual("0001-01-01T00:00:00", dt_format_iso(dt_utc_min()))
        self.assertEqual(dt_parse_iso("0001-01-01T00:00:00.000000+00:00"), dt_utc_min())
        self.assertEqual(dt_parse_iso("0001-01-01T00:00:00.000000"), dt_utc_min())

    def test_dt_utc_max(self):
        self.assertEqual(dt_utc(9999, 12, 31, 23, 59, 59, 999999), dt_utc_max())
        self.assertEqual("9999-12-31T23:59:59.999999+00:00", dt_format(dt_utc_max(), iso_format(True, True)))
        self.assertEqual("9999-12-31T23:59:59", dt_format_iso(dt_utc_max()))
        self.assertEqual(dt_parse_iso("9999-12-31T23:59:59.999999+00:00"), dt_utc_max())
        self.assertEqual(dt_parse_iso("9999-12-31T23:59:59.999999"), dt_utc_max())

    def test_dt_utc_epoch(self):
        self.assertEqual(dt_utc(1970, 1, 1, 0, 0, 0, 0), dt_utc_epoch())
        self.assertEqual(0.0, dt_to_ts(dt_utc_epoch()))
        self.assertEqual(dt_from_ts(0.0), dt_utc_epoch())
        self.assertEqual("1970-01-01T00:00:00.000000+00:00", dt_format(dt_utc_epoch(), iso_format(True, True)))
        self.assertEqual("1970-01-01T00:00:00", dt_format_iso(dt_utc_epoch()))
        self.assertEqual(dt_parse_iso("1970-01-01T00:00:00.000000+00:00"), dt_utc_epoch())
        self.assertEqual(dt_parse_iso("1970-01-01T00:00:00.000000"), dt_utc_epoch())

    data_td_us_roundtrip = [
        (0,),
        (1,),
        (999,),
        (1000,),
        (999999,),
        (1000000,),
        (60000000,),
        (3600000000,),
        (86399999999,),
        (86400000000,),
        (31536000000000,),
    ]

    @ddt.idata(data_td_us_roundtrip)
    @ddt.unpack
    def test_td_us_roundtrip(self, data):
        self.assertEqual(data, td_to_us(td_from_us(data)))

    data_td_us_roundtrip__td = [
        (datetime.timedelta(),),
        (datetime.timedelta(microseconds=1),),
        (datetime.timedelta(microseconds=999),),
        (datetime.timedelta(microseconds=1000),),
        (datetime.timedelta(microseconds=999999),),
        (datetime.timedelta(seconds=1),),
        (datetime.timedelta(minutes=1),),
        (datetime.timedelta(hours=1),),
        (datetime.timedelta(hours=23, minutes=59, seconds=59, microseconds=999999),),
        (datetime.timedelta(days=1),),
        (datetime.timedelta(days=365),),
    ]

    @ddt.idata(data_td_us_roundtrip__td)
    @ddt.unpack
    def test_td_us_roundtrip__td(self, data):
        self.assertEqual(data, td_from_us(td_to_us(data)))

    data_td_time_roundtrip = [
        (datetime.time(tzinfo=datetime.timezone.utc),),
        (datetime.time(tzinfo=datetime.timezone.utc, microsecond=1),),
        (datetime.time(tzinfo=datetime.timezone.utc, microsecond=999),),
        (datetime.time(tzinfo=datetime.timezone.utc, microsecond=1000),),
        (datetime.time(tzinfo=datetime.timezone.utc, microsecond=999999),),
        (datetime.time(tzinfo=datetime.timezone.utc, second=1),),
        (datetime.time(tzinfo=datetime.timezone.utc, minute=1),),
        (datetime.time(tzinfo=datetime.timezone.utc, hour=1),),
        (datetime.time(tzinfo=datetime.timezone.utc, hour=23, minute=59, second=59, microsecond=999999),),
    ]

    @ddt.idata(data_td_time_roundtrip)
    @ddt.unpack
    def test_td_time_roundtrip(self, data):
        self.assertEqual(data, td_to_time(td_from_time(data)))

    data_td_time_roundtrip__td = [
        (datetime.timedelta(),),
        (datetime.timedelta(microseconds=1),),
        (datetime.timedelta(microseconds=999),),
        (datetime.timedelta(microseconds=1000),),
        (datetime.timedelta(microseconds=999999),),
        (datetime.timedelta(seconds=1),),
        (datetime.timedelta(minutes=1),),
        (datetime.timedelta(hours=1),),
        (datetime.timedelta(hours=23, minutes=59, seconds=59, microseconds=999999),),
    ]

    @ddt.idata(data_td_time_roundtrip__td)
    @ddt.unpack
    def test_td_time_roundtrip__td(self, data):
        self.assertEqual(data, td_from_time(td_to_time(data)))

    data_dt_to_ts = [
        (dt_utc(1970, 1, 1), 0.0),
        (dt_utc(1969, 12, 31, 23, 59, 59), -1.0),
        (dt_utc(1969, 12, 31, 23, 59, 59, 1), -0.999999),
        (dt_utc(1969, 12, 31, 23, 59, 59, 1000), -0.999),
        (dt_utc(1969, 12, 31, 23, 59, 59, 999999), -0.000001),
        (dt_utc(1970, 1, 1, 0, 0, 1), 1.0),
        (dt_utc(1970, 1, 1, 0, 0, 1, 1), 1.000001),
        (dt_utc(1970, 1, 1, 0, 0, 1, 1000), 1.001),
        (dt_utc(1970, 1, 1, 0, 0, 1, 999999), 1.999999),
        (dt_utc(1970, 1, 1, 0, 0, 0, 1), 0.000001),
        (dt_utc(1970, 1, 1, 0, 0, 0, 1000), 0.001),
        (dt_utc(1970, 1, 1, 0, 0, 0, 999999), 0.999999),
        (dt_utc(2025, 1, 1, 0, 0, 0), 1735689600.0),
        (dt_utc(2025, 1, 1, 0, 0, 0, 1), 1735689600.000001),
        (dt_utc(2025, 1, 1, 0, 0, 0, 1000), 1735689600.001),
        (dt_utc(2025, 1, 1, 0, 0, 0, 999999), 1735689600.999999),
        (dt_utc(2100, 1, 1, 0, 0, 0), 4102444800.0),
        (dt_utc(2100, 1, 1, 0, 0, 0, 1), 4102444800.000001),
        (dt_utc(2100, 1, 1, 0, 0, 0, 1000), 4102444800.001),
        (dt_utc(2100, 1, 1, 0, 0, 0, 999999), 4102444800.999999),
    ]

    @ddt.idata(data_dt_to_ts)
    @ddt.unpack
    def test_dt_to_ts(self, data, expect):
        self.assertEqual(expect, dt_to_ts(data))

    data_dt_to_ts_us = [
        (dt_utc(1970, 1, 1), 0),
        (dt_utc(1969, 12, 31, 23, 59, 59), -1000000),
        (dt_utc(1969, 12, 31, 23, 59, 59, 1), -999999),
        (dt_utc(1969, 12, 31, 23, 59, 59, 1000), -999000),
        (dt_utc(1969, 12, 31, 23, 59, 59, 999999), -1),
        (dt_utc(1970, 1, 1, 0, 0, 1), 1000000),
        (dt_utc(1970, 1, 1, 0, 0, 1, 1), 1000001),
        (dt_utc(1970, 1, 1, 0, 0, 1, 1000), 1001000),
        (dt_utc(1970, 1, 1, 0, 0, 1, 999999), 1999999),
        (dt_utc(1970, 1, 1, 0, 0, 0, 1), 1),
        (dt_utc(1970, 1, 1, 0, 0, 0, 1000), 1000),
        (dt_utc(1970, 1, 1, 0, 0, 0, 999999), 999999),
        (dt_utc(2025, 1, 1, 0, 0, 0), 1735689600000000),
        (dt_utc(2025, 1, 1, 0, 0, 0, 1), 1735689600000001),
        (dt_utc(2025, 1, 1, 0, 0, 0, 1000), 1735689600001000),
        (dt_utc(2025, 1, 1, 0, 0, 0, 999999), 1735689600999999),
        (dt_utc(2100, 1, 1, 0, 0, 0), 4102444800000000),
        (dt_utc(2100, 1, 1, 0, 0, 0, 1), 4102444800000001),
        (dt_utc(2100, 1, 1, 0, 0, 0, 1000), 4102444800001000),
        (dt_utc(2100, 1, 1, 0, 0, 0, 999999), 4102444800999999),
    ]

    @ddt.idata(data_dt_to_ts_us)
    @ddt.unpack
    def test_dt_to_ts_us(self, data, expect):
        self.assertEqual(expect, dt_to_ts_us(data))

    data_dt_from_ts = [
        (0.0, dt_utc(1970, 1, 1)),
        (-1.0, dt_utc(1969, 12, 31, 23, 59, 59)),
        (-0.999999, dt_utc(1969, 12, 31, 23, 59, 59, 1)),
        (-0.999, dt_utc(1969, 12, 31, 23, 59, 59, 1000)),
        (-0.000001, dt_utc(1969, 12, 31, 23, 59, 59, 999999)),
        (1.0, dt_utc(1970, 1, 1, 0, 0, 1)),
        (1.000001, dt_utc(1970, 1, 1, 0, 0, 1, 1)),
        (1.001, dt_utc(1970, 1, 1, 0, 0, 1, 1000)),
        (1.999999, dt_utc(1970, 1, 1, 0, 0, 1, 999999)),
        (0.000001, dt_utc(1970, 1, 1, 0, 0, 0, 1)),
        (0.001, dt_utc(1970, 1, 1, 0, 0, 0, 1000)),
        (0.999999, dt_utc(1970, 1, 1, 0, 0, 0, 999999)),
        (1735689600.0, dt_utc(2025, 1, 1, 0, 0, 0)),
        (1735689600.000001, dt_utc(2025, 1, 1, 0, 0, 0, 1)),
        (1735689600.001, dt_utc(2025, 1, 1, 0, 0, 0, 1000)),
        (1735689600.999999, dt_utc(2025, 1, 1, 0, 0, 0, 999999)),
        (4102444800.0, dt_utc(2100, 1, 1, 0, 0, 0)),
        (4102444800.000001, dt_utc(2100, 1, 1, 0, 0, 0, 1)),
        (4102444800.001, dt_utc(2100, 1, 1, 0, 0, 0, 1000)),
        (4102444800.999999, dt_utc(2100, 1, 1, 0, 0, 0, 999999)),
    ]

    @ddt.idata(data_dt_from_ts)
    @ddt.unpack
    def test_dt_from_ts(self, data, expect):
        self.assertEqual(expect, dt_from_ts(data))

    data_dt_from_ts_us = [
        (0, dt_utc(1970, 1, 1)),
        (-1000000, dt_utc(1969, 12, 31, 23, 59, 59)),
        (-999999, dt_utc(1969, 12, 31, 23, 59, 59, 1)),
        (-999000, dt_utc(1969, 12, 31, 23, 59, 59, 1000)),
        (-1, dt_utc(1969, 12, 31, 23, 59, 59, 999999)),
        (1000000, dt_utc(1970, 1, 1, 0, 0, 1)),
        (1000001, dt_utc(1970, 1, 1, 0, 0, 1, 1)),
        (1001000, dt_utc(1970, 1, 1, 0, 0, 1, 1000)),
        (1999999, dt_utc(1970, 1, 1, 0, 0, 1, 999999)),
        (1, dt_utc(1970, 1, 1, 0, 0, 0, 1)),
        (1000, dt_utc(1970, 1, 1, 0, 0, 0, 1000)),
        (999999, dt_utc(1970, 1, 1, 0, 0, 0, 999999)),
        (1735689600000000, dt_utc(2025, 1, 1, 0, 0, 0)),
        (1735689600000001, dt_utc(2025, 1, 1, 0, 0, 0, 1)),
        (1735689600001000, dt_utc(2025, 1, 1, 0, 0, 0, 1000)),
        (1735689600999999, dt_utc(2025, 1, 1, 0, 0, 0, 999999)),
        (4102444800000000, dt_utc(2100, 1, 1, 0, 0, 0)),
        (4102444800000001, dt_utc(2100, 1, 1, 0, 0, 0, 1)),
        (4102444800001000, dt_utc(2100, 1, 1, 0, 0, 0, 1000)),
        (4102444800999999, dt_utc(2100, 1, 1, 0, 0, 0, 999999)),
    ]

    @ddt.idata(data_dt_from_ts_us)
    @ddt.unpack
    def test_dt_from_ts_us(self, data, expect):
        self.assertEqual(expect, dt_from_ts_us(data))

    data_dt_parse = [
        ("00010101T000000", basic_format(), dt_utc(1, 1, 1, 0, 0, 0)),
        ("00010101T000000.000000", basic_format(with_us=True), dt_utc(1, 1, 1, 0, 0, 0)),
        ("00010101T000000+0000", basic_format(with_tz=True), dt_utc(1, 1, 1, 0, 0, 0)),
        ("00010101T000000.000000+0000", basic_format(with_us=True, with_tz=True), dt_utc(1, 1, 1, 0, 0, 0)),
        ("19700101T000000", basic_format(), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("19700101T000000.000000", basic_format(with_us=True), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("19700101T000000+0000", basic_format(with_tz=True), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("19700101T000000.000000+0000", basic_format(with_us=True, with_tz=True), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("99991231T235959",
         basic_format(),
         dt_utc(9999, 12, 31, 23, 59, 59)),
        ("99991231T235959.000000",
         basic_format(with_us=True),
         dt_utc(9999, 12, 31, 23, 59, 59)),
        ("99991231T235959+0000",
         basic_format(with_tz=True),
         dt_utc(9999, 12, 31, 23, 59, 59)),
        ("99991231T235959.000000+0000",
         basic_format(with_us=True, with_tz=True),
         dt_utc(9999, 12, 31, 23, 59, 59)),

        ("0001-01-01T00:00:00", extended_format(), dt_utc(1, 1, 1, 0, 0, 0)),
        ("0001-01-01T00:00:00.000000", extended_format(with_us=True), dt_utc(1, 1, 1, 0, 0, 0)),
        ("0001-01-01T00:00:00+00:00", extended_format(with_tz=True), dt_utc(1, 1, 1, 0, 0, 0)),
        ("0001-01-01T00:00:00.000000+00:00", extended_format(with_us=True, with_tz=True), dt_utc(1, 1, 1, 0, 0, 0)),
        ("1970-01-01T00:00:00", extended_format(), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("1970-01-01T00:00:00.000000", extended_format(with_us=True), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("1970-01-01T00:00:00+00:00", extended_format(with_tz=True), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("1970-01-01T00:00:00.000000+00:00", extended_format(with_us=True, with_tz=True), dt_utc(1970, 1, 1, 0, 0, 0)),
        ("9999-12-31T23:59:59",
         extended_format(),
         dt_utc(9999, 12, 31, 23, 59, 59)),
        ("9999-12-31T23:59:59.000000",
         extended_format(with_us=True),
         dt_utc(9999, 12, 31, 23, 59, 59)),
        ("9999-12-31T23:59:59+00:00",
         extended_format(with_tz=True),
         dt_utc(9999, 12, 31, 23, 59, 59)),
        ("9999-12-31T23:59:59.000000+00:00",
         extended_format(with_us=True, with_tz=True),
         dt_utc(9999, 12, 31, 23, 59, 59)),

        ("0001-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S", dt_utc(1, 1, 1, 0, 0, 0)),
        ("9999-12-31T23:59:59", "%Y-%m-%dT%H:%M:%S", dt_utc(9999, 12, 31, 23, 59, 59)),
        ("1970-01-01", "%Y-%m-%d", dt_utc(1970, 1, 1)),
        ("1970-01-01 12:30:45", "%Y-%m-%d %H:%M:%S", dt_utc(1970, 1, 1, 12, 30, 45)),
        ("1970-01-01T12:30:45", "%Y-%m-%dT%H:%M:%S", dt_utc(1970, 1, 1, 12, 30, 45)),
        ("1970-01-01T12:30:45", ["%H:%M:%S", "%Y-%m-%dT%H:%M:%S"], dt_utc(1970, 1, 1, 12, 30, 45)),
        ("1970-01-01T12:30:45", ("%H:%M:%S", "%Y-%m-%dT%H:%M:%S"), dt_utc(1970, 1, 1, 12, 30, 45)),
        ("2020-10-01", "%Y-%m-%d", dt_utc(2020, 10, 1)),
        ("2020-10-01 12:30:45", "%Y-%m-%d %H:%M:%S", dt_utc(2020, 10, 1, 12, 30, 45)),
        ("2020-10-01T12:30:45", "%Y-%m-%dT%H:%M:%S", dt_utc(2020, 10, 1, 12, 30, 45)),
        ("1949-10-01", "%Y-%m-%d", dt_utc(1949, 10, 1)),
        ("1949-10-01 12:30:45", "%Y-%m-%d %H:%M:%S", dt_utc(1949, 10, 1, 12, 30, 45)),
        ("1949-10-01T12:30:45", "%Y-%m-%dT%H:%M:%S", dt_utc(1949, 10, 1, 12, 30, 45)),

        ("0009-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S", dt_utc(9, 1, 1, 0, 0, 0)),
        ("0090-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S", dt_utc(90, 1, 1, 0, 0, 0)),
        ("0900-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S", dt_utc(900, 1, 1, 0, 0, 0)),
        ("9000-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S", dt_utc(9000, 1, 1, 0, 0, 0)),

        ("99-12-31/12:30:45", "%y-%m-%d/%H:%M:%S", dt_utc(1999, 12, 31, 12, 30, 45)),
        ("00-01-01/12:30:45", "%y-%m-%d/%H:%M:%S", dt_utc(2000, 1, 1, 12, 30, 45)),

        ("1999/99-12-31/12:30:45", "%Y/%y-%m-%d/%H:%M:%S", dt_utc(1999, 12, 31, 12, 30, 45)),
        ("2000/00-01-01/12:30:45", "%Y/%y-%m-%d/%H:%M:%S", dt_utc(2000, 1, 1, 12, 30, 45)),
        ("99/1999-12-31/12:30:45", "%y/%Y-%m-%d/%H:%M:%S", dt_utc(1999, 12, 31, 12, 30, 45)),
        ("00/2000-01-01/12:30:45", "%y/%Y-%m-%d/%H:%M:%S", dt_utc(2000, 1, 1, 12, 30, 45)),

        ("2999/99-12-31/12:30:45", "%Y/%y-%m-%d/%H:%M:%S", dt_utc(1999, 12, 31, 12, 30, 45)),
        ("1000/00-01-01/12:30:45", "%Y/%y-%m-%d/%H:%M:%S", dt_utc(2000, 1, 1, 12, 30, 45)),
        ("99/2999-12-31/12:30:45", "%y/%Y-%m-%d/%H:%M:%S", dt_utc(2999, 12, 31, 12, 30, 45)),
        ("00/1000-01-01/12:30:45", "%y/%Y-%m-%d/%H:%M:%S", dt_utc(1000, 1, 1, 12, 30, 45)),
    ]

    @ddt.idata(data_dt_parse)
    @ddt.unpack
    def test_dt_parse(self, dt_str, fmt_str, expect):
        self.assertEqual(expect, dt_parse(dt_str, fmt_str))

    data_dt_format = [
        (dt_utc(1, 1, 1, 0, 0, 0), basic_format(), "00010101T000000"),
        (dt_utc(1, 1, 1, 0, 0, 0), basic_format(with_us=True), "00010101T000000.000000"),
        (dt_utc(1, 1, 1, 0, 0, 0), basic_format(with_tz=True), "00010101T000000+0000"),
        (dt_utc(1, 1, 1, 0, 0, 0), basic_format(with_us=True, with_tz=True), "00010101T000000.000000+0000"),
        (dt_utc(1970, 1, 1, 0, 0, 0), basic_format(), "19700101T000000"),
        (dt_utc(1970, 1, 1, 0, 0, 0), basic_format(with_us=True), "19700101T000000.000000"),
        (dt_utc(1970, 1, 1, 0, 0, 0), basic_format(with_tz=True), "19700101T000000+0000"),
        (dt_utc(1970, 1, 1, 0, 0, 0), basic_format(with_us=True, with_tz=True), "19700101T000000.000000+0000"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         basic_format(),
         "99991231T235959"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         basic_format(with_us=True),
         "99991231T235959.000000"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         basic_format(with_tz=True),
         "99991231T235959+0000"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         basic_format(with_us=True, with_tz=True),
         "99991231T235959.000000+0000"),

        (dt_utc(1, 1, 1, 0, 0, 0), extended_format(), "0001-01-01T00:00:00"),
        (dt_utc(1, 1, 1, 0, 0, 0), extended_format(with_us=True), "0001-01-01T00:00:00.000000"),
        (dt_utc(1, 1, 1, 0, 0, 0), extended_format(with_tz=True), "0001-01-01T00:00:00+00:00"),
        (dt_utc(1, 1, 1, 0, 0, 0), extended_format(with_us=True, with_tz=True), "0001-01-01T00:00:00.000000+00:00"),
        (dt_utc(1970, 1, 1, 0, 0, 0), extended_format(), "1970-01-01T00:00:00"),
        (dt_utc(1970, 1, 1, 0, 0, 0), extended_format(with_us=True), "1970-01-01T00:00:00.000000"),
        (dt_utc(1970, 1, 1, 0, 0, 0), extended_format(with_tz=True), "1970-01-01T00:00:00+00:00"),
        (dt_utc(1970, 1, 1, 0, 0, 0), extended_format(with_us=True, with_tz=True), "1970-01-01T00:00:00.000000+00:00"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         extended_format(),
         "9999-12-31T23:59:59"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         extended_format(with_us=True),
         "9999-12-31T23:59:59.000000"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         extended_format(with_tz=True),
         "9999-12-31T23:59:59+00:00"),
        (dt_utc(9999, 12, 31, 23, 59, 59),
         extended_format(with_us=True, with_tz=True),
         "9999-12-31T23:59:59.000000+00:00"),

        (dt_utc(9999, 12, 31, 23, 59, 59), "%Y-%m-%dT%H:%M:%S", "9999-12-31T23:59:59"),
        (dt_utc(1970, 1, 1), "%Y-%m-%d", "1970-01-01"),
        (dt_utc(1970, 1, 1, 12, 30, 45), "%Y-%m-%d %H:%M:%S", "1970-01-01 12:30:45"),
        (dt_utc(1970, 1, 1, 12, 30, 45), "%Y-%m-%dT%H:%M:%S", "1970-01-01T12:30:45"),
        (dt_utc(2020, 10, 1), "%Y-%m-%d", "2020-10-01"),
        (dt_utc(2020, 10, 1, 12, 30, 45), "%Y-%m-%d %H:%M:%S", "2020-10-01 12:30:45"),
        (dt_utc(2020, 10, 1, 12, 30, 45), "%Y-%m-%dT%H:%M:%S", "2020-10-01T12:30:45"),
        (dt_utc(1949, 10, 1), "%Y-%m-%d", "1949-10-01"),
        (dt_utc(1949, 10, 1, 12, 30, 45), "%Y-%m-%d %H:%M:%S", "1949-10-01 12:30:45"),
        (dt_utc(1949, 10, 1, 12, 30, 45), "%Y-%m-%dT%H:%M:%S", "1949-10-01T12:30:45"),

        (dt_utc(9, 1, 1, 0, 0, 0), "%Y-%m-%dT%H:%M:%S", "0009-01-01T00:00:00"),
        (dt_utc(90, 1, 1, 0, 0, 0), "%Y-%m-%dT%H:%M:%S", "0090-01-01T00:00:00"),
        (dt_utc(900, 1, 1, 0, 0, 0), "%Y-%m-%dT%H:%M:%S", "0900-01-01T00:00:00"),
        (dt_utc(9000, 1, 1, 0, 0, 0), "%Y-%m-%dT%H:%M:%S", "9000-01-01T00:00:00"),

        (dt_utc(1999, 12, 31, 12, 30, 45), "%y-%m-%d/%H:%M:%S", "99-12-31/12:30:45"),
        (dt_utc(2000, 1, 1, 12, 30, 45), "%y-%m-%d/%H:%M:%S", "00-01-01/12:30:45"),
        (dt_utc(1999, 12, 31, 12, 30, 45), "%Y/%y-%m-%d/%H:%M:%S", "1999/99-12-31/12:30:45"),
        (dt_utc(2000, 1, 1, 12, 30, 45), "%Y/%y-%m-%d/%H:%M:%S", "2000/00-01-01/12:30:45"),
        (dt_utc(1999, 12, 31, 12, 30, 45), "%y/%Y-%m-%d/%H:%M:%S", "99/1999-12-31/12:30:45"),
        (dt_utc(2000, 1, 1, 12, 30, 45), "%y/%Y-%m-%d/%H:%M:%S", "00/2000-01-01/12:30:45"),

        (dt_utc(9, 1, 1, 0, 0, 0), "%y-%m-%d/%H:%M:%S", "09-01-01/00:00:00"),
        (dt_utc(90, 1, 1, 0, 0, 0), "%y-%m-%d/%H:%M:%S", "90-01-01/00:00:00"),
        (dt_utc(900, 1, 1, 0, 0, 0), "%y-%m-%d/%H:%M:%S", "00-01-01/00:00:00"),
        (dt_utc(9000, 1, 1, 0, 0, 0), "%y-%m-%d/%H:%M:%S", "00-01-01/00:00:00"),
        (dt_utc(9, 1, 1, 0, 0, 0), "%Y/%y-%m-%d/%H:%M:%S", "0009/09-01-01/00:00:00"),
        (dt_utc(90, 1, 1, 0, 0, 0), "%Y/%y-%m-%d/%H:%M:%S", "0090/90-01-01/00:00:00"),
        (dt_utc(900, 1, 1, 0, 0, 0), "%Y/%y-%m-%d/%H:%M:%S", "0900/00-01-01/00:00:00"),
        (dt_utc(9000, 1, 1, 0, 0, 0), "%Y/%y-%m-%d/%H:%M:%S", "9000/00-01-01/00:00:00"),
    ]

    @ddt.idata(data_dt_format)
    @ddt.unpack
    def test_dt_format(self, dt, fmt_str, expect):
        self.assertEqual(expect, dt_format(dt, fmt_str))
