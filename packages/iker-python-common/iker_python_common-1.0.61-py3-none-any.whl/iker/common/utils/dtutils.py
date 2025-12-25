import datetime
import re
import sys
from collections.abc import Sequence

from iker.common.utils.funcutils import memorized, singleton

__all__ = [
    "basic_date_format",
    "basic_time_format",
    "basic_format",
    "extended_date_format",
    "extended_time_format",
    "extended_format",
    "iso_date_format",
    "iso_time_format",
    "iso_format",
    "iso_formats",
    "dt_utc_min",
    "dt_utc_max",
    "dt_utc_epoch",
    "dt_utc_infinity",
    "dt_utc_now",
    "dt_utc",
    "td_to_us",
    "td_from_us",
    "td_to_time",
    "td_from_time",
    "dt_to_ts",
    "dt_to_ts_us",
    "dt_from_ts",
    "dt_from_ts_us",
    "dt_parse",
    "dt_format",
    "dt_parse_iso",
    "dt_format_iso",
]


@singleton
def basic_date_format() -> str:
    """
    Returns the basic date format string.

    :return: The basic date format string.
    """
    return "%Y%m%d"


@memorized
def basic_time_format(with_us: bool = False, with_tz: bool = False) -> str:
    """
    Returns the basic time format string, with optional microseconds and timezone.

    :param with_us: If ``True``, include microseconds in the format.
    :param with_tz: If ``True``, include timezone in the format.
    :return: The basic time format string.
    """
    fmt_str = "T%H%M%S"
    if with_us:
        fmt_str = fmt_str + ".%f"
    if with_tz:
        fmt_str = fmt_str + "%z"
    return fmt_str


@memorized
def basic_format(with_us: bool = False, with_tz: bool = False) -> str:
    """
    Returns the basic combined date and time format string, with optional microseconds and timezone.

    :param with_us: If ``True``, include microseconds in the time format.
    :param with_tz: If ``True``, include timezone in the time format.
    :return: The basic combined date and time format string.
    """
    return basic_date_format() + basic_time_format(with_us, with_tz)


@singleton
def extended_date_format() -> str:
    """
    Returns the extended date format string.

    :return: The extended date format string.
    """
    return "%Y-%m-%d"


@memorized
def extended_time_format(with_us: bool = False, with_tz: bool = False) -> str:
    """
    Returns the extended time format string, with optional microseconds and timezone.

    :param with_us: If ``True``, include microseconds in the format.
    :param with_tz: If ``True``, include timezone in the format.
    :return: The extended time format string.
    """
    fmt_str = "T%H:%M:%S"
    if with_us:
        fmt_str = fmt_str + ".%f"
    if with_tz:
        fmt_str = fmt_str + "%:z"
    return fmt_str


@memorized
def extended_format(with_us: bool = False, with_tz: bool = False) -> str:
    """
    Returns the extended combined date and time format string, with optional microseconds and timezone.

    :param with_us: If ``True``, include microseconds in the time format.
    :param with_tz: If ``True``, include timezone in the time format.
    :return: The extended combined date and time format string.
    """
    return extended_date_format() + extended_time_format(with_us, with_tz)


iso_date_format = extended_date_format
iso_time_format = extended_time_format
iso_format = extended_format


@singleton
def iso_formats() -> list[str]:
    """
    Returns a list of supported ISO 8601 date and time format strings, including both basic and extended forms, with
    optional microseconds and timezone.

    :return: A list of ISO 8601 format strings.
    """
    return [
        extended_format(True, False),
        extended_format(False, True),
        extended_format(True, True),
        extended_format(False, False),
        extended_date_format(),
        extended_time_format(True, False),
        extended_time_format(False, True),
        extended_time_format(True, True),
        extended_time_format(False, False),
        basic_format(True, False),
        basic_format(False, True),
        basic_format(True, True),
        basic_format(False, False),
        basic_date_format(),
        basic_time_format(True, False),
        basic_time_format(False, True),
        basic_time_format(True, True),
        basic_time_format(False, False),
    ]


@singleton
def dt_utc_min() -> datetime.datetime:
    return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


