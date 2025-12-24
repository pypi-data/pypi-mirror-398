# cython: language_level=3
# cython: wraparound=False
# cython: boundscheck=False

# Cython imports
import cython
from cython.cimports import numpy as np  # type: ignore
from cython.cimports.cpython import datetime  # type: ignore
from cython.cimports.cpython.set import PySet_Contains as set_contains  # type: ignore


np.import_array()
np.import_umath()
datetime.import_datetime()

# Python imports
import numpy as np
import pandas as pd
import datetime, zoneinfo
from functools import lru_cache as _lru_cache
from cytimes import errors

# Constants --------------------------------------------------------------------------------------------
# . argument
SENTINEL: int = -1
# . pandas
NAT: object = pd.NaT
# . calendar
# fmt: off
DAYS_BR_MONTH: cython.int[13] = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
DAYS_IN_MONTH: cython.int[13] = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DAYS_BR_QUARTER: cython.int[5] = [0, 90, 181, 273, 365]
DAYS_IN_QUARTER: cython.int[5] = [0, 90, 91, 92, 92]
# fmt: on
# . date
ORDINAL_MAX: cython.int = 3_652_059
# . datetime
#: EPOCH (1970-01-01)
EPOCH_DT: datetime.datetime = datetime.datetime_new(
    1970, 1, 1, 0, 0, 0, 0, datetime.get_utc(), 0
)
EPOCH_YEAR: cython.longlong = 1970
EPOCH_MONTH: cython.longlong = 23_628
EPOCH_DAY: cython.longlong = 719_163
EPOCH_HOUR: cython.longlong = EPOCH_DAY * 24
EPOCH_MINUTE: cython.longlong = EPOCH_HOUR * 60
EPOCH_SECOND: cython.longlong = EPOCH_MINUTE * 60
EPOCH_MILLISECOND: cython.longlong = EPOCH_SECOND * 1_000
EPOCH_MICROSECOND: cython.longlong = EPOCH_MILLISECOND * 1_000
#: EPOCH pre-compute
EPOCH_C4: cython.longlong = math_div_floor(1970, 4)  # type: ignore
EPOCH_C100: cython.longlong = math_div_floor(1970, 100)  # type: ignore
EPOCH_C400: cython.longlong = math_div_floor(1970, 400)  # type: ignore
EPOCH_CBASE: cython.longlong = EPOCH_C4 - EPOCH_C100 + EPOCH_C400
# . timezone
UTC: datetime.tzinfo = datetime.get_utc()
T_TIMEZONE: object = datetime.timezone
T_ZONEINFO: object = zoneinfo.ZoneInfo
NULL_TZOFFSET: cython.int = -100_000  # Sentinel for null offset
# . conversion for seconds
SS_MINUTE: cython.longlong = 60
SS_HOUR: cython.longlong = SS_MINUTE * 60
SS_DAY: cython.longlong = SS_HOUR * 24
# . conversion for milliseconds
MS_SECOND: cython.longlong = 1_000
MS_MINUTE: cython.longlong = MS_SECOND * 60
MS_HOUR: cython.longlong = MS_MINUTE * 60
MS_DAY: cython.longlong = MS_HOUR * 24
# . conversion for microseconds
US_MILLISECOND: cython.longlong = 1_000
US_SECOND: cython.longlong = US_MILLISECOND * 1_000
US_MINUTE: cython.longlong = US_SECOND * 60
US_HOUR: cython.longlong = US_MINUTE * 60
US_DAY: cython.longlong = US_HOUR * 24
# . conversion for nanoseconds
NS_MICROSECOND: cython.longlong = 1_000
NS_MILLISECOND: cython.longlong = NS_MICROSECOND * 1_000
NS_SECOND: cython.longlong = NS_MILLISECOND * 1_000
NS_MINUTE: cython.longlong = NS_SECOND * 60
NS_HOUR: cython.longlong = NS_MINUTE * 60
NS_DAY: cython.longlong = NS_HOUR * 24
# . conversion for timedelta64
TD64_YY_DAY: cython.double = 365.2425  # Exact days in a year for td64
TD64_YY_SECOND: cython.longlong = int(TD64_YY_DAY * SS_DAY)
TD64_YY_MILLISECOND: cython.longlong = TD64_YY_SECOND * 1_000
TD64_YY_MICROSECOND: cython.longlong = TD64_YY_MILLISECOND * 1_000
TD64_YY_NANOSECOND: cython.longlong = TD64_YY_MICROSECOND * 1_000
TD64_MM_DAY: cython.double = 30.436875  # Exact days in a month for td64
TD64_MM_SECOND: cython.longlong = int(TD64_MM_DAY * SS_DAY)
TD64_MM_MILLISECOND: cython.longlong = TD64_MM_SECOND * 1_000
TD64_MM_MICROSECOND: cython.longlong = TD64_MM_MILLISECOND * 1_000
TD64_MM_NANOSECOND: cython.longlong = TD64_MM_MICROSECOND * 1_000
# . datetime64 range
#: Minimum datetime64 in nanoseconds (1677-09-21 00:12:43.145224193)
DT64_NS_YY_MIN: cython.longlong = -293  # >= 1678
DT64_NS_MM_MIN: cython.longlong = -3_508  # >= 1677-10
DT64_NS_WW_MIN: cython.longlong = -15_251  # >= 1677-09-30
DT64_NS_DD_MIN: cython.longlong = -106_751  # >= 1677-09-22
DT64_NS_HH_MIN: cython.longlong = DT64_NS_DD_MIN * 24
DT64_NS_MI_MIN: cython.longlong = DT64_NS_HH_MIN * 60
DT64_NS_SS_MIN: cython.longlong = DT64_NS_MI_MIN * 60
DT64_NS_MS_MIN: cython.longlong = DT64_NS_SS_MIN * 1_000
DT64_NS_US_MIN: cython.longlong = DT64_NS_MS_MIN * 1_000
DT64_NS_NS_MIN: cython.longlong = DT64_NS_US_MIN * 1_000
#: Maximum datetime64 in nanoseconds (2262-04-11 23:47:16.854775807)
DT64_NS_YY_MAX: cython.longlong = 292  # <= 2262
DT64_NS_MM_MAX: cython.longlong = 3_507  # <= 2262-03
DT64_NS_WW_MAX: cython.longlong = 15_250  # <= 2262-04-03
DT64_NS_DD_MAX: cython.longlong = 106_750  # <= 2262-04-10
DT64_NS_HH_MAX: cython.longlong = DT64_NS_DD_MAX * 24
DT64_NS_MI_MAX: cython.longlong = DT64_NS_HH_MAX * 60
DT64_NS_SS_MAX: cython.longlong = DT64_NS_MI_MAX * 60
DT64_NS_MS_MAX: cython.longlong = DT64_NS_SS_MAX * 1_000
DT64_NS_US_MAX: cython.longlong = DT64_NS_MS_MAX * 1_000
DT64_NS_NS_MAX: cython.longlong = DT64_NS_US_MAX * 1_000
# . datetime64 dtype
DT64_DTYPE_YY: np.dtype = np.dtype("datetime64[Y]")
DT64_DTYPE_MM: np.dtype = np.dtype("datetime64[M]")
DT64_DTYPE_WW: np.dtype = np.dtype("datetime64[W]")
DT64_DTYPE_DD: np.dtype = np.dtype("datetime64[D]")
DT64_DTYPE_HH: np.dtype = np.dtype("datetime64[h]")
DT64_DTYPE_MI: np.dtype = np.dtype("datetime64[m]")
DT64_DTYPE_SS: np.dtype = np.dtype("datetime64[s]")
DT64_DTYPE_MS: np.dtype = np.dtype("datetime64[ms]")
DT64_DTYPE_US: np.dtype = np.dtype("datetime64[us]")
DT64_DTYPE_NS: np.dtype = np.dtype("datetime64[ns]")
DT64_DTYPE_PS: np.dtype = np.dtype("datetime64[ps]")
DT64_DTYPE_FS: np.dtype = np.dtype("datetime64[fs]")
DT64_DTYPE_AS: np.dtype = np.dtype("datetime64[as]")
# . numpy datetime units
DT_NPY_UNIT_YY: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_Y
DT_NPY_UNIT_MM: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_M
DT_NPY_UNIT_WW: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_W
DT_NPY_UNIT_DD: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_D
DT_NPY_UNIT_HH: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_h
DT_NPY_UNIT_MI: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_m
DT_NPY_UNIT_SS: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_s
DT_NPY_UNIT_MS: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_ms
DT_NPY_UNIT_US: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_us
DT_NPY_UNIT_NS: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_ns
DT_NPY_UNIT_PS: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_ps
DT_NPY_UNIT_FS: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_fs
DT_NPY_UNIT_AS: cython.int = np.NPY_DATETIMEUNIT.NPY_FR_as


# datetime.tzinfo --------------------------------------------------------------------------------------
def _get_local_timezone() -> object:
    """(internal) Get the process-local timezone `<'datetime.tzinfo'>`.

    :returns `<'zoneinfo.ZoneInfo/datetime.timezone'>`: The local timezone.

        - Returns a concrete IANA zone (`zoneinfo.ZoneInfo`) when possible
          using [babel](https://github.com/python-babel/babel) `LOCALTZ` name.
        - If that fails, falls back to a fixed-offset `datetime.timezone` using
          the **current** local UTC offset (but no DST rules).

    ## Notice
    - The fixed-offset fallback reflects the offset *at the moment of call* and
      does not track historical or future transitions.
    """
    from babel.dates import LOCALTZ

    if isinstance(LOCALTZ, T_ZONEINFO):
        return LOCALTZ
    try:
        return T_ZONEINFO(LOCALTZ.zone)
    except Exception:
        return tz_new(0, 0, tz_local_sec(None))  # type: ignore


_LOCAL_TIMEZONE: object = _get_local_timezone()


@_lru_cache(maxsize=128)
def _get_zoneinfo(name: str) -> zoneinfo.ZoneInfo | datetime.timezone:
    """(internal) Get `zoneinfo.ZoneInfo` object by name with caching."""
    name_lower: str = name.lower()
    if name_lower == "local":
        return _LOCAL_TIMEZONE  # type: ignore
    if set_contains(_UTC_ALIASES, name_lower):  # type: ignore
        return UTC
    try:
        return T_ZONEINFO(name)
    except Exception as err:
        raise errors.InvalidTimezoneError("Invalid timezone name '%s'" % name) from err


_UTC_ALIASES: set = {
    "z",
    "utc",
    "gmt",
    "gmt0",
    "gmt+0",
    "gmt-0",
    "zulu",
    "universal",
    "greenwich",
    "etc/utc",
    "etc/gmt",
    "etc/gmt0",
    "etc/gmt+0",
    "etc/gmt-0",
    "etc/zulu",
    "etc/universal",
}


@cython.cfunc
@cython.inline(True)
def tz_parse(tz: zoneinfo.ZoneInfo | datetime.timezone | str | None) -> object:
    """(cfunc) Parse timezone input to `<'zoneinfo.ZoneInfo/datetime.timezone/None'>`.

    :param tz `<'datetime.timezone/zoneinfo.ZoneInfo/pytz/str/None'>`: The timezone object.

        - If 'tz' is `None` → return `None`.
        - If 'tz' is `datetime.timezone/zoneinfo.ZoneInfo` → return as-is.
        - If 'tz' is `str` →:

            - `"local"` (case-insensitive) → cached local timezone
            - common UTC aliases (case-insensitive) → UTC
            - otherwise interpreted as a canonical IANA key via ZoneInfo

        - If 'tz' is `pytz` timezone → mapped by its `zone` name to a `ZoneInfo`.

    :returns `<'zoneinfo.ZoneInfo/datetime.timezone/None'>`: The normalized timezone object.
    :raises `InvalidTimezoneError`: If 'tz' is invalid or unrecognized.
    """
    # None
    if tz is None:
        return tz  # exit: as-is

    # zoneinfo.ZoneInfo / datetime.timezone
    dtype = type(tz)
    if dtype is T_ZONEINFO or dtype is T_TIMEZONE:
        return tz  # exit: as-is

    # 'str' timezone name
    if isinstance(tz, str):
        return _get_zoneinfo(tz)

    # 'key' attribute: ZoneInfo subclass
    exc = None
    if hasattr(tz, "key"):
        try:
            return _get_zoneinfo(tz.key)
        except Exception as err:
            exc = err

    # name attribute: ZoneInfo subclass
    if hasattr(tz, "name"):
        try:
            return _get_zoneinfo(tz.name)
        except Exception as err:
            exc = err

    # 'zone' attribute: pytz
    if hasattr(tz, "zone"):
        try:
            return _get_zoneinfo(tz.zone)
        except Exception as err:
            exc = err

    # Unsupported type
    if exc is None:
        raise errors.InvalidTimezoneError(
            "Unsupported timezone '%s' %s" % (tz, type(tz))
        )
    else:
        raise errors.InvalidTimezoneError(
            "Unsupported timezone '%s' %s\nError: %s" % (tz, type(tz), exc)
        ) from exc


