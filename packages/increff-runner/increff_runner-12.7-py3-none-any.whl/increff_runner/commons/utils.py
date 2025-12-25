# TODO @jaynit Delete this if not required #cr1_unni

from __future__ import annotations
from typing import TypeVar, TYPE_CHECKING, Any
from dotenv import dotenv_values
from datetime import date

if TYPE_CHECKING:
    from . import TsvMan
SPECIAL_CHARS = ["'", "\\"]

T = TypeVar("T")


def normalize(s: T | tuple) -> T | str | tuple:
    if s is None:
        return ""
    if isinstance(s, int) or isinstance(s, float):
        return s
    if isinstance(s, str):
        return s.upper().replace('"', "")
    if isinstance(s, tuple):
        return tuple(map(normalize, s))
    if isinstance(s, date):
        return str(s)
    raise NotImplementedError(f"Normalize is not implemented for type `{type(s)}`")


def minimum(l: list(str)):
    return min(list(map(lambda i: int(i), l)))


def create_map(tsv: TsvMan):
    data_map = dict()
    for _, row in tsv.iterrows():
        keyValue = tuple(map(lambda i: row[i], tsv.key))
        data_map[keyValue] = row
    return data_map


def is_string_empty(s: str | None):
    return s is None or len(s.strip()) == 0


def validate_string(lno: int, col: str, val: str):
    if val is not None and not any(map(lambda c: c in val, SPECIAL_CHARS)):
        return ""
    return f"{lno + 1}: Invalid {col} {val} No special characters(', \\, null) allowed"


def get_config(key: str):
    return dotenv_values("loadapi.conf").get(key)


def build_filepath(ftype: str | None, tablename: str, ext: str = ".tsv"):
    if ftype is None:
        raise ValueError("File type can't be None")
    return f"{ftype}/{tablename}"


def day_of_week(weekday: int):
    """
    :param weekday: Day of Week as an ISO number
    1 - Monday, 2 - Tuesday, ...
    """
    pref = ""
    if weekday == 1:
        pref = "MON"
    elif weekday == 2:
        pref = "TUES"
    elif weekday == 3:
        pref = "WEDNES"
    elif weekday == 4:
        pref = "THURS"
    elif weekday == 5:
        pref = "FRI"
    elif weekday == 6:
        pref = "SATUR"
    elif weekday == 7:
        pref = "SUN"
    else:
        raise ValueError("Invalid day of week")
    return f"{pref}DAY"
