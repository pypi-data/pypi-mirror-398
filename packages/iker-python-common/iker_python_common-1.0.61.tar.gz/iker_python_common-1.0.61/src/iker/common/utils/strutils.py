import datetime
from collections.abc import Callable
from typing import Any

from iker.common.utils.dtutils import dt_parse_iso

__all__ = [
    "is_none",
    "is_empty",
    "is_blank",
    "trim_to_none",
    "trim_to_empty",
    "parse_bool",
    "parse_bool_or",
    "parse_int_or",
    "parse_float_or",
    "parse_str_or",
    "str_conv",
    "repr_data",
    "parse_params_string",
    "make_params_string",
    "strip_margin",
]


def is_none(s: str) -> bool:
    return s is None


def is_empty(s: str) -> bool:
    return is_none(s) or len(s) == 0


def is_blank(s: str) -> bool:
    return is_empty(s) or is_empty(s.strip())


def trim_to_none(s: str, chars: str | None = None) -> str | None:
    if is_none(s):
        return None
    s = s.strip(chars)
    if is_empty(s):
        return None
    return s


def trim_to_empty(s: str, chars: str = None) -> str:
    if is_none(s):
        return ""
    return s.strip(chars)


def parse_bool(v: Any) -> bool:
    if v is None:
        return False
    elif isinstance(v, (int, float)):
        return bool(v)
    elif isinstance(v, str):
        if not v:
            return False
        if v.lower() in ["true", "yes", "on", "1", "y"]:
            return True
        if v.lower() in ["false", "no", "off", "0", "n"]:
            return False
        raise ValueError(f"not a valid boolean literal '{v}'")
    elif isinstance(v, bool):
        return v
    else:
        raise ValueError(f"type '{type(v)}' is not convertible to bool")


def parse_bool_or(v: Any, default: bool | None = False) -> bool | None:
    try:
        return parse_bool(v)
    except ValueError:
        return default


def parse_int_or(v: Any, default: int | None = 0) -> int | None:
    try:
        if isinstance(v, str):
            return int(v, 0)
        return int(v)
    except (TypeError, ValueError):
        return default


def parse_float_or(v: Any, default: float | None = 0.0) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def parse_str_or(v: Any, default: str | None = "") -> str | None:
    try:
        return str(v)
    except (TypeError, ValueError):
        return default


def str_conv(s: Any) -> int | float | bool | str | datetime.datetime:
    if type(s) in (int, float, bool, datetime.datetime):
        return s
    value = parse_int_or(s, None)
    if value is not None:
        return value
    value = parse_float_or(s, None)
    if value is not None:
        return value
    value = parse_bool_or(s, None)
    if value is not None:
        return value
    try:
        value = dt_parse_iso(s)
        if value is not None:
            return value
    except Exception:
        pass
    return s


def repr_data(o) -> str:
    if isinstance(o, object):
        return "{}({})".format(o.__class__.__name__, ",".join("{}={}".format(k, v) for k, v in vars(o).items()))
    return str(o)


def parse_params_string(
    s: str,
    *,
    delim: str = ",",
    kv_delim: str = "=",
    neg_prefix: str = "-",
    str_parser: Callable[[str], Any] = str,
    true_value: Any = True,
    false_value: Any = False,
) -> dict[str, Any]:
    if is_blank(s):
        return {}

    result = {}
    for param in s.split(delim):
        match param.split(kv_delim, 1):
            case [key]:
                if len(key) == 0 or key == neg_prefix:
                    continue
                if key.startswith(neg_prefix):
                    result[key[len(neg_prefix):]] = false_value
                else:
                    result[key] = true_value
            case [key, value]:
                if len(key) == 0 or key == neg_prefix:
                    continue
                result[key] = str_parser(value)
            case _:
                raise ValueError(f"malformed param '{param}'")
    return result


def make_params_string(
    params: dict[str, Any],
    *,
    delim: str = ",",
    kv_delim: str = "=",
    neg_prefix: str = "-",
    str_maker: Callable[[Any], str] = str,
) -> str:
    if len(params or {}) == 0:
        return ""

    kv_strs = []
    for key, value in params.items():
        if len(key) == 0 or key == neg_prefix:
            continue
        if isinstance(value, bool):
            kv_strs.append(key if value is True else neg_prefix + key)
        else:
            kv_strs.append(kv_delim.join((key, str_maker(value))))
    return delim.join(kv_strs)


def strip_margin(text: str, *, margin_char: str = "|", line_concat: str = " ") -> str:
    stripped_text = ""
    last_stripped_line = ""
    for lineno, line in enumerate(text.splitlines()):
        stripped_line = line.lstrip()
        if stripped_line.startswith(margin_char):
            stripped_line = stripped_line[len(margin_char):]
        if len(stripped_line) == 0:
            if lineno > 0:
                stripped_text += "\n"
        elif len(last_stripped_line) > 0:
            stripped_text += line_concat + stripped_line
        else:
            stripped_text += stripped_line
        last_stripped_line = stripped_line
    return stripped_text