########## The REST utility functions are in the utils.pxd file ##########
########## The following functions are for testing purpose only ##########
def _test_utils() -> None:
    # Parser
    _test_parser()
    # Time
    _test_localtime_n_gmtime()
    # Calendar
    _test_is_leap_year()
    _test_days_bf_year()
    _test_doy()
    _test_quarter_of_month()
    _test_days_in_quarter()
    _test_days_in_month()
    _test_days_bf_month()
    _test_weekday()
    _test_isocalendar()
    _test_iso_week1_mon_ord()
    _test_ymd_to_ord()
    _test_ymd_fr_ord()
    _test_ymd_fr_iso()
    # datetime.date
    _test_date_generate()
    _test_date_type_check()
    _test_date_conversion()
    # datetime.datetime
    _test_dt_generate()
    _test_dt_type_check()
    _test_dt_tzinfo()
    _test_dt_conversion()
    _test_dt_mainipulate()
    _test_dt_arithmetic()
    _test_dt_normalize_tz()
    # datetime.time
    _test_time_generate()
    _test_time_type_check()
    _test_time_conversion()
    # datetime.timedelta
    _test_timedelta_generate()
    _test_timedelta_type_check()
    _test_timedelta_conversion()
    # datetime.tzinfo
    _test_tzinfo_generate()
    _test_tzinfo_type_check()
    _test_tzinfo_access()
    # numpy.share
    _test_numpy_share()
    # numpy.datetime64
    _test_datetime64_type_check()
    _test_datetime64_conversion()
    # numpy.timedelta64
    _test_timedelta64_type_check()
    _test_timedelta64_conversion()
    # numpy.ndarray
    _test_ndarray_type_check()
    _test_ndarray_generate()
    _test_ndarray_dt64_type_check()
    _test_ndarray_dt64_conversion()
    _test_ndarray_td64_type_check()
    _test_ndarray_td64_conversion()
    # math
    _test_math()
    _test_ndarray_math()
    _test_slice_to_uint()
    _test_slice_to_ufloat()
    # hmsf
    _test_sec_to_us()
    _cross_test_with_ndarray()


# Parser
def _test_parser() -> None:
    # boolean
    for i in range(128):
        s = chr(i)
        # is_iso_sep
        if s in ("t", "T", " "):
            assert is_iso_sep(i)  # type: ignore
            assert is_str_iso_sep(s)  # type: ignore
        else:
            assert not is_iso_sep(i)  # type: ignore
            assert not is_str_iso_sep(s)  # type: ignore
        # is_date_sep
        if s in ("-", "/", "."):
            assert is_date_sep(i)  # type: ignore
            assert is_str_date_sep(s)  # type: ignore
        else:
            assert not is_date_sep(i)  # type: ignore
            assert not is_str_date_sep(s)  # type: ignore
        # is_time_sep
        if s == ":":
            assert is_time_sep(i)  # type: ignore
            assert is_str_time_sep(s)  # type: ignore
        else:
            assert not is_time_sep(i)  # type: ignore
            assert not is_str_time_sep(s)  # type: ignore
        # is_isoweek_sep
        if s in ("w", "W"):
            assert is_isoweek_sep(i)  # type: ignore
            assert is_str_isoweek_sep(s)  # type: ignore
        else:
            assert not is_isoweek_sep(i)  # type: ignore
            assert not is_str_isoweek_sep(s)  # type: ignore
        # is_ascii_digit
        if s in "0123456789":
            assert is_ascii_digit(i)  # type: ignore
            assert is_str_ascii_digits(s)  # type: ignore
        else:
            assert not is_ascii_digit(i)  # type: ignore
            assert not is_str_ascii_digits(s)  # type: ignore
        # is_ascii_letter_upper
        if s in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert is_ascii_letter_upper(i)  # type: ignore
            assert is_str_ascii_letters_upper(s)  # type: ignore
        else:
            assert not is_ascii_letter_upper(i)  # type: ignore
            assert not is_str_ascii_letters_upper(s)  # type: ignore
        # is_ascii_letter_lower
        if s in "abcdefghijklmnopqrstuvwxyz":
            assert is_ascii_letter_lower(i)  # type: ignore
            assert is_str_ascii_letters_lower(s)  # type: ignore
        else:
            assert not is_ascii_letter_lower(i)  # type: ignore
            assert not is_str_ascii_letters_lower(s)  # type: ignore
        # alphabetic
        if s in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
            assert is_ascii_letter(i)  # type: ignore
            assert is_str_ascii_letters(s)  # type: ignore
            assert is_alpha(i)  # type: ignore
            assert is_str_alphas(s)  # type: ignore
        else:
            assert not is_ascii_letter(i)  # type: ignore
            assert not is_str_ascii_letters(s)  # type: ignore
            assert not is_alpha(i)  # type: ignore
            assert not is_str_alphas(s)  # type: ignore
        # ctl
        if i < 32 or i == 127:
            assert is_ascii_ctl(i)  # type: ignore
            assert is_str_ascii_ctl(s)  # type: ignore
        else:
            assert not is_ascii_ctl(i)  # type: ignore
            assert not is_str_ascii_ctl(s)  # type: ignore
        # ctl or space
        if i <= 32 or i == 127:
            assert is_ascii_ctl_or_space(i)  # type: ignore
            assert is_str_ascii_ctl_or_space(s)  # type: ignore
        else:
            assert not is_ascii_ctl_or_space(i)  # type: ignore
            assert not is_str_ascii_ctl_or_space(s)  # type: ignore

    for k in (None, ""):
        assert not is_str_iso_sep(k)  # type: ignore
        assert not is_str_date_sep(k)  # type: ignore
        assert not is_str_time_sep(k)  # type: ignore
        assert not is_str_isoweek_sep(k)  # type: ignore
        assert not is_str_ascii_ctl(k)  # type: ignore
        assert not is_str_ascii_ctl_or_space(k)  # type: ignore
        assert not is_str_ascii_digits(k)  # type: ignore
        assert not is_str_ascii_letters_upper(k)  # type: ignore
        assert not is_str_ascii_letters_lower(k)  # type: ignore
        assert not is_str_ascii_letters(k)  # type: ignore
        assert not is_str_alphas(k)  # type: ignore

    # Alphabetic extend case
    for i in range(192, 208):
        assert not is_ascii_letter(i)  # type: ignore
        assert not is_str_ascii_letters(chr(i))  # type: ignore
        assert is_alpha(i)  # type: ignore
        assert is_str_alphas(chr(i))  # type: ignore

    # Parse
    # . parse_numeric_kind
    assert parse_numeric_kind("1", 0) == 1  # type: ignore
    assert parse_numeric_kind("1.", 0) == 2  # type: ignore
    assert parse_numeric_kind("1.1", 0) == 2  # type: ignore
    assert parse_numeric_kind(".1", 0) == 2  # type: ignore
    assert parse_numeric_kind("0.1", 0) == 2  # type: ignore
    assert parse_numeric_kind("", 0) == 0  # type: ignore
    assert parse_numeric_kind(None, 0) == 0  # type: ignore
    assert parse_numeric_kind("1a", 0) == 0  # type: ignore

    # . parse_isoyear
    t: str = "2021-01-02T03:04:05.006007"
    assert parse_isoyear(t, 0) == 2021  # type: ignore
    assert parse_isoyear(t, 1) == -1  # type: ignore
    assert parse_isoyear(None, 1) == -1  # type: ignore

    # . parse_isomonth
    assert parse_isomonth(t, 5) == 1  # type: ignore
    assert parse_isomonth(t, 6) == -1  # type: ignore
    assert parse_isomonth(None, 6) == -1  # type: ignore

    # . parse_isoday
    assert parse_isoday(t, 8) == 2  # type: ignore
    assert parse_isoday(t, 9) == -1  # type: ignore
    assert parse_isoday(None, 9) == -1  # type: ignore

    # . parse_isoweek
    t = "2021-W52-6"
    assert parse_isoweek(t, 6) == 52  # type: ignore
    assert parse_isoweek(t, 7) == -1  # type: ignore
    assert parse_isoweek(None, 7) == -1  # type: ignore

    # . parse_isoweekday
    assert parse_isoweekday(t, 9) == 6  # type: ignore
    assert parse_isoweekday(t, 8) == -1  # type: ignore
    assert parse_isoweekday(t, 10) == -1  # type: ignore
    assert parse_isoweekday(t, 1) == -1  # type: ignore
    assert parse_isoweekday(t, 0) == 2  # type: ignore
    assert parse_isoweekday(None, 0) == -1  # type: ignore

    # . parse_isodoy
    t = "2021-365"
    assert parse_isodoy(t, 5) == 365  # type: ignore
    assert parse_isodoy(t, 6) == -1  # type: ignore
    assert parse_isodoy(t, 4) == -1  # type: ignore
    t = "2021-367"
    assert parse_isodoy(t, 5) == -1  # type: ignore
    t = "2021-000"
    assert parse_isodoy(t, 5) == -1  # type: ignore
    assert parse_isodoy(None, 4) == -1  # type: ignore

    # . parse_isohour
    t = "03:04:05"
    assert parse_isohour(t, 0) == 3  # type: ignore
    assert parse_isohour(t, 1) == -1  # type: ignore
    assert parse_isohour(None, 1) == -1  # type: ignore

    # . parse_isominute
    assert parse_isominute(t, 3) == 4  # type: ignore
    assert parse_isominute(t, 4) == -1  # type: ignore
    assert parse_isominute(None, 4) == -1  # type: ignore

    # . parse_isosecond
    assert parse_isosecond(t, 6) == 5  # type: ignore
    assert parse_isosecond(t, 7) == -1  # type: ignore
    assert parse_isosecond(None, 7) == -1  # type: ignore

    # . parse_isofraction
    assert parse_isofraction(".1", 1) == 100_000  # type: ignore
    assert parse_isofraction(".01", 1) == 10_000  # type: ignore
    assert parse_isofraction(".123456", 1) == 123456  # type: ignore
    assert parse_isofraction(".1234567", 1) == 123456  # type: ignore
    assert parse_isofraction("", 1) == -1  # type: ignore
    assert parse_isofraction(None, 1) == -1  # type: ignore

    # . parse_second_and_fraction
    for t, ss, us in (
        ("1", 1, -1),
        ("1.", 1, -1),
        ("1.0", 1, 0),
        ("1.12", 1, 120_000),
        ("1.123456", 1, 123_456),
        ("1.1234567", 1, 123_456),
        ("0.1", 0, 100_000),
        ("0.12", 0, 120_000),
        ("0.123456", 0, 123_456),
        ("0.1234567", 0, 123_456),
        (".1", 0, 100_000),
        (".12", 0, 120_000),
        (".123456", 0, 123_456),
        (".1234567", 0, 123_456),
    ):
        out = parse_second_and_fraction(t, 0)  # type: ignore
        assert out.second == ss, f"{t}: {out.second} != {ss}"
        assert out.microsecond == us, f"{t}: {out.microsecond} != {us}"

    out = parse_second_and_fraction("", 0)  # type: ignore
    assert out.second == -1, f"{out.second} != -1"
    assert out.microsecond == -1, f"{out.microsecond} != -1"
    out = parse_second_and_fraction(None, 0)  # type: ignore
    assert out.second == -1, f"{out.second} != -1"
    assert out.microsecond == -1, f"{out.microsecond} != -1"

    print("Passed: parser")


# Time
def _test_localtime_n_gmtime() -> None:
    import time, numpy as np

    for t in (-0.6, -0.5, -0.4, -0.1, 0, 0.1, 0.4, 0.5, 0.6, time.time()):
        cmp = time.localtime(t)
        _tm = tm_localtime(t)  # type: ignore
        assert _tm.tm_sec == cmp.tm_sec, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_min == cmp.tm_min, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_hour == cmp.tm_hour, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_mday == cmp.tm_mday, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_mon == cmp.tm_mon, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_year == cmp.tm_year, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_wday == cmp.tm_wday, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_yday == cmp.tm_yday, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_isdst == cmp.tm_isdst, f"{_tm.tm_sec} != {cmp.tm_sec}"

        cmp = time.gmtime(t)
        _tm = tm_gmtime(t)  # type: ignore
        assert _tm.tm_sec == cmp.tm_sec, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_min == cmp.tm_min, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_hour == cmp.tm_hour, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_mday == cmp.tm_mday, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_mon == cmp.tm_mon, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_year == cmp.tm_year, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_wday == cmp.tm_wday, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_yday == cmp.tm_yday, f"{_tm.tm_sec} != {cmp.tm_sec}"
        assert _tm.tm_isdst == cmp.tm_isdst, f"{_tm.tm_sec} != {cmp.tm_sec}"

    for t in (np.inf, -np.inf):
        try:
            tm_localtime(t)  # type: ignore
        except RuntimeError:
            pass
        else:
            raise AssertionError("Should raise RuntimeError")
        try:
            tm_gmtime(t)  # type: ignore
        except RuntimeError:
            pass
        else:
            raise AssertionError("Should raise RuntimeError")

    print("Passed: localtime & gmtime")

    del time


# Calendar
def _test_is_leap_year() -> None:
    from _pydatetime import _is_leap  # type: ignore

    for i in range(-10000, 10001):
        val = is_leap_year(i)  # type: ignore
        cmp = _is_leap(i)
        assert val == cmp, f"{i}: {val} != {cmp}"

    assert is_leap_year(0)  # type: ignore
    assert is_leap_year(-4)  # type: ignore
    assert not is_leap_year(-100)  # type: ignore
    assert is_leap_year(-400)  # type: ignore

    del _is_leap