@singleton
def dt_utc_max() -> datetime.datetime:
    """
    Returns the maximum representable UTC datetime.

    :return: The maximum UTC datetime.
    """
    return datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)


@singleton
def dt_utc_epoch() -> datetime.datetime:
    """
    Returns the UTC datetime representing the POSIX epoch (1970-01-01T00:00:00Z).

    :return: The UTC epoch datetime.
    """
    return datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)


dt_utc_infinity = dt_utc_max


def dt_utc_now() -> datetime.datetime:
    """
    Returns the current date and time in UTC.

    :return: The current UTC datetime.
    """
    return datetime.datetime.now(tz=datetime.timezone.utc)


def dt_utc(
    year: int,
    month: int = None,
    day: int = None,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0
) -> datetime.datetime:
    """
    Returns a UTC datetime instance for the specified date and time components.

    :param year: Year component.
    :param month: Month component.
    :param day: Day component.
    :param hour: Hour component.
    :param minute: Minute component.
    :param second: Second component.
    :param microsecond: Microsecond component.
    :return: The specified UTC datetime.
    """
    return datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo=datetime.timezone.utc)


def td_to_us(td: datetime.timedelta) -> int:
    """
    Returns the total number of microseconds in the given ``timedelta``.

    :param td: The ``timedelta`` to convert.
    :return: The total number of microseconds in ``td``.
    """
    return (td.days * 86400 + td.seconds) * 1000000 + td.microseconds


def td_from_us(us: int) -> datetime.timedelta:
    """
    Returns a ``timedelta`` representing the given number of microseconds.

    :param us: The number of microseconds.
    :return: The corresponding ``timedelta``.
    """
    return datetime.timedelta(microseconds=us)


def td_to_time(td: datetime.timedelta) -> datetime.time:
    """
    Returns a ``time`` object representing the given ``timedelta``.

    :param td: The ``timedelta`` to convert.
    :return: The corresponding ``time`` object.
    """
    return (dt_utc_min() + td).timetz()


def td_from_time(t: datetime.time) -> datetime.timedelta:
    """
    Returns a ``timedelta`` representing the given ``time``.

    :param t: The ``time`` to convert.
    :return: The corresponding ``timedelta``.
    """
    return datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)


def dt_to_td(dt: datetime.datetime) -> datetime.timedelta:
    """
    Returns the ``timedelta`` between the given ``datetime`` and the POSIX epoch.

    :param dt: The ``datetime`` to convert.
    :return: The ``timedelta`` from the POSIX epoch to ``dt``.
    """
    return dt.replace(tzinfo=datetime.timezone.utc) - dt_utc_epoch()


def dt_to_ts(dt: datetime.datetime) -> float:
    """
    Returns the timestamp in seconds (as a float) for the given ``datetime`` since the POSIX epoch.

    :param dt: The ``datetime`` to convert.
    :return: The timestamp in seconds from the POSIX epoch.
    """
    return dt_to_ts_us(dt) / 1.0e6


def dt_to_ts_us(dt: datetime.datetime) -> int:
    """
    Returns the timestamp in microseconds (as an integer) for the given ``datetime`` since the POSIX epoch.

    :param dt: The ``datetime`` to convert.
    :return: The timestamp in microseconds from the POSIX epoch.
    """
    return td_to_us(dt_to_td(dt))


def dt_from_td(td: datetime.timedelta) -> datetime.datetime:
    """
    Returns the UTC datetime corresponding to the given ``timedelta`` from the POSIX epoch.

    :param td: The ``timedelta`` from the POSIX epoch.
    :return: The corresponding UTC datetime.
    """
    return dt_utc_epoch() + td


def dt_from_ts(ts: float) -> datetime.datetime:
    """
    Returns the UTC datetime corresponding to the given timestamp in seconds from the POSIX epoch.

    :param ts: Timestamp in seconds from the POSIX epoch.
    :return: The corresponding UTC datetime.
    """
    return dt_from_ts_us(round(ts * 1.0e6))


def dt_from_ts_us(ts: int) -> datetime.datetime:
    """
    Returns the UTC datetime corresponding to the given timestamp in microseconds from the POSIX epoch.

    :param ts: Timestamp in microseconds from the POSIX epoch.
    :return: The corresponding UTC datetime.
    """
    return dt_from_td(td_from_us(ts))