def _test_days_bf_year() -> None:
    from _pydatetime import _days_before_year  # type: ignore

    for i in range(-10000, 10001):
        val = days_bf_year(i)  # type: ignore
        cmp = _days_before_year(i)
        assert val == cmp, f"{i}: {val} != {cmp}"

    print("Passed: days_bf_year")

    del _days_before_year


def _test_doy() -> None:

    for y in range(-10000, 10001):
        for m in range(1, 13):
            for d in range(1, 32):
                if d > 28:
                    d = min(d, days_in_month(y, m))  # type: ignore
                doy = day_of_year(y, m, d)  # type: ignore
                _ymd = ymd_fr_doy(y, doy)  # type: ignore
                assert _ymd.year == y, f"{y}-{m}-{d}: {y} != {_ymd.year}"
                assert _ymd.month == m, f"{y}-{m}-{d}: {m} != {_ymd.month}"
                assert _ymd.day == d, f"{y}-{m}-{d}: {d} != {_ymd.day}"

    print("Passed: ymd_fr_doy")


def _test_quarter_of_month() -> None:
    count: cython.int = 0
    value: cython.int = 1
    for i in range(1, 13):
        val = quarter_of_month(i)  # type: ignore
        cmp = value
        assert val == cmp, f"{i}: {val} != {cmp}"
        count += 1
        if count == 3:
            count = 0
            value += 1
    print("Passed: quarter_of_month")


def _test_days_in_quarter() -> None:
    # non-leap
    year: cython.int = 2021
    for i in range(1, 13):
        qtr: cython.int = quarter_of_month(i)  # type: ignore
        val = days_in_quarter(year, i)  # type: ignore
        cmp = DAYS_IN_QUARTER[qtr]
        assert val == cmp, f"{i}: {val} != {cmp}"
    # leap
    year = 2024
    for i in range(1, 13):
        qtr: cython.int = quarter_of_month(i)  # type: ignore
        val = days_in_quarter(year, i)  # type: ignore
        if qtr == 1:
            cmp = DAYS_IN_QUARTER[qtr] + 1
        else:
            cmp = DAYS_IN_QUARTER[qtr]
        assert val == cmp, f"{i}: {val} != {cmp}"
    print("Passed: days_in_quarter")


def _test_days_in_month() -> None:
    from _pydatetime import _days_in_month  # type: ignore

    for year in range(-1000, 1001):
        for i in range(1, 13):
            val = days_in_month(year, i)  # type: ignore
            cmp = _days_in_month(year, i)
            assert val == cmp, f"{year}-{i}: {val} != {cmp}"

    print("Passed: days_in_month")

    del _days_in_month


def _test_days_bf_month() -> None:
    from _pydatetime import _days_before_month  # type: ignore

    for year in range(-1000, 1001):
        for i in range(1, 13):
            val = days_bf_month(year, i)  # type: ignore
            cmp = _days_before_month(year, i)
            assert val == cmp, f"{i}: {val} != {cmp}"

    print("Passed: days_bf_month")

    del _days_before_month


def _test_weekday() -> None:
    from datetime import date

    year: cython.int
    month: cython.int
    day: cython.int
    for year in range(1, 10000):
        for month in range(1, 13):
            for day in range(1, 32):
                if day > 28:
                    day = min(day, days_in_month(year, month))  # type: ignore
                val = ymd_weekday(year, month, day)  # type: ignore
                cmp = date(year, month, day).weekday()
                assert val == cmp, f"{year}-{month}-{day}: {val} != {cmp}"
    print("Passed: weekday")

    del date


def _test_isocalendar() -> None:
    from datetime import date

    year: cython.int
    month: cython.int
    day: cython.int
    for year in range(1, 10000):
        for month in range(1, 13):
            for day in range(1, 32):
                if day > 28:
                    day = min(day, days_in_month(year, month))  # type: ignore
                cmp = date(year, month, day).isocalendar()
                iso_calr = ymd_isocalendar(year, month, day)  # type: ignore
                assert (
                    iso_calr.year == cmp.year
                ), f"{year}-{month}-{day}: {iso_calr.year} != {cmp.year}"
                assert (
                    iso_calr.week == cmp.week
                ), f"{year}-{month}-{day}: {iso_calr.week} != {cmp.week}"
                assert (
                    iso_calr.weekday == cmp.weekday
                ), f"{year}-{month}-{day}: {iso_calr.weekday} != {cmp.weekday}"

                iso_year = ymd_isoyear(year, month, day)  # type: ignore
                assert (
                    iso_year == cmp.year
                ), f"{year}-{month}-{day}: {iso_year} != {cmp.year}"
                iso_week = ymd_isoweek(year, month, day)  # type: ignore
                assert (
                    iso_week == cmp.week
                ), f"{year}-{month}-{day}: {iso_week} != {cmp.week}"
                iso_weekday = ymd_isoweekday(year, month, day)  # type: ignore
                assert (
                    iso_weekday == cmp.weekday
                ), f"{year}-{month}-{day}: {iso_weekday} != {cmp.weekday}"

    print("Passed: isocalendar")

    del date


def _test_iso_week1_mon_ord() -> None:
    from _pydatetime import _isoweek1monday  # type: ignore

    for year in range(1, 10000):
        val = iso_week1_mon_ord(year)  # type: ignore
        cmp = _isoweek1monday(year)
        assert val == cmp, f"{year}: {val} != {cmp}"
    print("Passed: iso_week1_mon_ord")

    del _isoweek1monday


def _test_ymd_to_ord() -> None:
    from _pydatetime import _ymd2ord  # type: ignore

    year: cython.int
    month: cython.int
    day: cython.int
    for year in range(-10000, 10001):
        for month in range(1, 13):
            for day in range(1, 32):
                if day > 28:
                    day = min(day, days_in_month(year, month))  # type: ignore
                val = ymd_to_ord(year, month, day)  # type: ignore
                cmp = _ymd2ord(year, month, day)
                assert val == cmp, f"{year}-{month}-{day}: {val} != {cmp}"
    print("Passed: ymd_to_ord")

    del _ymd2ord


def _test_ymd_fr_ord() -> None:
    from _pydatetime import _ord2ymd, _MAXORDINAL  # type: ignore

    for i in range(-_MAXORDINAL - 1000, _MAXORDINAL + 1001):
        val = ymd_fr_ord(i)  # type: ignore
        (y, m, d) = _ord2ymd(i)
        assert (
            val.year == y and val.month == m and val.day == d
        ), f"{i}: {val} != {y}-{m}-{d}"

    print("Passed: ymd_fr_ord")

    del _ord2ymd, _MAXORDINAL


def _test_ymd_fr_iso() -> None:
    from _pydatetime import _isoweek_to_gregorian  # type: ignore

    year: cython.int
    week: cython.int
    weekday: cython.int
    for year in range(1, 10000):
        for week in range(1, 54):
            for weekday in range(1, 8):
                try:
                    (y, m, d) = _isoweek_to_gregorian(year, week, weekday)
                except ValueError:
                    continue
                val = ymd_fr_iso(year, week, weekday)  # type: ignore
                if y == 10_000 or val.year == 10_000:
                    continue
                assert (
                    val.year == y and val.month == m and val.day == d
                ), f"{year}-{week}-{weekday}: {val} != {y}-{m}-{d}"

    print("Passed: ymd_fr_iso")

    del _isoweek_to_gregorian


# datetime.date
def _test_date_generate() -> None:
    import datetime
    from pendulum import Date

    tz = datetime.timezone(datetime.timedelta(hours=23, minutes=59))

    # New
    assert datetime.date(1, 1, 1) == date_new()  # type: ignore
    assert datetime.date(1, 1, 1) == date_new(1)  # type: ignore
    assert datetime.date(1, 1, 1) == date_new(1, 1)  # type: ignore
    assert datetime.date(1, 1, 1) == date_new(1, 1, 1)  # type: ignore
    assert type(date_new(1, 1, 1)) is datetime.date  # type: ignore
    assert type(date_new(1, 1, 1, None)) is datetime.date  # type: ignore
    assert type(date_new(1, 1, 1, datetime.date)) is datetime.date  # type: ignore
    assert type(date_new(1, 1, 1, Date)) is Date  # type: ignore

    # Now
    assert datetime.date.today() == date_now()  # type: ignore
    assert datetime.date.today() == date_now(None)  # type: ignore
    assert datetime.datetime.now(UTC).date() == date_now(UTC)  # type: ignore
    assert datetime.datetime.now(tz).date() == date_now(tz)  # type: ignore

    print("Passed: date_generate")

    del datetime, Date


def _test_date_type_check() -> None:
    import datetime

    class CustomDate(datetime.date):
        pass

    date = datetime.date.today()
    assert is_date(date)  # type: ignore
    assert is_date_exact(date)  # type: ignore

    date = CustomDate(1, 1, 1)
    assert is_date(date)  # type: ignore
    assert not is_date_exact(date)  # type: ignore

    print("Passed: date_type_check")

    del CustomDate, datetime


def _test_date_conversion() -> None:
    import datetime
    from pendulum import Date

    date = datetime.date(2021, 1, 2)
    pdate = Date(2021, 1, 2)
    dt = datetime.datetime(2021, 1, 2)

    _tm = date_to_tm(date)  # type: ignore
    assert tuple(date.timetuple()) == (
        _tm.tm_year,
        _tm.tm_mon,
        _tm.tm_mday,
        _tm.tm_hour,
        _tm.tm_min,
        _tm.tm_sec,
        _tm.tm_wday,
        _tm.tm_yday,
        _tm.tm_isdst,
    )
    assert "01/02/2021" == date_strformat(date, "%m/%d/%Y")  # type: ignore
    assert "2021-01-02" == date_isoformat(date)  # type: ignore
    assert date.toordinal() == date_to_ord(date)  # type: ignore
    assert (date.toordinal() - EPOCH_DAY) * 86400 == date_to_sec(date)  # type: ignore
    assert (date.toordinal() - EPOCH_DAY) * 86400_000000 == date_to_us(date)  # type: ignore

    assert date == date_fr_date(pdate)  # type: ignore
    assert type(date_fr_date(pdate)) is datetime.date  # type: ignore
    assert type(date_fr_date(pdate, None)) is datetime.date  # type: ignore
    assert type(date_fr_date(pdate, datetime.date)) is datetime.date  # type: ignore
    assert type(date_fr_date(pdate, Date)) is Date  # type: ignore
    assert type(date_fr_date(date)) is datetime.date  # type: ignore
    assert type(date_fr_date(date, None)) is datetime.date  # type: ignore
    assert type(date_fr_date(date, datetime.date)) is datetime.date  # type: ignore
    assert type(date_fr_date(date, Date)) is Date  # type: ignore

    assert date == date_fr_dt(dt)  # type: ignore
    assert type(date_fr_dt(dt)) is datetime.date  # type: ignore
    assert type(date_fr_dt(dt, None)) is datetime.date  # type: ignore
    assert type(date_fr_dt(dt, datetime.date)) is datetime.date  # type: ignore
    assert type(date_fr_dt(dt, Date)) is Date  # type: ignore

    tmp = date_fr_ord(date.toordinal())  # type: ignore
    assert date == tmp and type(tmp) is datetime.date

    tmp = date_fr_sec((date.toordinal() - EPOCH_DAY) * 86400)  # type: ignore
    assert date == tmp and type(tmp) is datetime.date

    tmp = date_fr_us((date.toordinal() - EPOCH_DAY) * 86400_000000)  # type: ignore
    assert date == tmp and type(tmp) is datetime.date

    tmp = date_fr_ts(dt.timestamp())  # type: ignore
    assert date == tmp and type(tmp) is datetime.date

    print("Passed: date_conversion")

    del datetime, Date


# datetime.datetime
def _test_dt_generate() -> None:
    import datetime
    from pandas import Timestamp
    from pendulum import DateTime

    tz = datetime.timezone(datetime.timedelta(hours=23, minutes=59))

    # New
    assert datetime.datetime(1, 1, 1, 0, 0, 0, 0) == dt_new()  # type: ignore
    assert datetime.datetime(1, 1, 1, 0, 0, 0, 0) == dt_new(1)  # type: ignore
    assert datetime.datetime(1, 1, 1, 0, 0, 0, 0) == dt_new(1, 1)  # type: ignore
    assert datetime.datetime(1, 1, 1, 0, 0, 0, 0) == dt_new(1, 1, 1)  # type: ignore
    assert datetime.datetime(1, 1, 1, 1, 0, 0, 0) == dt_new(1, 1, 1, 1)  # type: ignore
    assert datetime.datetime(1, 1, 1, 1, 1, 0, 0) == dt_new(1, 1, 1, 1, 1)  # type: ignore
    assert datetime.datetime(1, 1, 1, 1, 1, 1, 0) == dt_new(1, 1, 1, 1, 1, 1)  # type: ignore
    assert datetime.datetime(1, 1, 1, 1, 1, 1, 1) == dt_new(1, 1, 1, 1, 1, 1, 1)  # type: ignore
    assert datetime.datetime(1, 1, 1, 1, 1, 1, 1, tz) == dt_new(1, 1, 1, 1, 1, 1, 1, tz)  # type: ignore
    assert type(dt_new(1, 1, 1, 1, 1, 1, 1, tz, 0)) is datetime.datetime  # type: ignore
    assert type(dt_new(1, 1, 1, 1, 1, 1, 1, tz, 0, None)) is datetime.datetime  # type: ignore
    assert type(dt_new(1, 1, 1, 1, 1, 1, 1, tz, 0, datetime.datetime)) is datetime.datetime  # type: ignore
    assert type(dt_new(1, 1, 1, 1, 1, 1, 1, tz, 0, Timestamp)) is Timestamp  # type: ignore
    assert type(dt_new(1, 1, 1, 1, 1, 1, 1, tz, 0, DateTime)) is DateTime  # type: ignore

    # Now
    for dt_n, dt_c in (
        (datetime.datetime.now(), dt_now()),  # type: ignore
        (datetime.datetime.now(), dt_now(None)),  # type: ignore
        (datetime.datetime.now(UTC), dt_now(UTC)),  # type: ignore
        (datetime.datetime.now(tz), dt_now(tz)),  # type: ignore
    ):
        assert (
            (dt_n.year == dt_c.year)
            and (dt_n.month == dt_c.month)
            and (dt_n.day == dt_c.day)
            and (dt_n.hour == dt_c.hour)
            and (dt_n.minute == dt_c.minute)
            and (dt_n.second == dt_c.second)
            and (-1000 < dt_n.microsecond - dt_c.microsecond < 1000)
            and (dt_n.tzinfo == dt_c.tzinfo)
        ), f"{dt_n} != {dt_c}"

    print("Passed: dt_generate")

    del datetime, Timestamp, DateTime


def _test_dt_type_check() -> None:
    import datetime

    class CustomDateTime(datetime.datetime):
        pass

    dt = datetime.datetime.now()
    assert is_dt(dt)  # type: ignore
    assert is_dt_exact(dt)  # type: ignore

    dt = CustomDateTime(1, 1, 1)
    assert is_dt(dt)  # type: ignore
    assert not is_dt_exact(dt)  # type: ignore

    print("Passed: dt_type_check")

    del CustomDateTime, datetime


def _test_dt_tzinfo() -> None:
    import datetime

    dt = datetime.datetime(2021, 1, 2, 3, 4, 5, 6)
    tz = datetime.timezone(datetime.timedelta(hours=1, minutes=1))
    dt_tz1 = datetime.datetime(2021, 1, 2, 3, 4, 5, 6, tz)
    dt_tz2 = datetime.datetime(2021, 1, 2, 3, 4, 5, 6, zoneinfo.ZoneInfo("CET"))

    for t in (dt, dt_tz1, dt_tz2):
        assert t.tzname() == dt_tzname(t)  # type: ignore
        assert t.dst() == dt_dst(t)  # type: ignore
        assert t.utcoffset() == dt_utcoffset(t)  # type: ignore

    print("Passed: dt_tzinfo")

    del datetime


def _test_dt_conversion() -> None:
    import datetime
    from pandas import Timestamp

    dt = datetime.datetime(2021, 1, 2, 3, 4, 5, 6)
    tz1 = datetime.timezone(datetime.timedelta(hours=1, minutes=1))
    dt_tz1 = datetime.datetime(2021, 1, 2, 3, 4, 5, 6, tz1)
    tz2 = datetime.timezone(datetime.timedelta(hours=23, minutes=59))
    dt_tz2 = datetime.datetime(2021, 1, 2, 3, 4, 5, 6, tz2)
    tz3 = datetime.timezone(datetime.timedelta(hours=-23, minutes=-59))
    dt_tz3 = datetime.datetime(2021, 1, 2, 3, 4, 5, 6, tz3)
    dt_tz4 = datetime.datetime(2021, 1, 2, 3, 4, 5, 6, zoneinfo.ZoneInfo("CET"))

    for d in (dt, dt_tz1, dt_tz2, dt_tz3, dt_tz4):
        _tm = dt_to_tm(d, False)  # type: ignore
        assert tuple(d.timetuple()) == (
            _tm.tm_year,
            _tm.tm_mon,
            _tm.tm_mday,
            _tm.tm_hour,
            _tm.tm_min,
            _tm.tm_sec,
            _tm.tm_wday,
            _tm.tm_yday,
            _tm.tm_isdst,
        )
        _tm = dt_to_tm(d, True)  # type: ignore
        assert tuple(d.utctimetuple()) == (
            _tm.tm_year,
            _tm.tm_mon,
            _tm.tm_mday,
            _tm.tm_hour,
            _tm.tm_min,
            _tm.tm_sec,
            _tm.tm_wday,
            _tm.tm_yday,
            _tm.tm_isdst,
        )

    assert "01/02/2021 000006.05-04-03" == dt_strformat(dt, "%m/%d/%Y %f.%S-%M-%H")  # type: ignore
    assert "01/02/2021 000006.05-04-03+0101" == dt_strformat(dt_tz1, "%m/%d/%Y %f.%S-%M-%H%z")  # type: ignore
    assert "01/02/2021 000006.05-04-03UTC+01:01" == dt_strformat(dt_tz1, "%m/%d/%Y %f.%S-%M-%H%Z")  # type: ignore
    assert "2021-01-02T03:04:05.000006" == dt_isoformat(dt_tz1, "T", False)  # type: ignore
    assert "2021-01-02T03:04:05" == dt_isoformat(dt_tz1.replace(microsecond=0), "T", False)  # type: ignore
    assert "2021-01-02 03:04:05.000006+0101" == dt_isoformat(dt_tz1, " ", True)  # type: ignore
    assert "2021-01-02 03:04:05+0101" == dt_isoformat(dt_tz1.replace(microsecond=0), " ", True)  # type: ignore
    assert dt.toordinal() == dt_to_ord(dt)  # type: ignore
    assert dt_tz2.toordinal() == dt_to_ord(dt_tz2, False)  # type: ignore
    assert dt_tz2.toordinal() - 1 == dt_to_ord(dt_tz2, True)  # type: ignore
    assert dt_tz3.toordinal() == dt_to_ord(dt_tz3, False)  # type: ignore
    assert dt_tz3.toordinal() + 1 == dt_to_ord(dt_tz3, True)  # type: ignore
    secs = (
        (dt.toordinal() - EPOCH_DAY) * 86400
        + dt.hour * 3600
        + dt.minute * 60
        + dt.second
        + dt.microsecond / 1_000_000
    )
    assert secs == dt_to_sec(dt)  # type: ignore
    assert secs == dt_to_sec(dt_tz1, False)  # type: ignore
    offset = datetime.timedelta(hours=1, minutes=1).total_seconds()
    assert secs - offset == dt_to_sec(dt_tz1, True)  # type: ignore
    us = int(secs * 1_000_000)
    assert us == dt_to_us(dt)  # type: ignore
    assert us == dt_to_us(dt_tz1, False)  # type: ignore
    assert us - (offset * 1_000_000) == dt_to_us(dt_tz1, True)  # type: ignore
    for t in (dt, dt_tz1, dt_tz2, dt_tz3, dt_tz4):
        assert t.timestamp() == dt_to_ts(t)  # type: ignore

    date = datetime.date(2021, 1, 2)
    time1 = datetime.time(3, 4, 5, 6)
    time2 = datetime.time(3, 4, 5, 6, tz1)
    assert dt == dt_combine(date, time1)  # type: ignore
    assert dt_tz1 == dt_combine(date, time2)  # type: ignore
    assert datetime.datetime(2021, 1, 2) == dt_combine(date, None)  # type: ignore
    tmp = datetime.datetime.now()
    tmp1 = tmp.replace(hour=3, minute=4, second=5, microsecond=6)
    assert tmp1 == dt_combine(None, time1)  # type: ignore
    tmp2 = tmp1.replace(tzinfo=tz1)
    assert tmp2 == dt_combine(None, time2)  # type: ignore
    tmp3 = tmp.replace(hour=0, minute=0, second=0, microsecond=0)
    assert tmp3 == dt_combine()  # type: ignore

    assert datetime.datetime(2021, 1, 2) == dt_fr_date(date)  # type: ignore
    assert datetime.datetime(2021, 1, 2, tzinfo=tz1) == dt_fr_date(date, tz1)  # type: ignore
    assert type(dt_fr_dt(Timestamp(dt))) is datetime.datetime  # type: ignore
    assert type(dt_fr_dt(Timestamp(dt), None)) is datetime.datetime  # type: ignore
    assert type(dt_fr_dt(Timestamp(dt), datetime.datetime)) is datetime.datetime  # type: ignore
    assert type(dt_fr_dt(Timestamp(dt), Timestamp)) is Timestamp  # type: ignore
    assert type(dt_fr_dt(dt)) is datetime.datetime  # type: ignore
    assert type(dt_fr_dt(dt, None)) is datetime.datetime  # type: ignore
    assert type(dt_fr_dt(dt, datetime.datetime)) is datetime.datetime  # type: ignore
    assert type(dt_fr_dt(dt, Timestamp)) is Timestamp  # type: ignore
    assert dt == dt_fr_dt(Timestamp(dt))  # type: ignore
    assert dt_tz1 == dt_fr_dt(Timestamp(dt_tz1))  # type: ignore
    assert datetime.datetime(2021, 1, 2) == dt_fr_ord(dt.toordinal())  # type: ignore
    assert datetime.datetime(2021, 1, 2) == dt_fr_ord(dt_to_ord(dt_tz2, False))  # type: ignore
    assert datetime.datetime(2021, 1, 1) == dt_fr_ord(dt_to_ord(dt_tz2, True))  # type: ignore
    assert datetime.datetime(2021, 1, 2) == dt_fr_ord(dt_to_ord(dt_tz3, False))  # type: ignore
    assert datetime.datetime(2021, 1, 3) == dt_fr_ord(dt_to_ord(dt_tz3, True))  # type: ignore
    assert dt == dt_fr_sec(dt_to_sec(dt))  # type: ignore
    assert dt_tz1 == dt_fr_sec(dt_to_sec(dt_tz1, False), tz1)  # type: ignore
    assert dt == dt_fr_us(dt_to_us(dt))  # type: ignore
    assert dt_tz1 == dt_fr_us(dt_to_us(dt_tz1, False), tz1)  # type: ignore

    dt = datetime.datetime(2021, 1, 2, 3, 4, 5, 6)
    tz1 = datetime.timezone(datetime.timedelta(hours=1, minutes=1))
    tz2 = datetime.timezone(datetime.timedelta(hours=23, minutes=59))
    tz3 = datetime.timezone(datetime.timedelta(hours=-23, minutes=-59))
    tz4 = zoneinfo.ZoneInfo("CET")
    for tz in (None, tz1, tz2, tz3, tz4):
        dt_ = dt.replace(tzinfo=tz1)
        ts = dt_.timestamp()
        assert datetime.datetime.fromtimestamp(ts, tz) == dt_fr_ts(ts, tz)  # type: ignore

    print("Passed: dt_conversion")

    del datetime, Timestamp


def _test_dt_mainipulate() -> None:
    import datetime

    dt = datetime.datetime(2021, 1, 2, 3, 4, 5, 6)
    tz1 = datetime.timezone(datetime.timedelta(hours=1, minutes=1))
    tz2 = datetime.timezone(datetime.timedelta(hours=23, minutes=59))
    tz3 = datetime.timezone(datetime.timedelta(hours=-23, minutes=-59))
    tz4 = zoneinfo.ZoneInfo("CET")

    for tz in (None, tz1, tz2, tz3, tz4):
        assert dt.replace(tzinfo=tz) == dt_replace_tz(dt, tz)  # type: ignore
    assert 1 == dt_replace_fold(dt.replace(tzinfo=tz1, fold=0), 1).fold  # type: ignore

    print("Passed: dt_manipulate")

    del datetime


def _test_dt_arithmetic() -> None:
    import datetime

    dt = datetime.datetime(2021, 1, 2, 3, 4, 5, 6)
    td1 = datetime.timedelta(1, 1, 1)
    assert dt_add(dt, 1, 1, 1) == dt + td1  # type: ignore

    td2 = datetime.timedelta(1, 86400, 1)
    assert dt_add(dt, 1, 86400, 1) == dt + td2  # type: ignore

    td3 = datetime.timedelta(1, 86399, 1)
    assert dt_add(dt, 1, 86399, 1) == dt + td3  # type: ignore

    td4 = datetime.timedelta(-1, -1, -1)
    assert dt_add(dt, -1, -1, -1) == dt + td4  # type: ignore

    td5 = datetime.timedelta(-1, -86400, -1)
    assert dt_add(dt, -1, -86400, -1) == dt + td5  # type: ignore

    td6 = datetime.timedelta(-1, -86399, -1)
    assert dt_add(dt, -1, -86399, -1) == dt + td6  # type: ignore

    td7 = datetime.timedelta(1, 60, 100000)
    assert dt_add(dt, 1, 60, 100000) == dt + td7  # type: ignore

    td8 = datetime.timedelta(-1, -60, -100000)
    assert dt_add(dt, -1, -60, -100000) == dt + td8  # type: ignore

    print("Passed: date_arithmetic")

    del datetime