basic_date_regex: re.Pattern[str] = re.compile(r"(\d{4})(\d{2})(\d{2})")
extended_date_regex: re.Pattern[str] = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
basic_time_regex: re.Pattern[str] = re.compile(r"T(\d{2})(\d{2})(\d{2})(\.\d{1,6})?")
extended_time_regex: re.Pattern[str] = re.compile(r"T(\d{2}):(\d{2}):(\d{2})(\.\d{1,6})?")
basic_tz_regexp: re.Pattern[str] = re.compile(r"([+-])(\d{2})(\d{2})")
extended_tz_regexp: re.Pattern[str] = re.compile(r"([+-])(\d{2}):(\d{2})")


def dt_parse(dt_str: str, fmt_str: str | Sequence[str]) -> datetime.datetime | None:
    """
    Safely parses a string value representing a datetime into a ``datetime`` instance. Supports multiple format
    candidates and handles ISO 8601 timezone formats.

    :param dt_str: String value representing the datetime.
    :param fmt_str: Format string, or a sequence of format string candidates.
    :return: The parsed ``datetime`` instance, or ``None`` if input is ``None``.
    :raises ValueError: If no format matches the input string.
    """
    if dt_str is None:
        return None

    if isinstance(fmt_str, str):
        for tz_directive in ["%z", "%:z"]:
            if tz_directive in fmt_str:
                if tz_directive == "%:z":
                    # Replaces ISO 8601 timezone format "%:z" (e.g., "+01:00") with "%z" (e.g., "+0100")
                    # because ``datetime.strptime`` does not support "%:z".
                    dt_str = extended_tz_regexp.sub(r"\1\2\3", dt_str)
                    fmt_str = fmt_str.replace("%:z", "%z")
                return datetime.datetime.strptime(dt_str, fmt_str)
        return datetime.datetime.strptime(dt_str, fmt_str).replace(tzinfo=datetime.timezone.utc)
    elif isinstance(fmt_str, Sequence):
        for s in fmt_str:
            try:
                return dt_parse(dt_str, s)
            except ValueError:
                pass
        raise ValueError(f"time data '{dt_str}' does not match the given formats")
    else:
        raise ValueError("malformed format")


def dt_format(dt: datetime.datetime, fmt_str: str) -> str | None:
    """
    Safely formats a ``datetime`` instance as a string using the specified format. Handles ISO 8601 timezone formats and
    supports years with fewer than four digits.

    :param dt: The ``datetime`` instance to format.
    :param fmt_str: The format string.
    :return: The formatted string, or ``None`` if input is ``None``.
    """
    if dt is None or fmt_str is None:
        return None

    if dt.year < 1000 and "%Y" in fmt_str:
        year_str = str(dt.year).zfill(4)
        fmt_str = fmt_str.replace("%Y", year_str)

    if dt.year < 10 and "%y" in fmt_str:
        year_str = str(dt.year).zfill(2)
        fmt_str = fmt_str.replace("%y", year_str)

    # Manually handles the "%:z" timezone directive, since ``datetime.strftime``
    # does not support it before Python 3.12
    if sys.version_info < (3, 12):
        if "%:z" in fmt_str:
            tz_str = basic_tz_regexp.sub(r"\1\2:\3", dt.strftime("%z"))
            fmt_str = fmt_str.replace("%:z", tz_str)

    return dt.strftime(fmt_str)


def dt_parse_iso(dt_str: str) -> datetime.datetime | None:
    """
    Parses a string as an ISO 8601 datetime using all supported ISO format candidates.

    :param dt_str: String value representing the datetime.
    :return: The parsed ``datetime`` instance, or ``None`` if input is ``None``.
    """
    return dt_parse(dt_str, iso_formats())


def dt_format_iso(dt: datetime.datetime) -> str | None:
    """
    Formats a ``datetime`` instance as an ISO 8601 string using the default ISO format.

    :param dt: The ``datetime`` instance to format.
    :return: The formatted ISO 8601 string, or ``None`` if input is ``None``.
    """
    return dt_format(dt, iso_format())