def _test_dt_normalize_tz() -> None:
    import datetime, pendulum
    from zoneinfo import ZoneInfo

    test_pairs = [
        # New York fall-back (1:30 happens twice)
        datetime.datetime(
            2025, 11, 2, 1, 30, tzinfo=ZoneInfo("America/New_York"), fold=0
        ),
        datetime.datetime(
            2025, 11, 2, 1, 30, tzinfo=ZoneInfo("America/New_York"), fold=1
        ),
        # Berlin fall-back (CET/CEST)
        datetime.datetime(2025, 10, 26, 2, 30, tzinfo=ZoneInfo("CET"), fold=0),
        datetime.datetime(2025, 10, 26, 2, 30, tzinfo=ZoneInfo("CET"), fold=1),
        # New York spring-forward (2:30 never exists)
        datetime.datetime(
            2025, 3, 9, 2, 30, tzinfo=ZoneInfo("America/New_York"), fold=0
        ),
        datetime.datetime(
            2025, 3, 9, 2, 30, tzinfo=ZoneInfo("America/New_York"), fold=1
        ),
        # Paris spring-forward gap
        datetime.datetime(2025, 3, 30, 2, 30, tzinfo=ZoneInfo("Europe/Paris"), fold=0),
        datetime.datetime(2025, 3, 30, 2, 30, tzinfo=ZoneInfo("Europe/Paris"), fold=1),
        # Lord Howe (30-minute DST change) ambiguous
        datetime.datetime(
            2024, 4, 7, 1, 45, tzinfo=ZoneInfo("Australia/Lord_Howe"), fold=0
        ),
        datetime.datetime(
            2024, 4, 7, 1, 45, tzinfo=ZoneInfo("Australia/Lord_Howe"), fold=1
        ),
        # Lord Howe (30-minute DST change) non-existent
        datetime.datetime(
            2024, 10, 6, 2, 15, tzinfo=ZoneInfo("Australia/Lord_Howe"), fold=0
        ),
        datetime.datetime(
            2024, 10, 6, 2, 15, tzinfo=ZoneInfo("Australia/Lord_Howe"), fold=1
        ),
        # Odd offsets & negative DST
        datetime.datetime(
            2025, 1, 15, 12, 34, 56, tzinfo=ZoneInfo("Asia/Kathmandu"), fold=0
        ),
        datetime.datetime(
            2025, 1, 15, 12, 34, 56, tzinfo=ZoneInfo("Asia/Kathmandu"), fold=1
        ),
        # Dublin’s historical “negative DST” periods
        datetime.datetime(
            1971, 10, 31, 1, 30, tzinfo=ZoneInfo("Europe/Dublin"), fold=0
        ),
        datetime.datetime(
            1971, 10, 31, 1, 30, tzinfo=ZoneInfo("Europe/Dublin"), fold=1
        ),
        # Samoa skipping a day (dateline move)
        datetime.datetime(2011, 12, 29, tzinfo=ZoneInfo("Pacific/Apia"), fold=0),
        datetime.datetime(2011, 12, 29, tzinfo=ZoneInfo("Pacific/Apia"), fold=1),
        datetime.datetime(2011, 12, 30, tzinfo=ZoneInfo("Pacific/Apia"), fold=0),
        datetime.datetime(2011, 12, 30, tzinfo=ZoneInfo("Pacific/Apia"), fold=1),
        # Aware with tzinfo refusing utcoffset at wall time
        datetime.datetime(
            2025, 3, 9, 2, 30, tzinfo=ZoneInfo("America/New_York"), fold=0
        ),
        datetime.datetime(
            2025, 3, 9, 2, 30, tzinfo=ZoneInfo("America/New_York"), fold=1
        ),
    ]

    for dt in test_pairs:
        m_dt = dt_normalize_tz(dt)  # type: ignore
        p_dt = pendulum.datetime(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tz=dt.tzinfo,
            fold=dt.fold,
        )
        assert (
            m_dt.year == p_dt.year
            and m_dt.month == p_dt.month
            and m_dt.day == p_dt.day
            and m_dt.hour == p_dt.hour
            and m_dt.minute == p_dt.minute
            and m_dt.second == p_dt.second
            and m_dt.microsecond == p_dt.microsecond
            and m_dt.fold == p_dt.fold
        ), f"Failed: dt_normalize_tz({dt}) != pendulum result {p_dt}"

    print("Passed: dt_normalize_tz")

    del datetime, pendulum, ZoneInfo


# datetime.time
def _test_time_generate() -> None:
    import datetime
    from pendulum import Time

    tz = datetime.timezone(datetime.timedelta(hours=23, minutes=59))

    # New
    assert datetime.time(0, 0, 0, 0) == time_new()  # type: ignore
    assert datetime.time(0, 0, 0, 0) == time_new(0)  # type: ignore
    assert datetime.time(0, 0, 0, 0) == time_new(0, 0)  # type: ignore
    assert datetime.time(0, 0, 0, 0) == time_new(0, 0, 0)  # type: ignore
    assert datetime.time(0, 0, 0, 0) == time_new(0, 0, 0, 0)  # type: ignore
    assert datetime.time(1, 0, 0, 0) == time_new(1)  # type: ignore
    assert datetime.time(1, 1, 0, 0) == time_new(1, 1)  # type: ignore
    assert datetime.time(1, 1, 1, 0) == time_new(1, 1, 1)  # type: ignore
    assert datetime.time(1, 1, 1, 1) == time_new(1, 1, 1, 1)  # type: ignore
    assert datetime.time(1, 1, 1, 1, tz) == time_new(1, 1, 1, 1, tz)  # type: ignore
    assert type(time_new(1, 1, 1, 1, tz, 0)) is datetime.time  # type: ignore
    assert type(time_new(1, 1, 1, 1, tz, 0, None)) is datetime.time  # type: ignore
    assert type(time_new(1, 1, 1, 1, tz, 0, datetime.time)) is datetime.time  # type: ignore
    assert type(time_new(1, 1, 1, 1, tz, 0, Time)) is Time  # type: ignore

    # Now
    for t_n, t_c in (
        (datetime.datetime.now().time(), time_now()),  # type: ignore
        (datetime.datetime.now().time(), time_now(None)),  # type: ignore
        (datetime.datetime.now(UTC).timetz(), time_now(UTC)),  # type: ignore
        (datetime.datetime.now(tz).timetz(), time_now(tz)),  # type: ignore
    ):
        assert (
            (t_n.hour == t_c.hour)
            and (t_n.minute == t_c.minute)
            and (t_n.second == t_c.second)
            and (-1000 < t_n.microsecond - t_c.microsecond < 1000)
            and (t_n.tzinfo == t_c.tzinfo)
        ), f"{t_n} != {t_c}"

    print("Passed: time_generate")

    del datetime, Time


def _test_time_type_check() -> None:
    import datetime

    class CustomTime(datetime.time):
        pass

    time = datetime.time(1, 1, 1)
    assert is_time(time)  # type: ignore
    assert is_time_exact(time)  # type: ignore

    time = CustomTime(1, 1, 1)
    assert is_time(time)  # type: ignore
    assert not is_time_exact(time)  # type: ignore

    print("Passed: time_type_check")

    del CustomTime, datetime


def _test_time_conversion() -> None:
    import datetime
    from pendulum import Time

    tz1 = datetime.timezone(datetime.timedelta(hours=1, minutes=1))
    t1 = datetime.time(3, 4, 5, 6)
    t_tz1 = datetime.time(3, 4, 5, 6, tz1)
    pt = Time(3, 4, 5, 6)
    pt_tz1 = Time(3, 4, 5, 6, tz1)
    dt = datetime.datetime(1970, 1, 1, 3, 4, 5, 6)
    dt_tz1 = datetime.datetime(1970, 1, 1, 3, 4, 5, 6, tz1)

    assert "03:04:05.000006" == time_isoformat(t_tz1, False)  # type: ignore
    assert "03:04:05.000006+0101" == time_isoformat(t_tz1, True)  # type: ignore
    assert "03:04:05" == time_isoformat(t_tz1.replace(microsecond=0), False)  # type: ignore
    assert "03:04:05+0101" == time_isoformat(t_tz1.replace(microsecond=0), True)  # type: ignore
    secs = t1.hour * 3600 + t1.minute * 60 + t1.second + t1.microsecond / 1_000_000
    assert secs == time_to_sec(t1)  # type: ignore
    assert secs == time_to_sec(t_tz1)  # type: ignore
    us = int(secs * 1_000_000)
    assert us == time_to_us(t1)  # type: ignore
    assert us == time_to_us(t_tz1)  # type: ignore

    assert t1 == time_fr_time(pt)  # type: ignore
    assert t_tz1 == time_fr_time(pt_tz1)  # type: ignore
    assert type(time_fr_time(pt)) is datetime.time  # type: ignore
    assert type(time_fr_time(pt, None)) is datetime.time  # type: ignore
    assert type(time_fr_time(pt, datetime.time)) is datetime.time  # type: ignore
    assert type(time_fr_time(pt, Time)) is Time  # type: ignore
    assert type(time_fr_time(t1)) is datetime.time  # type: ignore
    assert type(time_fr_time(t1, None)) is datetime.time  # type: ignore
    assert type(time_fr_time(t1, datetime.time)) is datetime.time  # type: ignore
    assert type(time_fr_time(t1, Time)) is Time  # type: ignore

    assert t1 == time_fr_dt(dt)  # type: ignore
    assert t_tz1 == time_fr_dt(dt_tz1)  # type: ignore
    assert type(time_fr_dt(dt)) is datetime.time  # type: ignore
    assert type(time_fr_dt(dt, None)) is datetime.time  # type: ignore
    assert type(time_fr_dt(dt, datetime.time)) is datetime.time  # type: ignore
    assert type(time_fr_dt(dt, Time)) is Time  # type: ignore

    assert t1 == time_fr_sec(time_to_sec(t1))  # type: ignore
    assert t_tz1 == time_fr_sec(time_to_sec(t1), tz1)  # type: ignore
    assert t1 == time_fr_us(time_to_us(t1))  # type: ignore
    assert t_tz1 == time_fr_us(time_to_us(t1), tz1)  # type: ignore

    print("Passed: time_conversion")

    del datetime, Time


# datetime.timedelta
def _test_timedelta_generate() -> None:
    import datetime

    class CustomTD(datetime.timedelta):
        pass

    # New
    assert datetime.timedelta(0, 0, 0) == td_new()  # type: ignore
    assert datetime.timedelta(0, 0, 0) == td_new(0)  # type: ignore
    assert datetime.timedelta(0, 0, 0) == td_new(0, 0)  # type: ignore
    assert datetime.timedelta(0, 0, 0) == td_new(0, 0, 0)  # type: ignore
    assert datetime.timedelta(1, 0, 0) == td_new(1)  # type: ignore
    assert datetime.timedelta(1, 1, 0) == td_new(1, 1)  # type: ignore
    assert datetime.timedelta(1, 1, 1) == td_new(1, 1, 1)  # type: ignore
    assert datetime.timedelta(-1, 0, 0) == td_new(-1)  # type: ignore
    assert datetime.timedelta(-1, -1, 0) == td_new(-1, -1)  # type: ignore
    assert datetime.timedelta(-1, -1, -1) == td_new(-1, -1, -1)  # type: ignore
    assert type(td_new(-1, -1, -1)) is datetime.timedelta  # type: ignore
    assert type(td_new(-1, -1, -1, None)) is datetime.timedelta  # type: ignore
    assert type(td_new(-1, -1, -1, datetime.timedelta)) is datetime.timedelta  # type: ignore
    assert type(td_new(-1, -1, -1, CustomTD)) is CustomTD  # type: ignore

    print("Passed: timedelta_generate")

    del datetime, CustomTD


def _test_timedelta_type_check() -> None:
    import datetime

    class CustomTD(datetime.timedelta):
        pass

    td = datetime.timedelta(1, 1, 1)
    assert is_td(td)  # type: ignore
    assert is_td_exact(td)  # type: ignore

    td = CustomTD(1, 1, 1)
    assert is_td(td)  # type: ignore
    assert not is_td_exact(td)  # type: ignore

    print("Passed: timedelta_type_chech")

    del CustomTD, datetime


def _test_timedelta_conversion() -> None:
    import datetime

    assert "00:00:01" == td_isoformat(datetime.timedelta(0, 1))  # type: ignore
    assert "00:01:01" == td_isoformat(datetime.timedelta(0, 1, minutes=1))  # type: ignore
    assert "24:01:01" == td_isoformat(datetime.timedelta(1, 1, minutes=1))  # type: ignore
    assert "24:01:01.001000" == td_isoformat(datetime.timedelta(1, 1, 0, minutes=1, milliseconds=1))  # type: ignore
    assert "24:01:01.000001" == td_isoformat(datetime.timedelta(1, 1, 1, minutes=1))  # type: ignore
    assert "24:01:01.001001" == td_isoformat(datetime.timedelta(1, 1, 1, minutes=1, milliseconds=1))  # type: ignore
    assert "-00:00:01" == td_isoformat(datetime.timedelta(0, -1))  # type: ignore
    assert "-00:01:01" == td_isoformat(datetime.timedelta(0, -1, minutes=-1))  # type: ignore
    assert "-24:01:01" == td_isoformat(datetime.timedelta(-1, -1, minutes=-1))  # type: ignore
    assert "-24:01:01.001000" == td_isoformat(datetime.timedelta(-1, -1, 0, minutes=-1, milliseconds=-1))  # type: ignore
    assert "-24:01:01.000001" == td_isoformat(datetime.timedelta(-1, -1, -1, minutes=-1))  # type: ignore
    assert "-24:01:01.001001" == td_isoformat(datetime.timedelta(-1, -1, -1, minutes=-1, milliseconds=-1))  # type: ignore

    for h in range(-23, 24):
        for m in range(-59, 60):
            td = datetime.timedelta(hours=h, minutes=m)
            dt_str = str(datetime.datetime.now(datetime.timezone(td)))
            tz_str = dt_str[len(dt_str) - 6 :]
            with cython.wraparound(True):
                tz_str = tz_str[:-3] + tz_str[-2:]
            assert tz_str == td_utcformat(td)  # type: ignore

    td = datetime.timedelta(1, 1, 1)
    secs = td.total_seconds()
    assert secs == td_to_sec(td)  # type: ignore
    assert int(secs * 1_000_000) == td_to_us(td)  # type: ignore
    td = datetime.timedelta(-1, -1, -1)
    secs = td.total_seconds()
    assert secs == td_to_sec(td)  # type: ignore
    assert int(secs * 1_000_000) == td_to_us(td)  # type: ignore

    class CustomTD(datetime.timedelta):
        pass

    ctd = CustomTD(-1, -1, -1)
    assert td == td_fr_td(ctd)  # type: ignore
    assert type(td_fr_td(ctd)) is datetime.timedelta  # type: ignore
    assert type(td_fr_td(ctd, None)) is datetime.timedelta  # type: ignore
    assert type(td_fr_td(ctd, datetime.timedelta)) is datetime.timedelta  # type: ignore
    assert type(td_fr_td(ctd, CustomTD)) is CustomTD  # type: ignore
    assert type(td_fr_td(td)) is datetime.timedelta  # type: ignore
    assert type(td_fr_td(td, None)) is datetime.timedelta  # type: ignore
    assert type(td_fr_td(td, datetime.timedelta)) is datetime.timedelta  # type: ignore
    assert type(td_fr_td(td, CustomTD)) is CustomTD  # type: ignore
    assert td == td_fr_sec(td_to_sec(td))  # type: ignore
    assert td == td_fr_us(td_to_us(td))  # type: ignore

    print("Passed: timedelta_conversion")

    del CustomTD, datetime


# datetime.tzinfo
def _test_tzinfo_generate() -> None:
    import datetime, time
    from babel.dates import LOCALTZ

    # New
    assert datetime.timezone.utc == tz_new()  # type: ignore
    assert datetime.timezone(datetime.timedelta(hours=1, minutes=1)) == tz_new(1, 1)  # type: ignore
    assert datetime.timezone(datetime.timedelta(hours=-1, minutes=-1)) == tz_new(-1, -1)  # type: ignore
    assert datetime.timezone(datetime.timedelta(hours=23, minutes=59)) == tz_new(23, 59)  # type: ignore
    assert datetime.timezone(datetime.timedelta(hours=-23, minutes=-59)) == tz_new(-23, -59)  # type: ignore

    # Local
    assert tz_parse(LOCALTZ) == tz_local()  # type: ignore

    print("Passed: tzinfo_generate")

    del datetime, time, LOCALTZ


def _test_tzinfo_type_check() -> None:
    import datetime

    tz = UTC
    assert is_tz(tz)  # type: ignore
    assert not is_tz_exact(tz)  # type: ignore

    print("Passed: tzinfo_type_check")

    del datetime


def _test_tzinfo_access() -> None:
    import datetime

    dt = datetime.datetime.now()
    tz = dt.tzinfo
    assert None == tz_name(tz, dt)  # type: ignore
    assert None == tz_dst(tz, dt)  # type: ignore
    assert None == tz_utcoffset(tz, dt)  # type: ignore

    dt = datetime.datetime.now(UTC)
    tz = dt.tzinfo
    assert "UTC" == tz_name(tz, dt)  # type: ignore
    assert None == tz_dst(tz, dt)  # type: ignore
    assert datetime.timedelta() == tz_utcoffset(tz, dt)  # type: ignore

    dt = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
    tz = dt.tzinfo
    assert "CST" == tz_name(tz, dt)  # type: ignore
    assert datetime.timedelta() == tz_dst(tz, dt)  # type: ignore
    assert datetime.timedelta(hours=8) == tz_utcoffset(tz, dt)  # type: ignore

    dt = datetime.datetime.now()
    tz = datetime.timezone(datetime.timedelta(hours=23, minutes=59))
    assert "+2359" == tz_utcformat(tz, dt)  # type: ignore
    tz = datetime.timezone(datetime.timedelta(hours=1, minutes=1))
    assert "+0101" == tz_utcformat(tz, dt)  # type: ignore
    tz = datetime.timezone(datetime.timedelta(hours=-1, minutes=-1))
    assert "-0101" == tz_utcformat(tz, dt)  # type: ignore
    tz = datetime.timezone(datetime.timedelta(hours=-23, minutes=-59))
    assert "-2359" == tz_utcformat(tz, dt)  # type: ignore

    print("Passed: tzinfo_access")

    del datetime


# . numpy.share
def _test_numpy_share() -> None:
    import numpy as np

    units = ("Y", "M", "W", "D", "h", "m", "s", "ms", "us", "ns", "ps", "fs", "as")

    for unit in units:
        unit == nptime_unit_int2str(nptime_unit_str2int(unit))  # type: ignore

    for unit in units:
        arr = np.array([], dtype="datetime64[%s]" % unit)
        assert unit == nptime_unit_int2str(get_arr_nptime_unit(arr))  # type: ignore
        arr = np.array([1, 2, 3], dtype="datetime64[%s]" % unit)
        assert unit == nptime_unit_int2str(get_arr_nptime_unit(arr))  # type: ignore
        arr = np.array([], dtype="timedelta64[%s]" % unit)
        assert unit == nptime_unit_int2str(get_arr_nptime_unit(arr))  # type: ignore
        arr = np.array([1, 2, 3], dtype="timedelta64[%s]" % unit)
        assert unit == nptime_unit_int2str(get_arr_nptime_unit(arr))  # type: ignore

    print("Passed: numpy_share")

    del np


# . numpy.datetime64
def _test_datetime64_type_check() -> None:
    import numpy as np

    dt = np.datetime64("2021-01-02")
    assert is_dt64(dt)  # type: ignore
    assure_dt64(dt)  # type: ignore

    dt2 = 1
    assert not is_dt64(dt2)  # type: ignore
    try:
        assure_dt64(dt2)  # type: ignore
    except TypeError:
        pass
    else:
        raise AssertionError("Failed: datetime64_type_check")

    print("Passed: datetime64_type_check")

    del np


def _test_datetime64_conversion() -> None:
    import datetime, numpy as np

    units = ("Y", "M", "W", "D", "h", "m", "s", "ms", "us", "ns")
    for unit in units:
        for i in range(-500, 501):
            dt64 = np.datetime64(i, unit)
            us = dt64.astype("datetime64[us]").astype("int64")
            assert dt64_as_int64_us(dt64) == us  # type: ignore
            assert dt64_to_dt(dt64) == dt_fr_us(us)  # type: ignore

    print("Passed: datetime64_conversion")

    del datetime, np


# . numpy.timedelta64
def _test_timedelta64_type_check() -> None:
    import numpy as np

    td = np.timedelta64(1, "D")
    assert is_td64(td)  # type: ignore
    assure_td64(td)  # type: ignore

    td2 = 1
    assert not is_td64(td2)  # type: ignore
    try:
        assure_td64(td2)  # type: ignore
    except TypeError:
        pass
    else:
        raise AssertionError("Failed: timedelta64_type_check")

    print("Passed: timedelta64_type_check")

    del np


def _test_timedelta64_conversion() -> None:
    import datetime, numpy as np

    units = ("Y", "M", "W", "D", "h", "m", "s", "ms", "us", "ns")
    for unit in units:
        for i in range(-500, 501):
            td64 = np.timedelta64(i, unit)
            us = td64.astype("timedelta64[us]").astype("int64")
            assert td64_as_int64_us(td64) == us  # type: ignore
            assert td64_to_td(td64) == datetime.timedelta(microseconds=int(us))  # type: ignore

    print("Passed: timedelta64_conversion")

    del datetime, np


# . numpy.ndarray
def _test_ndarray_type_check() -> None:
    import numpy as np

    assert is_arr(np.array([1, 2, 3]))  # type: ignore
    assert is_arr(np.array([]))  # type: ignore
    assert is_arr("a") == False  # type: ignore

    print("Passed: ndarray_type_check")

    del np


# . numpy.ndarray - generate
def _test_ndarray_generate() -> None:
    import numpy as np

    arr1 = arr_zero_int64(5)  # type: ignore
    arr2 = np.array([0, 0, 0, 0, 0], dtype="int64")  # type: ignore
    assert np.equal(arr1, arr2).all()  # type: ignore

    arr1 = arr_fill_int64(1, 5)  # type: ignore
    arr2 = np.array([1, 1, 1, 1, 1], dtype="int64")  # type: ignore
    assert np.equal(arr1, arr2).all()  # type: ignore

    print("Passed: ndarray_generate")

    del np


# . numpy.ndarray[datetime64]
def _test_ndarray_dt64_type_check() -> None:
    import numpy as np

    assert is_dt64arr(np.array([1, 2, 3], dtype="datetime64[ns]"))  # type: ignore
    assert is_dt64arr(np.array([], dtype="datetime64[ns]"))  # type: ignore
    assert is_dt64arr(np.array([1, 2, 3], dtype="int64")) == False  # type: ignore
    assert is_dt64arr(np.array([], dtype="int64")) == False  # type: ignore

    print("Passed: ndarray_dt64_type_check")

    del np


def _test_ndarray_dt64_conversion() -> None:
    import numpy as np

    units = ("Y", "M", "W", "D", "h", "m", "s", "ms", "us", "ns")

    for my_unit in units:
        my_unit_int: cython.int = nptime_unit_str2int(my_unit)  # type: ignore
        arr = np.array([i for i in range(-1000, 1001)], dtype=f"datetime64[{my_unit}]")
        arr_i = arr.astype("int64")
        for to_unit in units:
            cmp = arr.astype(f"datetime64[{to_unit}]").astype("int64")
            val = dt64arr_as_int64(arr, to_unit)  # type: ignore
            assert np.equal(val, cmp).all()
            val = dt64arr_as_int64(arr, to_unit, my_unit_int)  # type: ignore
            assert np.equal(val, cmp).all()
            val = dt64arr_as_int64(arr_i, to_unit, my_unit_int)  # type: ignore
            assert np.equal(val, cmp).all()

    for my_unit in units:
        my_unit_int: cython.int = nptime_unit_str2int(my_unit)  # type: ignore
        arr = np.array([i for i in range(-1000, 1001)], dtype=f"datetime64[{my_unit}]")
        arr_i = arr.astype("int64")
        for to_unit in units:
            cmp = arr.astype(f"datetime64[{to_unit}]")
            val = dt64arr_as_unit(arr, to_unit)  # type: ignore
            assert np.equal(val, cmp).all()
            val = dt64arr_as_unit(arr, to_unit, my_unit_int)  # type: ignore
            assert np.equal(val, cmp).all()
            val = dt64arr_as_unit(arr_i, to_unit, my_unit_int)  # type: ignore
            assert np.equal(val, cmp).all()

    print("Passed: ndarray_dt64_conversion")

    del np


# . numpy.ndarray[timedelta64]
def _test_ndarray_td64_type_check() -> None:
    import numpy as np

    assert is_td64arr(np.array([1, 2, 3], dtype="timedelta64[ns]"))  # type: ignore
    assert is_td64arr(np.array([], dtype="timedelta64[ns]"))  # type: ignore
    assert is_td64arr(np.array([1, 2, 3], dtype="int64")) == False  # type: ignore
    assert is_td64arr(np.array([], dtype="int64")) == False  # type: ignore

    print("Passed: ndarray_td64_type_check")

    del np


def _test_ndarray_td64_conversion() -> None:
    import numpy as np

    units = ("Y", "M", "W", "D", "h", "m", "s", "ms", "us", "ns")

    for my_unit in units:
        arr = np.array([i for i in range(-500, 501)], dtype=f"timedelta64[{my_unit}]")
        cmp = arr.astype(f"timedelta64[us]")
        val = td64arr_as_int64_us(arr)  # type: ignore
        assert np.equal(val, cmp).all()

    print("Passed: ndarray_td64_conversion")

    del np


# . math
def _test_math() -> None:
    import math
    from decimal import (
        Decimal,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_HALF_DOWN,
        ROUND_CEILING,
        ROUND_FLOOR,
    )

    # Modulo
    test_cases = [
        (4, 2),
        (-9, 3),
        (9, -3),
        (-12, -4),
        (5, 2),  # normal positive remainder
        (-5, 2),  # negative numerator -> adjust
        (7, 4),  # remainder 3 < 4
        (-7, 4),  # remainder -3 -> adjust to 1
        (5, -2),  # remainder 1 -> adjust to -1
        (-5, -2),  # remainder -1 -> already same sign
        (7, -4),  # remainder 3 -> adjust to -1
        (-7, -4),  # remainder -3 -> already correct
        (5, 1),
        (-5, 1),
        (5, -1),
        (-5, -1),
        (0, 3),
        (0, -3),
        (0, 1),
        (0, -1),
        (7, 4),  # baseline 7 % 4 == 3
        (-7, 4),  # baseline -7 % 4 == 1
        (2**62, 3),  # positive large
        (-(2**62), 3),  # negative large
        (2**63 - 1, 7),  # max int64
        (-(2**63) + 1, 7),  # near min int64
        (2**62, -3),
        (-(2**62), -3),
    ]
    for num, factor in test_cases:
        res = math_mod(num, factor)  # type: ignore
        exp = num % factor
        assert res == exp, f"Failed: math_mod({num}, {factor}) = {res}, expected {exp}"

    # Round half to even / up / down
    test_cases = [
        # . Small magnitudes
        (4, 2),
        (-9, 3),
        (7, 4),
        (9, 5),
        (17, -10),
        (11, 4),
        (-11, 4),
        (23, -7),
        (5, 2),
        (15, 6),
        (25, 10),
        (35, 10),
        (-5, 2),
        (-15, 6),
        (-35, 10),
        (5, -2),
        (-5, -2),
        (35, -10),
        (1, 3),
        (2, 3),
        (-2, 3),
        (3, 2),
        (-3, 2),
        (3, -2),
        (-3, -2),
        (-8, -4),
        (0, 3),
        (0, -7),
        (7, 1),
        (-7, 1),
        (7, -1),
        (-7, -1),
        (14, 10),
        (16, 10),
        (-14, 10),
        (-16, 10),
        (11, 8),
        (13, 8),
        (-11, 8),
        (-13, 8),
        # . Large magnitudes
        (2**62, 3),
        (-(2**62), 3),
        (2**63 - 1, 7),
        (-(2**63) + 1, 7),
        (2**62, -3),
        (-(2**62), -3),
        (2**63 - 1, -7),
        (-(2**63) + 1, -7),
        (2**63 - 1, 2),
        (2**63 - 1, -2),
        (-(2**63) + 1, 2),
        (-(2**63) + 1, -2),
        (2**62, 10),
        (2**62 + 2, 10),
        (-(2**62), 10),
        (-(2**62) - 2, 10),
        (2**62, -10),
        (2**62 + 2, -10),
    ]
    for num, factor in test_cases:
        # half to even
        res = math_div_even(num, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(
            rounding=ROUND_HALF_EVEN
        )
        assert (
            res == exp
        ), f"Failed: math_div_even({num}, {factor}) = {res}, expected {exp}"
        # half to up
        res = math_div_up(num, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(rounding=ROUND_HALF_UP)
        assert (
            res == exp
        ), f"Failed: math_div_up({num}, {factor}) = {res}, expected {exp}"
        # half to down
        res = math_div_down(num, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(
            rounding=ROUND_HALF_DOWN
        )
        assert (
            res == exp
        ), f"Failed: math_div_down({num}, {factor}) = {res}, expected {exp}"

    # Ceil / Floor
    test_cases = [
        # 1) Exact division (r == 0)
        (4, 2),
        (-9, 3),
        (9, -3),
        (-12, -4),
        # 2) Positive divisor (mixed numerators)
        (7, 4),  # 1.75
        (11, 4),  # 2.75
        (-7, 4),  # -1.75
        (-11, 4),  # -2.75
        # 3) Negative divisor (mixed numerators)
        (7, -4),  # -1.75
        (11, -4),  # -2.75
        (-7, -4),  # 1.75
        (-11, -4),  # 2.75
        # 4) Fractions with |num| < |factor| (results in (-1, 0, 1) bands)
        (3, 5),
        (-3, 5),
        (3, -5),
        (-3, -5),
        (1, 3),
        (2, 3),
        (-1, 3),
        (-2, 3),
        # 5) Denominator ±1 (fast paths)
        (7, 1),
        (-7, 1),
        (7, -1),
        (-7, -1),
        # 6) Zero numerator
        (0, 3),
        (0, -3),
        (0, 1),
        (0, -1),
        # 7) Near “half-ish” examples (just below / just above halves)
        (14, 10),
        (16, 10),
        (-14, 10),
        (-16, 10),  # 1.4 / 1.6 / -1.4 / -1.6
        (11, 8),
        (13, 8),
        (-11, 8),
        (-13, 8),  # 1.375 / 1.625 / ...
        # 8) Sign-edge microcases around zero
        (1, -2),  # -0.5  -> floor=-1, ceil=0
        (-1, -2),  # 0.5   -> floor=0,  ceil=1
        (1, 2),  # 0.5   -> floor=0,  ceil=1
        (-1, 2),  # -0.5  -> floor=-1, ceil=0
        # 9) Large magnitudes within int64 (exercise remainder & sign at scale)
        (2**62, 3),
        (-(2**62), 3),
        (2**62, -3),
        (-(2**62), -3),
        (2**63 - 1, 7),
        (-(2**63) + 1, 7),
        (2**63 - 1, -7),
        (-(2**63) + 1, -7),
        # 10) Large cases where |num| < |factor| but huge num
        (2**62, 2**63 - 1),
        (-(2**62), 2**63 - 1),
        (2**62, -(2**63 - 1)),
        (-(2**62), -(2**63 - 1)),
    ]
    for num, factor in test_cases:
        res = math_div_ceil(num, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(rounding=ROUND_CEILING)
        assert (
            res == exp
        ), f"Failed: math_div_ceil({num}, {factor}) = {res}, expected {exp}"
        res = math_div_floor(num, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(rounding=ROUND_FLOOR)
        assert (
            res == exp
        ), f"Failed: math_div_floor({num}, {factor}) = {res}, expected {exp}"

    print("Passed: math")

    del (
        math,
        Decimal,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_HALF_DOWN,
        ROUND_CEILING,
        ROUND_FLOOR,
    )


def _test_ndarray_math() -> None:
    import numpy as np
    from decimal import (
        Decimal,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_HALF_DOWN,
        ROUND_CEILING,
        ROUND_FLOOR,
    )

    # Modulo
    test_cases = [
        (4, 2),
        (-9, 3),
        (9, -3),
        (-12, -4),
        (5, 2),  # normal positive remainder
        (-5, 2),  # negative numerator -> adjust
        (7, 4),  # remainder 3 < 4
        (-7, 4),  # remainder -3 -> adjust to 1
        (5, -2),  # remainder 1 -> adjust to -1
        (-5, -2),  # remainder -1 -> already same sign
        (7, -4),  # remainder 3 -> adjust to -1
        (-7, -4),  # remainder -3 -> already correct
        (5, 1),
        (-5, 1),
        (5, -1),
        (-5, -1),
        (0, 3),
        (0, -3),
        (0, 1),
        (0, -1),
        (7, 4),  # baseline 7 % 4 == 3
        (-7, 4),  # baseline -7 % 4 == 1
        (2**62, 3),  # positive large
        (-(2**62), 3),  # negative large
        (2**63 - 1, 7),  # max int64
        (-(2**63) + 1, 7),  # near min int64
        (2**62, -3),
        (-(2**62), -3),
    ]
    for num, factor in test_cases:
        arr = np.array([num], dtype="int64")
        res = arr_mod(arr, factor)  # type: ignore
        exp = arr % factor
        assert np.equal(res, exp).all()  # type: ignore

    # Round half to even / up / down
    test_cases = [
        # . Small magnitudes
        (4, 2),
        (-9, 3),
        (7, 4),
        (9, 5),
        (17, -10),
        (11, 4),
        (-11, 4),
        (23, -7),
        (5, 2),
        (15, 6),
        (25, 10),
        (35, 10),
        (-5, 2),
        (-15, 6),
        (-35, 10),
        (5, -2),
        (-5, -2),
        (35, -10),
        (1, 3),
        (2, 3),
        (-2, 3),
        (3, 2),
        (-3, 2),
        (3, -2),
        (-3, -2),
        (-8, -4),
        (0, 3),
        (0, -7),
        (7, 1),
        (-7, 1),
        (7, -1),
        (-7, -1),
        (14, 10),
        (16, 10),
        (-14, 10),
        (-16, 10),
        (11, 8),
        (13, 8),
        (-11, 8),
        (-13, 8),
        # . Large magnitudes
        (2**62, 3),
        (-(2**62), 3),
        (2**63 - 1, 7),
        (-(2**63) + 1, 7),
        (2**62, -3),
        (-(2**62), -3),
        (2**63 - 1, -7),
        (-(2**63) + 1, -7),
        (2**63 - 1, 2),
        (2**63 - 1, -2),
        (-(2**63) + 1, 2),
        (-(2**63) + 1, -2),
        (2**62, 10),
        (2**62 + 2, 10),
        (-(2**62), 10),
        (-(2**62) - 2, 10),
        (2**62, -10),
        (2**62 + 2, -10),
    ]
    for num, factor in test_cases:
        arr = np.array([num], dtype="int64")
        # half to even
        res = arr_div_even(arr, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(
            rounding=ROUND_HALF_EVEN
        )
        assert (
            res[0] == exp
        ), f"Failed: arr_div_even({num}, {factor}) = {res[0]}, expected {exp}"
        # half to even multiple
        if -(2**62) - 10 < num < 2**62 + 10:  # avoid overflow in *2
            res2 = arr_div_even_mul(arr, factor, 2)  # type: ignore
            assert (
                res2[0] == res[0] * 2
            ), f"Failed: arr_div_even_mul({num}, {factor}, 2) = {res2[0]}, expected {res[0] * 2}"
        # half to up
        res = arr_div_up(arr, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(rounding=ROUND_HALF_UP)
        assert (
            res[0] == exp
        ), f"Failed: arr_div_up({num}, {factor}) = {res[0]}, expected {exp}"
        # half to up multiple
        if -(2**62) - 10 < num < 2**62 + 10:  # avoid overflow in *2
            res2 = arr_div_up_mul(arr, factor, 2)  # type: ignore
            assert (
                res2[0] == res[0] * 2
            ), f"Failed: arr_div_up_mul({num}, {factor}, 2) = {res2[0]}, expected {res[0] * 2}"
        # half to down
        res = arr_div_down(arr, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(
            rounding=ROUND_HALF_DOWN
        )
        assert (
            res[0] == exp
        ), f"Failed: arr_div_down({num}, {factor}) = {res[0]}, expected {exp}"
        # half to down multiple
        if -(2**62) - 10 < num < 2**62 + 10:  # avoid overflow in *2
            res2 = arr_div_down_mul(arr, factor, 2)  # type: ignore
            assert (
                res2[0] == res[0] * 2
            ), f"Failed: arr_div_down_mul({num}, {factor}, 2) = {res2[0]}, expected {res[0] * 2}"

    # Ceil / Floor
    test_cases = [
        # 1) Exact division (r == 0)
        (4, 2),
        (-9, 3),
        (9, -3),
        (-12, -4),
        # 2) Positive divisor (mixed numerators)
        (7, 4),  # 1.75
        (11, 4),  # 2.75
        (-7, 4),  # -1.75
        (-11, 4),  # -2.75
        # 3) Negative divisor (mixed numerators)
        (7, -4),  # -1.75
        (11, -4),  # -2.75
        (-7, -4),  # 1.75
        (-11, -4),  # 2.75
        # 4) Fractions with |num| < |factor| (results in (-1, 0, 1) bands)
        (3, 5),
        (-3, 5),
        (3, -5),
        (-3, -5),
        (1, 3),
        (2, 3),
        (-1, 3),
        (-2, 3),
        # 5) Denominator ±1 (fast paths)
        (7, 1),
        (-7, 1),
        (7, -1),
        (-7, -1),
        # 6) Zero numerator
        (0, 3),
        (0, -3),
        (0, 1),
        (0, -1),
        # 7) Near “half-ish” examples (just below / just above halves)
        (14, 10),
        (16, 10),
        (-14, 10),
        (-16, 10),  # 1.4 / 1.6 / -1.4 / -1.6
        (11, 8),
        (13, 8),
        (-11, 8),
        (-13, 8),  # 1.375 / 1.625 / ...
        # 8) Sign-edge microcases around zero
        (1, -2),  # -0.5  -> floor=-1, ceil=0
        (-1, -2),  # 0.5   -> floor=0,  ceil=1
        (1, 2),  # 0.5   -> floor=0,  ceil=1
        (-1, 2),  # -0.5  -> floor=-1, ceil=0
        # 9) Large magnitudes within int64 (exercise remainder & sign at scale)
        (2**62, 3),
        (-(2**62), 3),
        (2**62, -3),
        (-(2**62), -3),
        (2**63 - 1, 7),
        (-(2**63) + 1, 7),
        (2**63 - 1, -7),
        (-(2**63) + 1, -7),
        # 10) Large cases where |num| < |factor| but huge num
        (2**62, 2**63 - 1),
        (-(2**62), 2**63 - 1),
        (2**62, -(2**63 - 1)),
        (-(2**62), -(2**63 - 1)),
    ]
    for num, factor in test_cases:
        arr = np.array([num], dtype="int64")
        # Ceil
        res = arr_div_ceil(arr, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(rounding=ROUND_CEILING)
        assert (
            res[0] == exp
        ), f"Failed: arr_div_ceil({num}, {factor}) = {res[0]}, expected {exp}"
        # Ceil multiple
        if -(2**62) - 10 < num < 2**62 + 10:  # avoid overflow in *2
            res2 = arr_div_ceil_mul(arr, factor, 2)  # type: ignore
            assert (
                res2[0] == res[0] * 2
            ), f"Failed: arr_div_ceil_mul({num}, {factor}, 2) = {res2[0]}, expected {res[0] * 2}"
        # Floor
        res = arr_div_floor(arr, factor)  # type: ignore
        exp = (Decimal(num) / Decimal(factor)).to_integral_value(rounding=ROUND_FLOOR)
        assert (
            res[0] == exp
        ), f"Failed: arr_div_floor({num}, {factor}) = {res[0]}, expected {exp}"
        # Floor multiple
        if -(2**62) - 10 < num < 2**62 + 10:  # avoid overflow in *2
            res2 = arr_div_floor_mul(arr, factor, 2)  # type: ignore
            assert (
                res2[0] == res[0] * 2
            ), f"Failed: arr_div_floor_mul({num}, {factor}, 2) = {res2[0]}, expected {res[0] * 2}"

    print("Passed: ndarray_math")

    del (
        np,
        Decimal,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_HALF_DOWN,
        ROUND_CEILING,
        ROUND_FLOOR,
    )


def _test_sec_to_us() -> None:

    pairs = [
        (0.0, 0),
        (1.0, 1_000_000),
        (1.000001, 1_000_001),
        (0.999999, 999_999),
        (59.9999996, 59_999_999),
        (60.0, 60_000_000),
        (12345.678901, 12_345_678_901),
        (-0.000001, -1),
        (-0.999999, -999_999),
        (-1.000001, -1_000_001),
        (-59.9999996, -59_999_999),
        (-60.0, -60_000_000),
        (-86399.9999996, -86_399_999_999),
        (86399.9999996, 86_399_999_999),
        (31556926.123456, 31_556_926_123_456),
        (-31556926.123456, -31_556_926_123_456),
        (1e-06, 1),
        (-1e-06, -1),
        (0.0000004, 0),
        (0.0000005, 0),
        (999999.9999995, 999_999_999_999),
        (-999999.9999995, -999_999_999_999),
        (1234567890.123456, 1_234_567_890_123_456),
        (-1234567890.123456, -1_234_567_890_123_456),
        (1672531199.9999996, 1_672_531_199_999_999),
        (-2208988800.0, -2_208_988_800_000_000),
        (946684800.0, 946_684_800_000_000),
        (-31536000.0, -31_536_000_000_000),
        (2_147_483_647.999999, 2_147_483_647_999_999),
        (-2_147_483_648.000001, -2_147_483_648_000_001),
    ]
    for ss, us in pairs:
        # sec_to_us
        res = sec_to_us(ss)  # type: ignore
        assert res == us, f"Failed: sec_to_us({ss}) = {res}, expected {us}"

        # tm_from_*
        t1 = tm_fr_sec(ss)  # type: ignore
        t2 = tm_fr_us(us)  # type: ignore
        assert (
            t1.tm_sec == t2.tm_sec
            and t1.tm_min == t2.tm_min
            and t1.tm_hour == t2.tm_hour
            and t1.tm_mday == t2.tm_mday
            and t1.tm_mon == t2.tm_mon
            and t1.tm_year == t2.tm_year
            and t1.tm_wday == t2.tm_wday
            and t1.tm_yday == t2.tm_yday
            and t1.tm_isdst == t2.tm_isdst
        ), f"Failed:\nhmsf_fr_sec({ss})\n => {t1}\nhmsf_fr_us({us})\n => {t2}"

        # hmsf_from_*
        h1 = hmsf_fr_sec(ss)  # type: ignore
        h2 = hmsf_fr_us(us)  # type: ignore
        assert (
            h1.hour == h2.hour
            and h1.minute == h2.minute
            and h1.second == h2.second
            and h1.microsecond == h2.microsecond
        ), f"Failed:\nhmsf_fr_sec({ss})\n => {h1}\nhmsf_fr_us({us})\n => {h2}"

        # date_from_*
        d1 = date_fr_sec(ss)  # type: ignore
        d2 = date_fr_us(us)  # type: ignore
        assert (
            d1 == d2
        ), f"Failed:\ndate_fr_sec({ss})\n => {d1}\ndate_fr_us({us})\n => {d2}"

    print("Passed: sec_to_us")


def _cross_test_with_ndarray() -> None:
    import numpy as np

    # Times
    V = 9_999_999
    arr = np.array([i for i in range(-V, V + 1)], dtype="datetime64[us]")
    arr_i = arr.astype("int64")
    arr_f = arr_i.astype("float64") / 1_000_000.0
    arr_Y = dt64arr_year(arr)  # type: ignore
    arr_M = dt64arr_month(arr)  # type: ignore
    arr_D = dt64arr_day(arr)  # type: ignore
    arr_h = dt64arr_hour(arr)  # type: ignore
    arr_m = dt64arr_minute(arr)  # type: ignore
    arr_s = dt64arr_second(arr)  # type: ignore
    arr_us = dt64arr_microsecond(arr)  # type: ignore
    for i in range(len(arr)):
        us_i: cython.longlong = arr_i[i]
        ss_f: cython.double = arr_f[i]
        yy: cython.longlong = arr_Y[i]
        mm: cython.longlong = arr_M[i]
        dd: cython.longlong = arr_D[i]
        hh: cython.longlong = arr_h[i]
        mi: cython.longlong = arr_m[i]
        ss: cython.longlong = arr_s[i]
        us: cython.longlong = arr_us[i]

        # YMD from microseconds
        _ymd = ymd_fr_us(us_i)  # type: ignore
        assert _ymd.year == yy, f"{_ymd.year} != {yy}"
        assert _ymd.month == mm, f"{_ymd.month} != {mm}"
        assert _ymd.day == dd, f"{_ymd.day} != {dd}"

        # YMD from seconds (float)
        _ymd = ymd_fr_sec(ss_f)  # type: ignore
        assert _ymd.year == yy, f"{_ymd.year} != {yy}"
        assert _ymd.month == mm, f"{_ymd.month} != {mm}"
        assert _ymd.day == dd, f"{_ymd.day} != {dd}"

        # hmsf From microseconds
        _hmsf = hmsf_fr_us(us_i)  # type: ignore
        assert _hmsf.hour == hh, f"{_hmsf.hour} != {hh}"
        assert _hmsf.minute == mi, f"{_hmsf.minute} != {mi}"
        assert _hmsf.second == ss, f"{_hmsf.second} != {ss}"
        assert _hmsf.microsecond == us, f"{_hmsf.microsecond} != {us}"

        # hmsf From seconds (float)
        _hmsf = hmsf_fr_sec(ss_f)  # type: ignore
        assert _hmsf.hour == hh, f"{_hmsf.hour} != {hh}"
        assert _hmsf.minute == mi, f"{_hmsf.minute} != {mi}"
        assert _hmsf.second == ss, f"{_hmsf.second} != {ss}"
        assert _hmsf.microsecond == us, f"{_hmsf.microsecond} != {us}"

        # tm from microseconds
        _tm = tm_fr_us(us_i)  # type: ignore
        assert _tm.tm_year == yy, f"{_tm.tm_year} != {yy}"
        assert _tm.tm_mon == mm, f"{_tm.tm_mon} != {mm}"
        assert _tm.tm_mday == dd, f"{_tm.tm_mday} != {dd}"
        assert _tm.tm_hour == hh, f"{_tm.tm_hour} != {hh}"
        assert _tm.tm_min == mi, f"{_tm.tm_min} != {mi}"
        assert _tm.tm_sec == ss, f"{_tm.tm_sec} != {ss}"

        # tm from seconds (float)
        _tm = tm_fr_sec(ss_f)  # type: ignore
        assert _tm.tm_year == yy, f"{_tm.tm_year} != {yy}"
        assert _tm.tm_mon == mm, f"{_tm.tm_mon} != {mm}"
        assert _tm.tm_mday == dd, f"{_tm.tm_mday} != {dd}"
        assert _tm.tm_hour == hh, f"{_tm.tm_hour} != {hh}"
        assert _tm.tm_min == mi, f"{_tm.tm_min} != {mi}"
        assert _tm.tm_sec == ss, f"{_tm.tm_sec} != {ss}"

        # dtm from microseconds
        _dtm = dtm_fr_us(us_i)  # type: ignore
        assert _dtm.year == yy, f"{_dtm.year} != {yy}"
        assert _dtm.month == mm, f"{_dtm.month} != {mm}"
        assert _dtm.day == dd, f"{_dtm.day} != {dd}"
        assert _dtm.hour == hh, f"{_dtm.hour} != {hh}"
        assert _dtm.minute == mi, f"{_dtm.minute} != {mi}"
        assert _dtm.second == ss, f"{_dtm.second} != {ss}"
        assert _dtm.microsecond == us, f"{_dtm.microsecond} != {us}"

        # dtm from seconds (float)
        _dtm = dtm_fr_sec(ss_f)  # type: ignore
        assert _dtm.year == yy, f"{_dtm.year} != {yy}"
        assert _dtm.month == mm, f"{_dtm.month} != {mm}"
        assert _dtm.day == dd, f"{_dtm.day} != {dd}"
        assert _dtm.hour == hh, f"{_dtm.hour} != {hh}"
        assert _dtm.minute == mi, f"{_dtm.minute} != {mi}"
        assert _dtm.second == ss, f"{_dtm.second} != {ss}"
        assert _dtm.microsecond == us, f"{_dtm.microsecond} != {us}"

    # Dates
    arr = np.array([i for i in range(-V, V + 1)], dtype="datetime64[D]")
    arr_ord = dt64arr_to_ord(arr)  # type: ignore
    arr_wkdy = dt64arr_weekday(arr)  # type: ignore
    arr_Y = dt64arr_year(arr)  # type: ignore
    arr_M = dt64arr_month(arr)  # type: ignore
    arr_D = dt64arr_day(arr)  # type: ignore
    for i in range(len(arr)):
        ord_i: cython.longlong = arr_ord[i]
        wkd_i: cython.longlong = arr_wkdy[i]
        yy: cython.longlong = arr_Y[i]
        mm: cython.longlong = arr_M[i]
        dd: cython.longlong = arr_D[i]

        # YMD from ordinal
        _ymd = ymd_fr_ord(ord_i)  # type: ignore
        assert _ymd.year == yy, f"{_ymd.year} != {yy}"
        assert _ymd.month == mm, f"{_ymd.month} != {mm}"
        assert _ymd.day == dd, f"{_ymd.day} != {dd}"

        # Weekday
        wkd = ymd_weekday(yy, mm, dd)  # type: ignore
        assert wkd == wkd_i, f"{wkd_i} != {wkd_i}"

    print("Passed: cross_test_with_ndarray")

    del np


def _test_slice_to_uint() -> None:
    non_digits = " +-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    i_str = "0123456789"
    i_len: cython.Py_ssize_t = len(i_str)
    for pfix in non_digits:
        try:
            slice_to_uint(pfix + i_str, 0, i_len + 1)  # type: ignore
        except ValueError:
            pass

    for sfix in non_digits:
        try:
            slice_to_uint(i_str + sfix, 0, i_len + 1)  # type: ignore
        except ValueError:
            pass

    try:
        slice_to_uint("", 0, 1)  # type: ignore
    except ValueError:
        pass

    try:
        slice_to_uint("", 0, 0)  # type: ignore
    except ValueError:
        pass

    assert slice_to_uint(i_str, 0, i_len) == 123456789  # type: ignore

    print("Passed: slice_to_uint")


def _test_slice_to_ufloat() -> None:

    assert slice_to_ufloat("1", 0, 1) == 1.0  # type: ignore
    assert slice_to_ufloat("1.1", 0, 3) == 1.1  # type: ignore
    assert slice_to_ufloat("0.1", 0, 3) == 0.1  # type: ignore
    assert slice_to_ufloat(".1", 0, 2) == 0.1  # type: ignore
    assert slice_to_ufloat("1.", 0, 2) == 1.0  # type: ignore

    for i in (
        "1.1.1",
        "1..1",
        "..1",
        "1..",
        ".",
        "a1.1",
        "1.1a",
        "-1.1",
        "+1.1",
        " 1.1",
        "1.1 ",
    ):
        try:
            slice_to_ufloat(i, 0, len(i))  # type: ignore
        except ValueError:
            pass

    try:
        slice_to_ufloat("", 0, 1)  # type: ignore
    except ValueError:
        pass

    try:
        slice_to_ufloat("", 0, 0)  # type: ignore
    except ValueError:
        pass

    print("Passed: slice_to_ufloat")
