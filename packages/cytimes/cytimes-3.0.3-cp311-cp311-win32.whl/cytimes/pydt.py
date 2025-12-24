# cython: language_level=3
# cython: wraparound=False
# cython: boundscheck=False

from __future__ import annotations

# Cython imports
import cython
from cython.cimports import numpy as np  # type: ignore
from cython.cimports.cpython import datetime  # type: ignore
from cython.cimports.cpython.unicode import PyUnicode_READ_CHAR as str_read  # type: ignore
from cython.cimports.cpython.unicode import PyUnicode_GET_LENGTH as str_len  # type: ignore
from cython.cimports.cytimes.parser import (  # type: ignore
    Configs,
    parse_obj as _parse_obj,
    parse_month as _parse_month,
    parse_weekday as _parse_weekday,
)
from cython.cimports.cytimes import errors, utils  # type: ignore

np.import_array()
np.import_umath()
datetime.import_datetime()

# Python imports
from time import struct_time
from typing_extensions import Self
import datetime
import numpy as np
from babel.dates import format_date as _format_date
from zoneinfo import available_timezones as _available_timezones
from cytimes.parser import (
    Configs,
    parse_obj as _parse_obj,
    parse_month as _parse_month,
    parse_weekday as _parse_weekday,
)
from cytimes import errors, utils

__all__ = ["Pydt"]


# Utils ---------------------------------------------------------------------------------------
@cython.cfunc
@cython.inline(True)
@cython.exceptval(-2, check=False)
def _parse_unit_factor(cls: object, unit: str) -> cython.longlong:
    """(internal) Parse the datetime 'unit' to the corresponding
    conversion factor to microsecond `<'int'>`.

    :param cls `<'type'>`: The class object calling this function.
    :param unit `<'str'>`: The datetime unit: 'D', 'h', 'm', 's', 'ms', 'us'.
    :return `<'int'>`: The corresponding microsecond conversion factor.
    """
    # Guard
    if unit is None:
        errors.raise_argument_error(
            cls,
            "round/ceil/floor(unit)",
            "Supports: 'D', 'h', 'm', 's', 'ms' or 'us'; got None.",
        )

    # Unit: 's', 'm', 'h', 'D'
    unit_len: cython.Py_ssize_t = str_len(unit)
    if unit_len == 1:
        ch0: cython.Py_UCS4 = str_read(unit, 0)
        if ch0 == "s":
            return utils.US_SECOND
        if ch0 == "m":
            return utils.US_MINUTE
        if ch0 == "h":
            return utils.US_HOUR
        if ch0 == "D":
            return utils.US_DAY

    # Unit: 'ms', 'us', 'ns'
    elif unit_len == 2 and str_read(unit, 1) == "s":
        ch0: cython.Py_UCS4 = str_read(unit, 0)
        if ch0 == "m":
            return utils.US_MILLISECOND
        if ch0 in ("u", "n"):
            return 1

    # Unit: 'min' for pandas compatibility
    elif unit_len == 3 and unit == "min":
        return utils.US_MINUTE

    # Unsupported unit
    errors.raise_argument_error(
        cls,
        "round/ceil/floor(unit)",
        "Supports: 'D', 'h', 'm', 's', 'ms' or 'us'; got '%s'." % unit,
    )


# Pydt (Python Datetime) ----------------------------------------------------------------------
@cython.cclass
class _Pydt(datetime.datetime):
    """The base class for `<'Pydt'>`, a subclass of the cpython `<'datetime.datetime'>`.

    - Do `NOT` instantiate the base class directly.
    """

    __cls: object

    # Constructor --------------------------------------------------------------------------
    @classmethod
    def _new(
        cls,
        year: cython.int = 1,
        month: cython.int = 1,
        day: cython.int = 1,
        hour: cython.int = 0,
        minute: cython.int = 0,
        second: cython.int = 0,
        microsecond: cython.int = 0,
        tzinfo: datetime.tzinfo | str | None = None,
        fold: cython.int = 1,
    ) -> Self:
        """(internal) Create a new `Pydt` instance."""
        # Normalize non-fixed timezone
        tzinfo = utils.tz_parse(tzinfo)
        if tzinfo is not None and type(tzinfo) is not utils.T_TIMEZONE:
            dt: datetime.datetime = datetime.datetime_new(
                year, month, day, hour, minute, second, microsecond, tzinfo, fold
            )
            try:
                dt_norm: datetime.datetime = utils.dt_normalize_tz(dt, None)
            except Exception as err:
                raise errors.AmbiguousTimeError(err) from err
            if dt is not dt_norm:
                year = dt_norm.year
                month = dt_norm.month
                day = dt_norm.day
                hour = dt_norm.hour
                minute = dt_norm.minute
                second = dt_norm.second
                microsecond = dt_norm.microsecond
                fold = 0

        # Construct datetime
        if fold == 1:
            pt: _Pydt = _Pydt.__new__(
                cls, year, month, day, hour, minute, second, microsecond, tzinfo, fold=1
            )
        else:
            pt: _Pydt = _Pydt.__new__(
                cls, year, month, day, hour, minute, second, microsecond, tzinfo
            )
        pt.__cls = cls
        return pt

    @classmethod
    def parse(
        cls,
        dtobj: object,
        default: object | None = None,
        yearfirst: bool | None = None,
        dayfirst: bool | None = None,
        ignoretz: cython.bint = True,
        isoformat: cython.bint = True,
        cfg: Configs = None,
    ) -> Self:
        """Parse a datetime-like object into a datetime `<'Pydt'>`.

        :param dtobj `<'Datetime-Like'>`: A datetime-like object, supports:

            - `<'str'>`                 → parses into datetime, honoring `default`, `yearfirst`, `dayfirst`,
                                          `ignoretz`, `isoformat` and `cfg`.
            - `<'datetime.datetime'>`   → accepts `as-is`.
            - `<'datetime.date'>`       → converts to timezone-naive datetime with the same date fields.
            - `<'int/float'>`           → interprets as `seconds since Unix epoch` and converts to timezone-naive datetime
                                          (fractional seconds as microseconds).
            - `<'np.datetime64'>`       → converts to timezone-naive datetime; resolution finer than microseconds is truncated.

        ## Parameters (Only for String Input)

        :param default `<'datetime/date/None'>`: Fallback source for missing Y/M/D. Defaults to `None`.
            If `None` and required fields are missing, raises an error.
        :param yearfirst `<'bool/None'>`: Parse the first ambiguous Y/M/D value as year. Defaults to `None`.
            If 'None', uses `cfg.yearfirst` if 'cfg' is specified; otherwise. Defaults to `True`.
        :param dayfirst `<'bool/None'>`: Parse the first ambiguous Y/M/D values as day. Defaults to `None`.
            If 'None', uses `cfg.dayfirst` if 'cfg' is specified; otherwise. Defaults to `False`.
        :param ignoretz `<'bool'>`: If `True`, ignore any timezone information and return a naive datetime. Defaults to `True`.
            When timezone info is not needed, setting to `True` can improve performance.
        :param isoformat `<'bool'>`: If `True`, attempt ISO parsing first (automatically falls back to token parsing on failure).
            Otherwise always use token parsing. Defaults to `True`. For most common datetime strings,
            ISO parsing (when matched even partially) is faster.
        :param cfg `<'Configs/None'>`: The Parser configuration. Defaults to `None`.
            If `None`, uses the module's default `Configs`.

        :returns `<'Pydt'>`: The parsed or converted datetime.
        :raises `<'InvalidArgumentError'>`: On unsupported input types or any conversion/parsing failed.

        ## Notes
        - Non-string inputs do `NOT` use `default`, `yearfirst`, `dayfirst`, `ignoretz`, `isoformat` or `cfg`.
        """
        # Default value
        if default is not None:
            try:
                default = _parse_obj(
                    default, None, yearfirst, dayfirst, True, isoformat, cfg, None
                )
            except Exception as err:
                errors.raise_argument_error(cls, "parse(default, ...)", None, err)

        # Parse datetime object
        try:
            return _parse_obj(
                dtobj, default, yearfirst, dayfirst, ignoretz, isoformat, cfg, cls
            )
        except Exception as err:
            errors.raise_argument_error(cls, "parse(dtobj, ...)", None, err)

    @classmethod
    def now(cls, tz: datetime.tzinfo | str | None = None) -> Self:
        """Contruct a current datetime with optional timezone `<'Pydt'>`.

        :param tz `<'tzinfo/str/None'>`: The optional timezone. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime.
        """
        tz = utils.tz_parse(tz)
        return utils.dt_now(tz, cls)

    @classmethod
    def utcnow(cls) -> Self:
        """Construct a current `UTC` datetime (timezone-aware) `<'Pydt'>`."""
        return utils.dt_now(utils.UTC, cls)

    @classmethod
    def today(cls) -> Self:
        """Construct a current `local` datetime (timezone-naive) `<'Pydt'>`.

        ## Equivalent
        >>> Pydt.now(None)
        """
        return utils.dt_now(None, cls)

    @classmethod
    def combine(
        cls,
        date: datetime.date | str | None = None,
        time: datetime.time | str | None = None,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Combine date and time into a new datetime `<'Pydt'>`.

        :param date `<'date/str/None'>`: A date-like object. Defaults to `None`.
            If None, uses today's `local` date.
        :param time `<'time/str/None'>`: A time-like object. Defaults to `None`.
            If None, uses `00:00:00.000000`.
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive (when `time` has no timezone info, see `Notes`).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting combined datetime.

        ## Notes
        - Both `date` and `time` supports datetime-like object (please refer
          to `parse()` method for details), but only the corresponding date
          or time fields are used for combination.
        - If `tz` is `None`, but `time` contains timezone information, the
          resulting datetime will be timezone-aware using `time`'s timezone.
        - If `tz` is specified (not `None`), it `overrides` any timezone
          information in `time`.
        """
        # Timezone
        tz = utils.tz_parse(tz)

        # Parse date
        if date is not None and not utils.is_date(date):
            try:
                date = _parse_obj(date, None, True, False, True, True, None, None)
            except Exception as err:
                errors.raise_argument_error(cls, "combine(date, ...)", None, err)
            date = utils.date_fr_dt(date, None)

        # Prase time
        if time is not None and not utils.is_time(time):
            try:
                time = _parse_obj(
                    time, utils.EPOCH_DT, True, False, False, True, None, None
                )
            except Exception as err:
                errors.raise_argument_error(cls, "combine(time, ...)", None, err)
            time = utils.time_fr_dt(time, None)

        # New instance
        return utils.dt_combine(date, time, tz, cls)

    @classmethod
    def fromordinal(
        cls,
        ordinal: cython.int,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from Gregorian ordinal days `<'Pydt'>`.

        :param ordinal `<'int'>`: The proleptic Gregorian ordinal (day 1 is `0001-01-01`).
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime.
        """
        tz = utils.tz_parse(tz)
        try:
            return utils.dt_fr_ord(ordinal, tz, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "fromordinal(ordinal, ...)", None, err)

    @classmethod
    def fromseconds(
        cls,
        seconds: int | float,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from seconds since the epoch `<'Pydt'>`.

        :param seconds `<'int/float'>`: Seconds since epoch.
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime.

        ## Notes
        - Unlike `fromtimestamp()`, this method never assumes local time when
          `tz is None`, and interprets `seconds` as-is without any local-time conversion.
        - When `tz` is specified, the timezone is simply `attached` without any conversion.
        """
        tz = utils.tz_parse(tz)
        try:
            return utils.dt_fr_sec(float(seconds), tz, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "fromseconds(seconds, ...)", None, err)

    @classmethod
    def frommicroseconds(
        cls,
        us: cython.longlong,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from microseconds since the epoch `<'Pydt'>`.

        :param us `<'int'>`: Microseconds since epoch.
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime.

        ## Notes
        - Unlike `fromtimestamp()`, this method never assumes local time when
          `tz is None`, and interprets `us` as-is without any local-time conversion.
        - When `tz` is specified, the timezone is simply `attached` without any conversion.
        """
        tz = utils.tz_parse(tz)
        try:
            return utils.dt_fr_us(us, tz, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "frommicroseconds(us, ...)", None, err)

    @classmethod
    def fromtimestamp(
        cls,
        ts: int | float,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from a POSIX timestamp optionally converted to a timezone `<'Pydt'>`.

        POSIX timestamps are interpreted as seconds since the Unix epoch (1970-01-01 00:00:00 UTC).

        :param ts `<'int/float'>`: POSIX timestamp.
        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` naive `local` time (assumes local timezone).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime. Naive if `tz is None`,
            otherwise aware in the specifed timezone.
        """
        tz = utils.tz_parse(tz)
        try:
            return utils.dt_fr_ts(float(ts), tz, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "fromtimestamp(ts, ...)", None, err)

    @classmethod
    def utcfromtimestamp(cls, ts: int | float) -> Self:
        """Construct a UTC-aware datetime from a POSIX timestamp (timezone-aware) `<'Pydt'>`.

        :param ts `<'int/float'>`: POSIX timestamp.
        :returns `<'Pydt'>`: A UTC-aware datetime.

        ## Equivalent
        >>> Pydt.fromtimestamp(ts, tz='UTC')
        """
        try:
            return utils.dt_fr_ts(float(ts), utils.UTC, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "utcfromtimestamp(ts)", None, err)

    @classmethod
    def fromisoformat(cls, dtstr: str) -> Self:
        """Construct a datetime from an ISO format string `<'Pydt'>`.

        :param dtstr `<'str'>`: The ISO format datetime string.
        :returns `<'Pydt'>`: The resulting datetime.
        """
        try:
            dt = datetime.datetime.fromisoformat(dtstr)
        except Exception as err:
            errors.raise_argument_error(cls, "fromisoformat(dtstr)", None, err)
            return  # unreachable: suppress compiler warning
        return utils.dt_fr_dt(dt, cls)

    @classmethod
    def fromisocalendar(
        cls,
        year: cython.int,
        week: cython.int,
        weekday: cython.int,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from from ISO calendar values (year, week, weekday) `<'Pydt'>`.

        :param year `<'int'>`: ISO year number.
        :param week `<'int'>`: ISO week number.
            Automatically clamped to [1..52/53] (depends on whether is a long year).
        :param weekday `<'int'>`: ISO weekday.
            Automatically clamped to [1=Mon..7=Sun].
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime.
        """
        tz = utils.tz_parse(tz)
        try:
            return utils.dt_fr_iso(year, week, weekday, tz, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "fromisocalendar(...)", None, err)

    @classmethod
    def fromdayofyear(
        cls,
        year: cython.int,
        doy: cython.int,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from Gregorian year and day-of-year `<'Pydt'>`.

        :param year `<'int'>`: Gregorian year number.
        :param doy `<'int'>`: The day-of-year.
            Automatically clamped to [1..365/366] (depends on whether is a long year).
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime.
        """
        tz = utils.tz_parse(tz)
        try:
            return utils.dt_fr_doy(year, doy, tz, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "fromdayofyear(year, doy)", None, err)

    @classmethod
    def fromdate(
        cls,
        date: datetime.date,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from a date (all time fields set to 0) `<'Pydt'>`.

        :param date `<'datetime.date'>`: An instance or subclass of `datetime.date`.
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime with time fields set to zero.
        """
        tz = utils.tz_parse(tz)
        return utils.dt_fr_date(date, tz, cls)

    @classmethod
    def fromdatetime(
        cls,
        dt: datetime.datetime,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from another datetime `<'Pydt'>`.

        :param dt `<'datetime.datetime'>`: An instance or subclass of `datetime.datetime`.
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive (when `dt` has no timezone info, see `Notes`).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime with the same fields
            and optional replaced timezone info.

        ## Notes
        - If `tz` is `None`, but `dt` contains timezone information, the
          resulting datetime will be timezone-aware using `dt`'s timezone.
        - If `tz` is specified (not `None`), it `overrides` any timezone
          information in `dt`.
        """
        tz = utils.tz_parse(tz)
        if tz is not None:
            # fmt: off
            return utils.dt_new(
                dt.year, dt.month, dt.day, dt.hour, dt.minute,
                dt.second, dt.microsecond, tz, 1, cls,
            )
            # fmt: on
        return utils.dt_fr_dt(dt, cls)

    @classmethod
    def fromdatetime64(
        cls,
        dt64: object,
        tz: datetime.tzinfo | str | None = None,
    ) -> Self:
        """Construct a datetime from numpy.datetime64 `<'Pydt'>`.

        :param dt64 `<'datetime64'>`: The numpy.datetime64 instance.
        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime.
            Resolution finer than microseconds is truncated.
        """
        tz = utils.tz_parse(tz)
        try:
            return utils.dt64_to_dt(dt64, tz, cls)
        except Exception as err:
            errors.raise_argument_error(cls, "fromdatetime64(dt64, ...)", None, err)

    @classmethod
    def strptime(cls, dtstr: str, fmt: str) -> Self:
        """Construct a datetime parsed from a datetime-string `<'Pydt'>`.

        :param dtstr `<'str'>`: The datetime-string.
        :param format `<'str'>`: The format used to parse the strings.
        :returns `<'Pydt'>`: The resulting datetime.
        """
        try:
            dt = datetime.datetime.strptime(dtstr, fmt)
        except Exception as err:
            errors.raise_argument_error(cls, "strptime(dtstr, fmt)", None, err)
            return  # unreachable: suppress compiler warning
        return utils.dt_fr_dt(dt, cls)

    # Convertor ----------------------------------------------------------------------------
    @cython.ccall
    def ctime(self) -> str:
        """Return ctime-style string `<'str'>`

        - ctime-stype: 'Tue Oct  1 08:19:05 2024'
        """
        return utils.dt_to_ctime(self)

    @cython.ccall
    def strftime(self, fmt: str) -> str:
        """Format to string according to the given format `<'str'>`.

        :param fmt `<'str'>`: The format, e.g.: `'%d/%m/%Y, %H:%M:%S'`.
        :returns `<'str'>`: The formatted string.
        """
        return utils.dt_strformat(self, fmt)

    @cython.ccall
    def isoformat(self, sep: str = "T") -> str:
        """Return the date and time formatted according to ISO format `<'str'>`.

        :param sep `<'str'>`: The separator between date and time components. Defaults to `'T'`.
        :returns `<'str'>`: The ISO formatted string.

            - The default format is `'YYYY-MM-DDTHH:MM:SS[.f]'` with an optional
              fractional part when `microseconds != 0`.
            - If timezone-aware, the UTC offset is appened to the end: `'YYYY-MM-DDTHH:MM:SS[.f]+HHMM'`
        """
        # Guard
        if sep is None:
            errors.raise_argument_error(
                self._cls(),
                "isoformat(sep)",
                "Argument 'sep' cannot be None.",
            )
        return utils.dt_isoformat(self, sep, True)

    @cython.ccall
    def timedict(self) -> dict[str, int]:
        """Return `local` time dictionary compatible with `time.localtime()` `<'dict'>`.

        ## Example
        >>> dt.timedict()
        >>> {
                'tm_year': 2024,
                'tm_mon': 10,
                'tm_mday': 11,
                'tm_hour': 8,
                'tm_min': 14,
                'tm_sec': 11,
                'tm_wday': 4,
                'tm_yday': 285,
                'tm_isdst': 1
            }
        """
        _tm = utils.dt_to_tm(self, False)
        return {
            "tm_year": _tm.tm_year,
            "tm_mon": _tm.tm_mon,
            "tm_mday": _tm.tm_mday,
            "tm_hour": _tm.tm_hour,
            "tm_min": _tm.tm_min,
            "tm_sec": _tm.tm_sec,
            "tm_wday": _tm.tm_wday,
            "tm_yday": _tm.tm_yday,
            "tm_isdst": _tm.tm_isdst,
        }

    @cython.ccall
    def utctimedict(self) -> dict[str, int]:
        """Return `UTC` time dictionary compatible with `time.gmtime()` `<'dict'>`.

        ## Example
        >>> dt.utctimedict()
        >>> {
                'tm_year': 2024,
                'tm_mon': 10,
                'tm_mday': 11,
                'tm_hour': 6,
                'tm_min': 15,
                'tm_sec': 6,
                'tm_wday': 4,
                'tm_yday': 285,
                'tm_isdst': 0
            }
        """
        _tm = utils.dt_to_tm(self, True)
        return {
            "tm_year": _tm.tm_year,
            "tm_mon": _tm.tm_mon,
            "tm_mday": _tm.tm_mday,
            "tm_hour": _tm.tm_hour,
            "tm_min": _tm.tm_min,
            "tm_sec": _tm.tm_sec,
            "tm_wday": _tm.tm_wday,
            "tm_yday": _tm.tm_yday,
            "tm_isdst": _tm.tm_isdst,
        }

    @cython.ccall
    def timetuple(self) -> object:
        """Return `local` time tuple compatible with `time.localtime()` `<'struct_time'>`.

        ## Example
        >>> dt.timetuple()
        >>> time.struct_time(
                tm_year=2025,
                tm_mon=11,
                tm_mday=6,
                tm_hour=16,
                tm_min=48,
                tm_sec=57,
                tm_wday=3,
                tm_yday=310,
                tm_isdst=0
            )
        """
        _tm = utils.dt_to_tm(self, False)
        return struct_time(
            (
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
        )

    @cython.ccall
    def utctimetuple(self) -> object:
        """Return `UTC` time tuple compatible with `time.gmtime()` `<'struct_time'>`.

        ## Example
        >>> dt.utctimetuple()
        >>> time.struct_time(
                tm_year=2025,
                tm_mon=11,
                tm_mday=6,
                tm_hour=8,
                tm_min=50,
                tm_sec=9,
                tm_wday=3,
                tm_yday=310,
                tm_isdst=0
            )
        """
        _tm = utils.dt_to_tm(self, True)
        return struct_time(
            (
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
        )

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def toordinal(self) -> cython.int:
        """Return proleptic Gregorian ordinal for the year, month and day `<'int'>`.

        - Only the year, month and day values contribute to the result.
        - '0001-01-01' is day 1.
        """
        return utils.dt_to_ord(self, False)

    @cython.ccall
    def toseconds(self, utc: cython.bint = False) -> cython.double:
        """Return total seconds since epoch `<'float'>`.

        Computes the offset from `1970-01-01 00:00:00` to this datetime.
        Fractional seconds reflect microsecond precision.

        :param utc `<'bool'>`: Whether to subtract the UTC offset. Defaults to `False`.

            - When `True` and the datetime is `timezone-aware`, subtract the UTC
              offset first (i.e., normalize to UTC) before computing the epoch
              difference.
            - For `naive` datetime this flag is ignored.

        :returns `<'float'>`: Seconds since epoch, where fractional part represents the microseconds.

        ## Notes
        - Unlike `timestamp()`, this method never assumes local time for
          naive datetimes. Naive values are interpreted `as-is` without
          any local-time conversion.
        - For aware datetimes, offset handling (including DST folds/gaps)
          follows the attached timezone.
        """
        return utils.dt_to_sec(self, utc)

    @cython.ccall
    def tomicroseconds(self, utc: cython.bint = False) -> cython.longlong:
        """Return total microseconds since epoch `<'int'>`.

        Computes the offset from `1970-01-01 00:00:00` to this datetime.

        :param utc `<'bool'>`: Whether to subtract the UTC offset. Defaults to `False`.

            - When `True` and the datetime is `timezone-aware`, subtract the UTC
              offset first (i.e., normalize to UTC) before computing the epoch
              difference.
            - For `naive` datetimes this flag is ignored.

        :returns `<'int'>`: Microseconds since epoch.

        ## Notes
        - Unlike `timestamp()`, this method never assumes local time for
          naive datetimes. Naive values are interpreted `as-is` without
          any local-time conversion.
        - For aware datetimes, offset handling (including DST folds/gaps)
          follows the attached timezone.
        """
        return utils.dt_to_us(self, utc)

    @cython.ccall
    def timestamp(self) -> cython.double:
        """Return as a POSIX timestamp `<'float'>`."""
        return utils.dt_to_ts(self)

    @cython.ccall
    def date(self) -> datetime.date:
        """Return the date part `<'datetime.date'>`."""
        return utils.date_fr_dt(self, None)

    @cython.ccall
    def time(self) -> datetime.time:
        """Return the time part (without timezone information) `<'datetime.time'>`."""
        return datetime.time_new(
            self.access_hour(),
            self.access_minute(),
            self.access_second(),
            self.access_microsecond(),
            None,
            0,
        )

    @cython.ccall
    def timetz(self) -> datetime.time:
        """Return the time part (with the same timezone information) `<'datetime.time'>`."""
        return utils.time_fr_dt(self, None)

    # Internal -----------------------------------------------------------------------------
    @cython.cfunc
    @cython.inline(True)
    def _cls(self) -> object:
        """(internal) Access the class object of the current instance `<'type[Pydt]'>`."""
        if self.__cls is None:
            self.__cls = self.__class__
        return self.__cls

    # Manipulator --------------------------------------------------------------------------
    @cython.ccall
    def replace(
        self,
        year: cython.int = -1,
        month: cython.int = -1,
        day: cython.int = -1,
        hour: cython.int = -1,
        minute: cython.int = -1,
        second: cython.int = -1,
        microsecond: cython.int = -1,
        tzinfo: datetime.tzinfo | str | None = -1,
        fold: cython.int = -1,
    ) -> _Pydt:
        """Replace the specified datetime fields with new values `<'Pydt'>`.

        :param year `<'int'>`: Absolute year. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..9999].
        :param month `<'int'>`: Absolute month. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..12].
        :param day `<'int'>`: Absolute day. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..maximum days the resulting month].
        :param hour `<'int'>`: Absolute hour. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..23].
        :param minute `<'int'>`: Absolute minute. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param second `<'int'>`: Absolute second. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param microsecond `<'int'>`: Absolute microsecond. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..999999].
        :param tzinfo `<'tzinfo/None'>`: The timeone. Defaults to `SENTINEL` (no change).

            - `<'None'>`: removes tzinfo (makes datetime naive).
            - `<'str'>`: Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>`: A subclass of `datetime.tzinfo`.

        :param fold `<'int'>`: Fold value (0 or 1) for ambiguous times. Defaults to `SENTINEL` (no change).
        :returns `<'Pydt'>`: The resulting datetime after applying the specified field replacements.
        """
        # Prase timezone
        if not isinstance(tzinfo, int):
            tzinfo = utils.tz_parse(tzinfo)

        # Replacement
        try:
            # fmt: off
            return utils.dt_replace(self, 
                year, month, day, hour, minute, second,
                microsecond, tzinfo, fold, self._cls(),
            )
            # fmt: on
        except Exception as err:
            errors.raise_argument_error(self._cls(), "replace(...)", None, err)

    # . year
    @cython.ccall
    def to_curr_year(
        self,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month and day in the current year `<'Pydt'>`.

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the current year.

        ## Example
        >>> dt.to_curr_year(month="Feb", day=31)    # The last day of February in the current year
        >>> dt.to_curr_year(month=11)               # The same day of November in the current year
        >>> dt.to_curr_year(day=1)                  # The 1st day of the current month
        """
        # Parse month
        mm: cython.int = _parse_month(month, None, True)
        if mm == -1 or mm == self.access_month():
            return self.to_curr_month(day)  # exit: same month
        yy: cython.int = self.access_year()

        # Clamp to max days
        dd: cython.int = self.access_day() if day < 1 else day
        if dd > 28:
            dd = min(dd, utils.days_in_month(yy, mm))

        # New instance
        try:
            return utils.dt_new(
                yy,
                mm,
                dd,
                self.access_hour(),
                self.access_minute(),
                self.access_second(),
                self.access_microsecond(),
                self.access_tzinfo(),
                self.access_fold(),
                self._cls(),
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_curr_year(...)", None, err)

    @cython.ccall
    def to_prev_year(
        self,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month and day in the previous year `<'Pydt'>`.

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the previous year.

        ## Example
        >>> dt.to_prev_year(month="Feb", day=31)    # The last day of February in the previous year
        >>> dt.to_prev_year(month=11)               # The same day of November in the previous year
        >>> dt.to_prev_year(day=1)                  # The 1st day of the current month in the previous year
        """
        return self.to_year(-1, month, day)

    @cython.ccall
    def to_next_year(
        self,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month and day in the next year `<'Pydt'>`.

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the next year.

        ## Example
        >>> dt.to_next_year(month="Feb", day=31)    # The last day of February in the next year
        >>> dt.to_next_year(month=11)               # The same day of November in the next year
        >>> dt.to_next_year(day=1)                  # The 1st day of the current month in the next year
        """
        return self.to_year(1, month, day)

    @cython.ccall
    def to_year(
        self,
        offset: cython.int,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month and day in the year (+/-) offset `<'Pydt'>`.

        :param offset `<'int'>`: The year offset (+/-).

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>` Month number (1=Jan...12=Dec).
            - `<'str'>` Month name (case-insensitive), e.g., 'Jan', 'februar', '三月'.
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pydt'>`: The adjusted datetime.

        ## Example
        >>> dt.to_year(-2, "Feb", 31)  # The last day of February, two years ago
        >>> dt.to_year(2, 11)          # The same day of November, two years later
        >>> dt.to_year(2, day=1)       # The 1st day of the current month, two years later
        """
        # Fast-path: no offset
        if offset == 0:
            return self.to_curr_year(month, day)  # exit

        # Compute new year & month & day
        yy: cython.int = self.access_year() + offset
        mm: cython.int = _parse_month(month, None, True)
        if mm == -1:
            mm = self.access_month()
        dd: cython.int = self.access_day() if day < 1 else day
        if dd > 28:
            dd = min(dd, utils.days_in_month(yy, mm))

        # New instance
        try:
            return utils.dt_new(
                yy,
                mm,
                dd,
                self.access_hour(),
                self.access_minute(),
                self.access_second(),
                self.access_microsecond(),
                self.access_tzinfo(),
                self.access_fold(),
                self._cls(),
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_year(...)", None, err)

    # . quarter
    @cython.ccall
    def to_curr_quarter(
        self,
        month: cython.int = -1,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month-of-quarter and day in the current quarter. `<'Pydt'>`.

        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the current quarter.

        ## Example
        >>> dt.to_curr_quarter(month=1, day=31) # The last day of the 1st quarter month in the current quarter
        >>> dt.to_curr_quarter(month=2)         # The same day of the 2nd quarter month in the current quarter
        >>> dt.to_curr_quarter(day=1)           # The 1st day of the current month-of-quarter in the current quarter
        """
        # Fast-path: no adjustment
        if month < 1:
            return self.to_curr_month(day)  # exit

        # Compute new month
        curr_mm: cython.int = self.access_month()
        mm: cython.int = utils.quarter_of_month(curr_mm) * 3 + (min(month, 3) - 3)
        if mm == curr_mm:
            return self.to_curr_month(day)  # exit: same month
        yy: cython.int = self.access_year()

        # Clamp to max days
        dd: cython.int = self.access_day() if day < 1 else day
        if dd > 28:
            dd = min(dd, utils.days_in_month(yy, mm))

        # New instance
        try:
            return utils.dt_new(
                yy,
                mm,
                dd,
                self.access_hour(),
                self.access_minute(),
                self.access_second(),
                self.access_microsecond(),
                self.access_tzinfo(),
                self.access_fold(),
                self._cls(),
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_curr_quarter(...)", None, err)

    @cython.ccall
    def to_prev_quarter(
        self,
        month: cython.int = -1,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month-of-quarter and day in the previous quarter. `<'Pydt'>`.

        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the previous quarter.

        ## Example
        >>> dt.to_prev_quarter(month=1, day=31) # The last day of the 1st quarter month in the previous quarter
        >>> dt.to_prev_quarter(month=2)         # The same day of the 2nd quarter month in the previous quarter
        >>> dt.to_prev_quarter(day=1)           # The 1st day of the current month-of-quarter in the previous quarter
        """
        return self.to_quarter(-1, month, day)

    @cython.ccall
    def to_next_quarter(
        self,
        month: cython.int = -1,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month-of-quarter and day in the next quarter. `<'Pydt'>`.

        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the next quarter.

        ## Example
        >>> dt.to_next_quarter(month=1, day=31) # The last day of the 1st quarter month in the next quarter
        >>> dt.to_next_quarter(month=2)         # The same day of the 2nd quarter month in the next quarter
        >>> dt.to_next_quarter(day=1)           # The 1st day of the current month-of-quarter in the next quarter
        """
        return self.to_quarter(1, month, day)

    @cython.ccall
    def to_quarter(
        self,
        offset: cython.int,
        month: cython.int = -1,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date to the specified month-of-quarter and day in the quarter (+/-) offset `<'Pydt'>`.

        :param offset `<'int'>`: The quarter offset (+/-).
        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime.

        ## Example
        >>> dt.to_quarter(-2, 1, 31)  # The last day of the 1st quarter month, two quarters ago
        >>> dt.to_quarter(2, 2)       # The same day of the 2nd quarter month, two quarters later
        >>> dt.to_quarter(2, day=1)   # The 1st day of the current month-of-quarter, two quarters later
        """
        # Fast-path: no offset
        if offset == 0:
            return self.to_curr_quarter(month, day)  # exit

        # Compute new year & month & day
        yy: cython.int = self.access_year()
        mm: cython.int = self.access_month()
        if month >= 1:
            mm = utils.quarter_of_month(mm) * 3 + (min(month, 3) - 3)
        m0: cython.int = mm + offset * 3
        yy = yy + (m0 - 1) // 12
        mm = ((m0 - 1) % 12) + 1
        dd: cython.int = self.access_day() if day < 1 else day
        if dd > 28:
            dd = min(dd, utils.days_in_month(yy, mm))

        # New instance
        try:
            return utils.dt_new(
                yy,
                mm,
                dd,
                self.access_hour(),
                self.access_minute(),
                self.access_second(),
                self.access_microsecond(),
                self.access_tzinfo(),
                self.access_fold(),
                self._cls(),
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_quarter(...)", None, err)

    # . month
    @cython.ccall
    def to_curr_month(self, day: cython.int = -1) -> _Pydt:
        """Adjust the date to the specified day of the current month `<'Pydt'>`.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the current month.

        ## Example
        >>> dt.to_curr_month(31)  # The last day of the current month
        >>> dt.to_curr_month(1)   # The 1st day of the current month
        """
        # Fast-path: no adjustment
        if day < 1:
            return self  # exit

        # Clamp to max days
        yy: cython.int = self.access_year()
        mm: cython.int = self.access_month()
        if day > 28:
            day = min(day, utils.days_in_month(yy, mm))
        if day == self.access_day():
            return self  # exit: same day

        # New instance
        try:
            return utils.dt_new(
                yy,
                mm,
                day,
                self.access_hour(),
                self.access_minute(),
                self.access_second(),
                self.access_microsecond(),
                self.access_tzinfo(),
                self.access_fold(),
                self._cls(),
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_curr_month(...)", None, err)

    @cython.ccall
    def to_prev_month(self, day: cython.int = -1) -> _Pydt:
        """Adjust the date to the specified day of the previous month `<'Pydt'>`.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the previous month.

        ## Example
        >>> dt.to_prev_month(31)  # The last day of the previous month
        >>> dt.to_prev_month(1)   # The 1st day of the previous month
        """
        return self.to_month(-1, day)

    @cython.ccall
    def to_next_month(self, day: cython.int = -1) -> _Pydt:
        """Adjust the date to the specified day of the next month `<'Pydt'>`.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime in the next month.

        ## Example
        >>> dt.to_next_month(31)  # The last day of the next month
        >>> dt.to_next_month(1)   # The 1st day of the next month
        """
        return self.to_month(1, day)

    @cython.ccall
    def to_month(self, offset: cython.int, day: cython.int = -1) -> _Pydt:
        """Adjust the date to the specified day of the month (+/-) offset `<'Pydt'>`.

        :param offset `<'int'>`: The month offset (+/-).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pydt'>`: The adjusted datetime.

        ## Example
        >>> dt.to_month(-2, 31)  # The last day of the month, two months ago
        >>> dt.to_month(2, 1)    # The 1st day of the month, two months later
        """
        # Fast-path: no offset
        if offset == 0:
            return self.to_curr_month(day)  # exit

        # Compute new year & month & day
        yy: cython.int = self.access_year()
        mm: cython.int = self.access_month()
        m0: cython.int = mm + offset
        yy = yy + (m0 - 1) // 12
        mm = ((m0 - 1) % 12) + 1
        dd: cython.int = self.access_day() if day < 1 else day
        if dd > 28:
            dd = min(dd, utils.days_in_month(yy, mm))

        # New instance
        try:
            return utils.dt_new(
                yy,
                mm,
                dd,
                self.access_hour(),
                self.access_minute(),
                self.access_second(),
                self.access_microsecond(),
                self.access_tzinfo(),
                self.access_fold(),
                self._cls(),
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_month(...)", None, err)

    # . weekday
    @cython.ccall
    def to_monday(self) -> _Pydt:
        """Adjust the date to the `Monday` of the current week `<'Pydt'>`."""
        return self._to_curr_weekday(0)

    @cython.ccall
    def to_tuesday(self) -> _Pydt:
        """Adjust the date to the `Tuesday` of the current week `<'Pydt'>`."""
        return self._to_curr_weekday(1)

    @cython.ccall
    def to_wednesday(self) -> _Pydt:
        """Adjust the date to the `Wednesday` of the current week `<'Pydt'>`."""
        return self._to_curr_weekday(2)

    @cython.ccall
    def to_thursday(self) -> _Pydt:
        """Adjust the date to the `Thursday` of the current week `<'Pydt'>`."""
        return self._to_curr_weekday(3)

    @cython.ccall
    def to_friday(self) -> _Pydt:
        """Adjust the date to the `Friday` of the current week `<'Pydt'>`."""
        return self._to_curr_weekday(4)

    @cython.ccall
    def to_saturday(self) -> _Pydt:
        """Adjust the date to the `Saturday` of the current week `<'Pydt'>`."""
        return self._to_curr_weekday(5)

    @cython.ccall
    def to_sunday(self) -> _Pydt:
        """Adjust the date to the `Sunday` of the current week `<'Pydt'>`."""
        return self._to_curr_weekday(6)

    @cython.ccall
    def to_curr_weekday(self, weekday: int | str | None = None) -> _Pydt:
        """Adjust the date to the specific weekday of the current week `<'Pydt'>`.

        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pydt'>`: The adjusted datetime in the current week.

        ## Example
        >>> dt.to_curr_weekday(0)      # The Monday of the current week
        >>> dt.to_curr_weekday("Tue")  # The Tuesday of the current week
        """
        return self._to_curr_weekday(_parse_weekday(weekday, None, True))

    @cython.ccall
    def to_prev_weekday(self, weekday: int | str | None = None) -> _Pydt:
        """Adjust the date to the specific weekday of the previous week `<'Pydt'>`.

        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pydt'>`: The adjusted datetime in the previous week.

        ## Example
        >>> dt.to_prev_weekday(0)      # The Monday of the previous week
        >>> dt.to_prev_weekday("Tue")  # The Tuesday of the previous week
        """
        return self.to_weekday(-1, weekday)

    @cython.ccall
    def to_next_weekday(self, weekday: int | str | None = None) -> _Pydt:
        """Adjust the date to the specific weekday of the next week `<'Pydt'>`.

        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pydt'>`: The adjusted datetime in the next week.

        ## Example
        >>> dt.to_next_weekday(0)      # The Monday of the next week
        >>> dt.to_next_weekday("Tue")  # The Tuesday of the next week
        """
        return self.to_weekday(1, weekday)

    @cython.ccall
    def to_weekday(self, offset: cython.int, weekday: int | str | None = None) -> _Pydt:
        """Adjust the date to the specific weekday of the week (+/-) offset `<'Pydt'>`.

        :param offset `<'int'>`: The week offset (+/-).
        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pydt'>`: The adjusted datetime.

        ## Example
        >>> dt.to_weekday(-2, 0)     # The Monday of the week, two weeks ago
        >>> dt.to_weekday(2, "Tue")  # The Tuesday of the week, two weeks later
        >>> dt.to_weekday(2)         # The same weekday of the week, two weeks later
        """
        # Fast-path: no offset
        wkd: cython.int = _parse_weekday(weekday, None, True)
        if offset == 0:
            return self._to_curr_weekday(wkd)  # exit

        # Compute new weekday
        days: cython.int = offset * 7
        if wkd != -1:
            days += wkd - self.access_weekday()

        # New instance
        return self.to_day(days)

    @cython.cfunc
    @cython.inline(True)
    def _to_curr_weekday(self, weekday: cython.int) -> _Pydt:
        """(internal) Adjust the date to the specific weekday of the current week `<'Pydt'>`.

        :param weekday `<'int'>`: Weekday number (0=Mon...6=Sun).
            Automatically clamped to [0..6]. If negative, no adjustment is made.
        :returns `<'Pydt'>`: The adjusted datetime in the current week.
        """
        # Fast-path: no adjustment
        if weekday < 0:
            return self  # exit

        # New instance
        return self.to_day(min(weekday, 6) - self.access_weekday())

    # . day
    @cython.ccall
    def to_yesterday(self) -> _Pydt:
        """Adjust the date to `Yesterday` `<'Pydt'>`."""
        return self.to_day(-1)

    @cython.ccall
    def to_tomorrow(self) -> _Pydt:
        """Adjust the date to `Tomorrow` `<'Pydt'>`."""
        return self.to_day(1)

    @cython.ccall
    def to_day(self, offset: cython.int) -> _Pydt:
        """Adjust the date to day (+/-) offset `<'Pydt'>`.

        :param offset `<'int'>`: The day offset (+/-).
        :returns `<'Pydt'>`: The adjusted datetime.

        ## Example
        >>> dt.to_day(-10)  # 10 days ago
        >>> dt.to_day(10)   # 10 days later
        """
        # Fast-path: no adjustment
        if offset == 0:
            return self  # exit

        # New instance
        try:
            return utils.dt_add(self, offset, 0, 0, self._cls())
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_day(...)", None, err)

    # . date&time
    @cython.ccall
    def normalize(self) -> _Pydt:
        """Set the time fields to midnight (00:00:00) `<'Pydt'>`.

        - This method is useful in cases, when the time does not matter.
        - The timezone is unaffected.
        """
        return self.to_time(0, 0, 0, 0)

    @cython.ccall
    def to_datetime(
        self,
        year: cython.int = -1,
        month: cython.int = -1,
        day: cython.int = -1,
        hour: cython.int = -1,
        minute: cython.int = -1,
        second: cython.int = -1,
        microsecond: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date and time fields with new values,
        without affecting the timezone `<'Pydt'>`.

        :param year `<'int'>`: Absolute year. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..9999].
        :param month `<'int'>`: Absolute month. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..12].
        :param day `<'int'>`: Absolute day. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..maximum days the resulting month].
        :param hour `<'int'>`: Absolute hour. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..23].
        :param minute `<'int'>`: Absolute minute. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param second `<'int'>`: Absolute second. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param microsecond `<'int'>`: Absolute microsecond. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..999999].
        :returns `<'Pydt'>`: The resulting datetime with new specified field values.

        ## Equivalent
        >>> dt.replace(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=second,
                microsecond=microsecond,
            )
        """
        try:
            # fmt: off
            return utils.dt_replace(self, 
                year, month, day, hour, minute, second,
                microsecond, -1, -1, self._cls(),
            )
            # fmt: on
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_datetime(...)", None, err)

    @cython.ccall
    def to_date(
        self,
        year: cython.int = -1,
        month: cython.int = -1,
        day: cython.int = -1,
    ) -> _Pydt:
        """Adjust the date with new values, without affecting other fields `<'Pydt'>`.

        :param year `<'int'>`: Absolute year. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..9999].
        :param month `<'int'>`: Absolute month. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..12].
        :param day `<'int'>`: Absolute day. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..maximum days the resulting month].
        :returns `<'Pydt'>`: The resulting datetime with new specified date field values.

        ## Equivalent
        >>> dt.replace(year=year, month=month, day=day)
        """
        try:
            return utils.dt_replace(
                self, year, month, day, -1, -1, -1, -1, -1, -1, self._cls()
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_date(...)", None, err)

    @cython.ccall
    def to_time(
        self,
        hour: cython.int = -1,
        minute: cython.int = -1,
        second: cython.int = -1,
        microsecond: cython.int = -1,
    ) -> _Pydt:
        """Adjust the time fields with new values, without affecting other fields `<'Pydt'>`.

        :param hour `<'int'>`: Absolute hour. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..23].
        :param minute `<'int'>`: Absolute minute. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param second `<'int'>`: Absolute second. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param microsecond `<'int'>`: Absolute microsecond. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..999999].
        :returns `<'Pydt'>`: The resulting datetime with new specified time field values.

        ## Equivalent
        >>> dt.replace(
                hour=hour,
                minute=minute,
                second=second,
                microsecond=microsecond,
            )
        """
        try:
            return utils.dt_replace(
                self, -1, -1, -1, hour, minute, second, microsecond, -1, -1, self._cls()
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "to_time(...)", None, err)

    @cython.ccall
    def to_first_of(self, unit: str) -> _Pydt:
        """Adjust the date fields to the first day of the specified datetime unit,
        without affecting the time fields `<'Pydt'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → First day of the year: `YYYY-01-01`
            - `'Q'` → First day of the quarter: `YYYY-MM-01`
            - `'M'` → First day of the month: `YYYY-MM-01`
            - `'W'` → First day (Monday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → First day of the specifed month: `YYYY-MM-01`

        :returns `<'Pydt'>`: The adjusted datetime.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self._cls(),
                "to_first_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W' or Month name; got None.",
            )

        # Unit: 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . weekday
            if ch0 == "W":
                return self._to_curr_weekday(0)
            # . month
            if ch0 == "M":
                return self.to_curr_month(1)
            # . quarter
            if ch0 == "Q":
                return self.to_curr_quarter(1, 1)
            # . year
            if ch0 == "Y":
                return self.to_date(-1, 1, 1)

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.to_date(-1, val, 1)

        # Unsupported unit
        errors.raise_argument_error(
            self._cls(),
            "to_first_of(unit)",
            "Supports: 'Y', 'Q', 'M', 'W' or Month name; got '%s'." % unit,
        )

    @cython.ccall
    def to_last_of(self, unit: str) -> _Pydt:
        """Adjust the date fields to the last day of the specified datetime unit,
        without affecting the time fields `<'Pydt'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → Last day of the year: `YYYY-12-31`
            - `'Q'` → Last day of the quarter: `YYYY-MM-(30..31)`
            - `'M'` → Last day of the month: `YYYY-MM-(28..31)`
            - `'W'` → Last day (Sunday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → Last day of the specifed month: `YYYY-MM-(28..31)`

        :returns `<'Pydt'>`: The adjusted datetime.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self._cls(),
                "to_last_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W' or Month name; got None.",
            )

        # Unit: 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . weekday
            if ch0 == "W":
                return self._to_curr_weekday(6)
            # . month
            if ch0 == "M":
                return self.to_curr_month(31)
            # . quarter
            if ch0 == "Q":
                return self.to_curr_quarter(3, 31)
            # . year
            if ch0 == "Y":
                return self.to_date(-1, 12, 31)

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.to_date(-1, val, 31)

        # Unsupported unit
        errors.raise_argument_error(
            self._cls(),
            "to_last_of(unit)",
            "Supports: 'Y', 'Q', 'M', 'W' or Month name; got '%s'." % unit,
        )

    @cython.ccall
    def to_start_of(self, unit: str) -> _Pydt:
        """Adjust the date & time fields to the start of the specified datetime unit `<'Pydt'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'`  → Start of year: `YYYY-01-01 00:00:00`
            - `'Q'`  → Start of quarter: `YYYY-MM-01 00:00:00`
            - `'M'`  → Start of month: `YYYY-MM-01 00:00:00`
            - `'W'`  → Start of week (Monday): `YYYY-MM-DD 00:00:00`
            - `'D'`  → Start of day: `YYYY-MM-DD 00:00:00`
            - `'h'`  → Start of hour: `YYYY-MM-DD hh:00:00`
            - `'m'`  → Start of minute: `YYYY-MM-DD hh:mm:00`
            - `'s'`  → Start of second: `YYYY-MM-DD hh:mm:ss.000000`
            - `'ms'` → Start of millisecond: `YYYY-MM-DD hh:mm:ss.uuu000`
            - `'us'` → Return the instance `as-is`.
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                     → Start of the specifed month: `YYYY-MM-01 00:00:00`
            - `Weekday` (e.g., `'Mon'`, `'Tuesday'`, `'星期三'`)
                     → Start of the specifed weekday: `YYYY-MM-DD 00:00:00`

        :returns `<'Pydt'>`: The adjusted datetime.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self._cls(),
                "to_start_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us' "
                "or Month/Weekday name; got None.",
            )

        # Unit: 's', 'm', 'h', 'D', 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . second
            if ch0 == "s":
                return self.to_time(-1, -1, -1, 0)
            # . minute
            if ch0 == "m":
                return self.to_time(-1, -1, 0, 0)
            # . hour
            if ch0 == "h":
                return self.to_time(-1, 0, 0, 0)
            # . day
            if ch0 == "D":
                return self.to_time(0, 0, 0, 0)
            # . week
            if ch0 == "W":
                # fmt: off
                return self.add(
                    0, 0, 0, 0,
                    -self.access_weekday(),
                    -self.access_hour(),
                    -self.access_minute(),
                    -self.access_second(),
                    0,
                    -self.access_microsecond(),
                )
                # fmt: on
            # . month
            if ch0 == "M":
                return self.to_datetime(-1, -1, 1, 0, 0, 0, 0)
            # . quarter
            if ch0 == "Q":
                mm: cython.int = self.access_month()
                mm = utils.quarter_of_month(mm) * 3 - 2
                return self.to_datetime(-1, mm, 1, 0, 0, 0, 0)
            # . year
            if ch0 == "Y":
                return self.to_datetime(-1, 1, 1, 0, 0, 0, 0)

        # Unit: 'ms', 'us', 'ns'
        elif unit_len == 2 and str_read(unit, 1) == "s":
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . millisecond
            if ch0 == "m":
                return self.to_time(-1, -1, -1, self.access_millisecond() * 1000)
            # . microsecond / nanosecond
            if ch0 in ("u", "n"):
                return self

        # Unit: 'min' for pandas compatibility
        elif unit_len == 3 and unit == "min":
            return self.to_time(-1, -1, 0, 0)

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.to_datetime(-1, val, 1, 0, 0, 0, 0)

        # Weekday name
        val: cython.int = _parse_weekday(unit, None, False)
        if val != -1:
            # fmt: off
            return self.add(
                0, 0, 0, 0,
                val - self.access_weekday(),
                -self.access_hour(),
                -self.access_minute(),
                -self.access_second(),
                0,
                -self.access_microsecond(),
            )
            # fmt: on

        # Invalid
        errors.raise_argument_error(
            self._cls(),
            "to_start_of(unit)",
            "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us' "
            "or Month/Weekday name; got '%s'." % unit,
        )

    @cython.ccall
    def to_end_of(self, unit: str) -> _Pydt:
        """Adjust the date & time fields to the end of the specified datetime unit `<'Pydt'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'`  → End of year: `YYYY-12-31 23:59:59.999999`
            - `'Q'`  → End of quarter: `YYYY-MM-(30..31) 23:59:59.999999`
            - `'M'`  → End of month: `YYYY-MM-(28..31) 23:59:59.999999`
            - `'W'`  → End of week (Sunday): `YYYY-MM-DD 23:59:59.999999`
            - `'D'`  → End of day: `YYYY-MM-DD 23:59:59.999999`
            - `'h'`  → End of hour: `YYYY-MM-DD hh:59:59.999999`
            - `'m'`  → End of minute: `YYYY-MM-DD hh:mm:59.999999`
            - `'s'`  → End of second: `YYYY-MM-DD hh:mm:ss.999999`
            - `'ms'` → End of millisecond: `YYYY-MM-DD hh:mm:ss.uuu999`
            - `'us'` → Return the instance `as-is`.
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                     → End of the specifed month: `YYYY-MM-(28..31) 23:59:59.999999`
            - `Weekday` (e.g., `'Mon'`, `'Tuesday'`, `'星期三'`)
                     → End of the specifed weekday: `YYYY-MM-DD 23:59:59.999999`

        :returns `<'Pydt'>`: The adjusted datetime.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self._cls(),
                "to_end_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us' "
                "or Month/Weekday name; got None.",
            )

        # Unit: 's', 'm', 'h', 'D', 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . second
            if ch0 == "s":
                return self.to_time(-1, -1, -1, 999999)
            # . minute
            if ch0 == "m":
                return self.to_time(-1, -1, 59, 999999)
            # . hour
            if ch0 == "h":
                return self.to_time(-1, 59, 59, 999999)
            # . day
            if ch0 == "D":
                return self.to_time(23, 59, 59, 999999)
            # . week
            if ch0 == "W":
                # fmt: off
                return self.add(
                    0, 0, 0, 0,
                    6 - self.access_weekday(),
                    23 - self.access_hour(),
                    59 - self.access_minute(),
                    59 - self.access_second(),
                    0,
                    999999 - self.access_microsecond(),
                )
                # fmt: on
            # . month
            if ch0 == "M":
                return self.to_datetime(-1, -1, 31, 23, 59, 59, 999999)
            # . quarter
            if ch0 == "Q":
                mm: cython.int = self.access_month()
                mm = utils.quarter_of_month(mm) * 3
                return self.to_datetime(-1, mm, 31, 23, 59, 59, 999999)
            # . year
            if ch0 == "Y":
                return self.to_datetime(-1, 12, 31, 23, 59, 59, 999999)

        # Unit: 'ms', 'us', 'ns'
        elif unit_len == 2 and str_read(unit, 1) == "s":
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . millisecond
            if ch0 == "m":
                return self.to_time(-1, -1, -1, self.access_millisecond() * 1000 + 999)
            # . microsecond / nanosecond
            if ch0 in ("u", "n"):
                return self

        # Unit: 'min' for pandas compatibility
        elif unit_len == 3 and unit == "min":
            return self.to_time(-1, -1, 59, 999999)

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.to_datetime(-1, val, 31, 23, 59, 59, 999999)

        # Weekday name
        val: cython.int = _parse_weekday(unit, None, False)
        if val != -1:
            # fmt: off
            return self.add(
                0, 0, 0, 0,
                val - self.access_weekday(),
                23 - self.access_hour(),
                59 - self.access_minute(),
                59 - self.access_second(),
                0,
                999999 - self.access_microsecond(),
            )
            # fmt: on

        # Invalid
        errors.raise_argument_error(
            self._cls(),
            "to_end_of(unit)",
            "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us' "
            "or Month/Weekday name; got '%s'." % unit,
        )

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_first_of(self, unit: str) -> cython.bint:
        """Check whether the date fields are on the first day of the specified datetime unit `<'bool'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → First day of the year: `YYYY-01-01`
            - `'Q'` → First day of the quarter: `YYYY-MM-01`
            - `'M'` → First day of the month: `YYYY-MM-01`
            - `'W'` → First day (Monday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → First day of the specifed month: `YYYY-MM-01`

        :return `<'bool'>`: True if the instance is on the first day
            of the specified datetime unit; Otherwise False.
        """
        # Guard
        if unit is None:
            return False

        # Unit: 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . weekday
            if ch0 == "W":
                return self.access_weekday() == 0
            # . month
            if ch0 == "M":
                return utils.dt_is_first_dom(self)
            # . quarter
            if ch0 == "Q":
                return utils.dt_is_first_doq(self)
            # . year
            if ch0 == "Y":
                return utils.dt_is_first_doy(self)

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.access_month() == val and utils.dt_is_first_dom(self)

        # Invalid
        return False

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_last_of(self, unit: str) -> cython.bint:
        """Check whether the date fields are on the last day of the specified datetime unit `<'bool'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → Last day of the year: `YYYY-12-31`
            - `'Q'` → Last day of the quarter: `YYYY-MM-(30..31)`
            - `'M'` → Last day of the month: `YYYY-MM-(28..31)`
            - `'W'` → Last day (Sunday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → Last day of the specifed month: `YYYY-MM-(28..31)`

        :return `<'bool'>`: True if the instance is on the last day
            of the specified datetime unit; Otherwise False.
        """
        # Guard
        if unit is None:
            return False

        # Unit: 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . weekday
            if ch0 == "W":
                return self.access_weekday() == 6
            # . month
            if ch0 == "M":
                return utils.dt_is_last_dom(self)
            # . quarter
            if ch0 == "Q":
                return utils.dt_is_last_doq(self)
            # . year
            if ch0 == "Y":
                return utils.dt_is_last_doy(self)

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.access_month() == val and utils.dt_is_last_dom(self)

        # Invalid
        return False

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_start_of(self, unit: str) -> cython.bint:
        """Check whether date & time fileds are the start of the specified datetime unit `<'bool'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'`  → Start of year: `YYYY-01-01 00:00:00`
            - `'Q'`  → Start of quarter: `YYYY-MM-01 00:00:00`
            - `'M'`  → Start of month: `YYYY-MM-01 00:00:00`
            - `'W'`  → Start of week (Monday): `YYYY-MM-DD 00:00:00`
            - `'D'`  → Start of day: `YYYY-MM-DD 00:00:00`
            - `'h'`  → Start of hour: `YYYY-MM-DD hh:00:00`
            - `'m'`  → Start of minute: `YYYY-MM-DD hh:mm:00`
            - `'s'`  → Start of second: `YYYY-MM-DD hh:mm:ss.000000`
            - `'ms'` → Start of millisecond: `YYYY-MM-DD hh:mm:ss.uuu000`
            - `'us'` → Return the instance `as-is`.
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                     → Start of the specifed month: `YYYY-MM-01 00:00:00`
            - `Weekday` (e.g., `'Mon'`, `'Tuesday'`, `'星期三'`)
                     → Start of the specifed weekday: `YYYY-MM-DD 00:00:00`

        :return `<'bool'>`: True if the instance is at the start
            of the specified datetime unit; Otherwise False.
        """
        # Guard
        if unit is None:
            return False

        # Unit: 's', 'm', 'h', 'D', 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . second
            if ch0 == "s":
                return self.access_microsecond() == 0
            # . minute
            if ch0 == "m":
                return self.access_second() == 0 and self.access_microsecond() == 0
            # . hour
            if ch0 == "h":
                return (
                    self.access_minute() == 0
                    and self.access_second() == 0
                    and self.access_microsecond() == 0
                )
            # Start of time - - - - - - - - - - - - - - - - - - - - - - - -
            if not utils.dt_is_start_of_time(self):
                return False
            # . day
            if ch0 == "D":
                return True
            # . week
            if ch0 == "W":
                return self.access_weekday() == 0
            # . month
            if ch0 == "M":
                return utils.dt_is_first_dom(self)
            # . quarter
            if ch0 == "Q":
                return utils.dt_is_first_doq(self)
            # . year
            if ch0 == "Y":
                return utils.dt_is_first_doy(self)

        # Unit: 'ms', 'us', 'ns'
        elif unit_len == 2 and str_read(unit, 1) == "s":
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . millisecond
            if ch0 == "m":
                return self.access_microsecond() % 1000 == 0
            # . microsecond / nanosecond
            if ch0 in ("u", "n"):
                return True

        # Unit: 'min' for pandas compatibility
        elif unit_len == 3 and unit == "min":
            return self.access_second() == 0 and self.access_microsecond() == 0

        # Start of time - - - - - - - - - - - - - - - - - - - - - - - -
        if not utils.dt_is_start_of_time(self):
            return False

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.access_month() == val and utils.dt_is_first_dom(self)

        # Weekday name
        val: cython.int = _parse_weekday(unit, None, False)
        if val != -1:
            return self.access_weekday() == val

        # Invalid
        return False

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_end_of(self, unit: str) -> cython.bint:
        """Check whether date & time fileds are the end of the specified datetime unit `<'bool'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'`  → End of year: `YYYY-12-31 23:59:59.999999`
            - `'Q'`  → End of quarter: `YYYY-MM-(30..31) 23:59:59.999999`
            - `'M'`  → End of month: `YYYY-MM-(28..31) 23:59:59.999999`
            - `'W'`  → End of week (Sunday): `YYYY-MM-DD 23:59:59.999999`
            - `'D'`  → End of day: `YYYY-MM-DD 23:59:59.999999`
            - `'h'`  → End of hour: `YYYY-MM-DD hh:59:59.999999`
            - `'m'`  → End of minute: `YYYY-MM-DD hh:mm:59.999999`
            - `'s'`  → End of second: `YYYY-MM-DD hh:mm:ss.999999`
            - `'ms'` → End of millisecond: `YYYY-MM-DD hh:mm:ss.uuu999`
            - `'us'` → Return the instance `as-is`.
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                     → End of the specifed month: `YYYY-MM-(28..31) 23:59:59.999999`
            - `Weekday` (e.g., `'Mon'`, `'Tuesday'`, `'星期三'`)
                     → End of the specifed weekday: `YYYY-MM-DD 23:59:59.999999`

        :return `<'bool'>`: True if the instance is at the end
            of the specified datetime unit; Otherwise False.
        """
        if unit is None:
            return False

        # Unit: 's', 'm', 'h', 'D', 'W', 'M', 'Q', 'Y'
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 1:
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . second
            if ch0 == "s":
                return self.access_microsecond() == 999_999
            # . minute
            if ch0 == "m":
                return (
                    self.access_second() == 59 and self.access_microsecond() == 999_999
                )
            # . hour
            if ch0 == "h":
                return (
                    self.access_minute() == 59
                    and self.access_second() == 59
                    and self.access_microsecond() == 999_999
                )
            # End of time - - - - - - - - - - - - - - - - - - - - - - - - -
            if not utils.dt_is_end_of_time(self):
                return False
            # . day
            if ch0 == "D":
                return True
            # . week
            if ch0 == "W":
                return self.access_weekday() == 6
            # . month
            if ch0 == "M":
                return utils.dt_is_last_dom(self)
            # . quarter
            if ch0 == "Q":
                return utils.dt_is_last_doq(self)
            # . year
            if ch0 == "Y":
                return utils.dt_is_last_doy(self)

        # Unit: 'ms', 'us', 'ns'
        elif unit_len == 2 and str_read(unit, 1) == "s":
            ch0: cython.Py_UCS4 = str_read(unit, 0)
            # . millisecond
            if ch0 == "m":
                return self.access_microsecond() % 1000 == 999
            # . microsecond / nanosecond
            if ch0 in ("u", "n"):
                return True

        # Unit: 'min' for pandas compatibility
        elif unit_len == 3 and unit == "min":
            return self.access_second() == 59 and self.access_microsecond() == 999_999

        # End of time - - - - - - - - - - - - - - - - - - - - - - - - -
        if not utils.dt_is_end_of_time(self):
            return False

        # Month name
        val: cython.int = _parse_month(unit, None, False)
        if val != -1:
            return self.access_month() == val and utils.dt_is_last_dom(self)

        # Weekday name
        val: cython.int = _parse_weekday(unit, None, False)
        if val != -1:
            return self.access_weekday() == val

        # Invalid
        return False

    # . round / ceil / floor
    @cython.ccall
    def round(self, unit: str) -> _Pydt:
        """Perform round operation to the specified datetime unit `<'Pydt'>`.

        :param unit `<'str'>`: The datetime unit to round to, supports:
            `'D', 'h', 'm', 's', 'ms', 'us'`.
        :returns `<'Pydt'>`: The resulting datetime.

        ## Equivalent
        >>> pd.Timestamp.round()
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self.__class__,
                "round(unit)",
                "Supports: 'D', 'h', 'm', 's', 'ms' or 'us'; got None.",
            )

        # Parse unit factor
        f: cython.longlong = _parse_unit_factor(self._cls(), unit)
        if f == 1:
            return self  # exit: no change

        # Round to unit
        ori_us: cython.longlong = utils.dt_to_us(self, False)
        new_us: cython.longlong = utils.math_div_even(ori_us, f) * f
        if new_us == ori_us:
            return self  # exit: same value

        # New instance
        try:
            return utils.dt_fr_us(new_us, self.access_tzinfo(), self._cls())
        except Exception as err:
            errors.raise_argument_error(self._cls(), "round(unit)", None, err)

    @cython.ccall
    def ceil(self, unit: str) -> _Pydt:
        """Perform ceil operation to the specified datetime unit `<'Pydt'>`.

        :param unit `<'str'>`: The datetime unit to ceil to, supports:
            `'D', 'h', 'm', 's', 'ms', 'us'`.
        :returns `<'Pydt'>`: The resulting datetime.

        ## Equivalent
        >>> pandas.Timestamp.ceil()
        """
        # Parse unit factor
        f: cython.longlong = _parse_unit_factor(self._cls(), unit)
        if f == 1:
            return self  # exit: no change

        # Ceil to unit
        ori_us: cython.longlong = utils.dt_to_us(self, False)
        new_us: cython.longlong = utils.math_div_ceil(ori_us, f) * f
        if new_us == ori_us:
            return self  # exit: same value

        # New instance
        try:
            return utils.dt_fr_us(new_us, self.access_tzinfo(), self._cls())
        except Exception as err:
            errors.raise_argument_error(self._cls(), "ceil(unit)", None, err)

    @cython.ccall
    def floor(self, unit: str) -> _Pydt:
        """Perform floor operation to the specified datetime unit `<'Pydt'>`.

        :param unit `<'str'>`: The datetime unit to floor to, supports:
            `'D', 'h', 'm', 's', 'ms', 'us'`.
        :returns `<'Pydt'>`: The resulting datetime.

        ## Equivalent
        >>> pandas.Timestamp.floor()
        """
        # Parse unit factor
        f: cython.longlong = _parse_unit_factor(self._cls(), unit)
        if f == 1:
            return self  # exit: no change

        # Floor to unit
        ori_us: cython.longlong = utils.dt_to_us(self, False)
        new_us: cython.longlong = utils.math_div_floor(ori_us, f) * f
        if new_us == ori_us:
            return self  # exit: same value

        # New instance
        try:
            return utils.dt_fr_us(new_us, self.access_tzinfo(), self._cls())
        except Exception as err:
            errors.raise_argument_error(self._cls(), "floor(unit)", None, err)

    # . fsp (fractional seconds precision)
    @cython.ccall
    def fsp(self, precision: cython.int) -> _Pydt:
        """Adjust to the specified fractional seconds precision `<'Pydt'>`.

        :param precision `<'int'>`: The target fractional seconds precision (0-6).
        :returns `<'Pydt'>`: The datetime with adjusted fractional seconds precision.

        ## Example
        >>> dt = Pydt(2024, 10, 15, 0, 12, 34, 456789)
        >>> dt.fsp(3)  # Millisecond precision
        >>> 2024-10-15 00:12:34.456000
        """
        # No change
        if precision >= 6:
            return self  # exit: same value
        if precision < 0:
            errors.raise_argument_error(
                self._cls(),
                "fsp(precision)",
                "Fractional seconds precision must be "
                "between 0...6, instead got %d." % precision,
            )

        # Adjust precision
        f: cython.longlong = int(10 ** (6 - precision))  # fsp factor
        ori_us: cython.longlong = utils.dt_to_us(self, False)
        new_us: cython.longlong = utils.math_div_floor(ori_us, f) * f
        if new_us == ori_us:
            return self  # exit: same value

        # New instance
        return utils.dt_fr_us(new_us, self.access_tzinfo(), self._cls())

    # Calendar -----------------------------------------------------------------------------
    # . iso
    @cython.ccall
    def isocalendar(self) -> dict[str, int]:
        """Return the ISO calendar `<'dict'>`.

        ## Example
        >>> dt.isocalendar()
        >>> {'year': 2024, 'week': 40, 'weekday': 2}
        """
        _iso = utils.ymd_isocalendar(
            self.access_year(), self.access_month(), self.access_day()
        )
        return {"year": _iso.year, "week": _iso.week, "weekday": _iso.weekday}

    @cython.ccall
    @cython.exceptval(check=False)
    def isoyear(self) -> cython.int:
        """Return the ISO calendar year (1-10000) `<'int'>`."""
        return utils.ymd_isoyear(
            self.access_year(), self.access_month(), self.access_day()
        )

    @cython.ccall
    @cython.exceptval(check=False)
    def isoweek(self) -> cython.int:
        """Return the ISO calendar week number (1-53) `<'int'>`."""
        return utils.ymd_isoweek(
            self.access_year(), self.access_month(), self.access_day()
        )

    @cython.ccall
    @cython.exceptval(check=False)
    def isoweekday(self) -> cython.int:
        """Return the ISO calendar weekday (1=Mon...7=Sun) `<'int'>`."""
        return utils.ymd_isoweekday(
            self.access_year(), self.access_month(), self.access_day()
        )

    # . year
    @property
    def year(self) -> int:
        """The year (1-9999) `<'int'>`."""
        return datetime.datetime_year(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_year(self) -> cython.int:
        """Return the year (1-9999) `<'int'>`."""
        return datetime.datetime_year(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def is_year(self, year: cython.int) -> cython.bint:
        """Check whether is the exact `year` `<'bool'>."""
        return self.access_year() == year

    @cython.ccall
    @cython.exceptval(check=False)
    def is_leap_year(self) -> cython.bint:
        """Check whether is in a leap year `<'bool'>`."""
        return utils.is_leap_year(self.access_year())

    @cython.ccall
    @cython.exceptval(check=False)
    def is_long_year(self) -> cython.bint:
        """Check whether is in a long year `<'bool'>`.

        - Long year: maximum ISO week number is 53.
        """
        return utils.is_long_year(self.access_year())

    @cython.ccall
    @cython.exceptval(check=False)
    def leap_bt_year(self, year: cython.int) -> cython.int:
        """Compute the total number of leap years between `year` and instance `<'int'>`."""
        return utils.leaps_bt_years(self.access_year(), year)

    @cython.ccall
    @cython.exceptval(check=False)
    def days_in_year(self) -> cython.int:
        """Return the maximum number of days (365, 366) in the year `<'int'>`."""
        return utils.days_in_year(self.access_year())

    @cython.ccall
    @cython.exceptval(check=False)
    def days_bf_year(self) -> cython.int:
        """Return the number of days strictly before January 1 of year `<'int'>`."""
        return utils.days_bf_year(self.access_year())

    @cython.ccall
    @cython.exceptval(check=False)
    def day_of_year(self) -> cython.int:
        """Return the number of days since the 1st day of the year `<'int'>`."""
        return utils.day_of_year(
            self.access_year(), self.access_month(), self.access_day()
        )

    # . quarter
    @property
    def quarter(self) -> int:
        """The quarter (1-4) `<'int'>`."""
        return self.access_quarter()

    @cython.ccall
    @cython.exceptval(check=False)
    def access_quarter(self) -> cython.int:
        """Return the quarter (1-4) `<'int'>`."""
        return utils.quarter_of_month(self.access_month())

    @cython.ccall
    @cython.exceptval(check=False)
    def is_quarter(self, quarter: cython.int) -> cython.bint:
        """Check whether is the exact `quarter` `<'bool'>`."""
        return self.access_quarter() == quarter

    @cython.ccall
    @cython.exceptval(check=False)
    def days_in_quarter(self) -> cython.int:
        """Return the maximum number of days (90-92) in the quarter `<'int'>`."""
        return utils.days_in_quarter(self.access_year(), self.access_month())

    @cython.ccall
    @cython.exceptval(check=False)
    def days_bf_quarter(self) -> cython.int:
        """Return the number of days strictly before the first day
        of the calendar quarter `<'int'>`.
        """
        return utils.days_bf_quarter(self.access_year(), self.access_month())

    @cython.ccall
    @cython.exceptval(check=False)
    def day_of_quarter(self) -> cython.int:
        """Return the number of days since the 1st day of the quarter `<'int'>`."""
        return utils.day_of_quarter(
            self.access_year(), self.access_month(), self.access_day()
        )

    # . month
    @property
    def month(self) -> int:
        """The month (1-12) `<'int'>`."""
        return datetime.datetime_month(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_month(self) -> cython.int:
        """Return the month (1-12) `<'int'>`."""
        return datetime.datetime_month(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def is_month(self, month: int | str) -> cython.bint:
        """Check whether is the exact `month` `<'bool'>`.

        :param month `<'int/str'>`: Month value.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').

        :return `<'bool'>`: True if `month` is recognized and matched
            with the instance's month; Otherwise False.
        """
        return self.access_month() == _parse_month(month, None, False)

    @cython.ccall
    @cython.exceptval(check=False)
    def days_in_month(self) -> cython.int:
        """Return the maximum number of days (28-31) in the month `<'int'>`."""
        return utils.days_in_month(self.access_year(), self.access_month())

    @cython.ccall
    @cython.exceptval(check=False)
    def days_bf_month(self) -> cython.int:
        """Return the number of days strictly before the first day
        of the calendar month `<'int'>`.
        """
        return utils.days_bf_month(self.access_year(), self.access_month())

    @cython.ccall
    @cython.exceptval(check=False)
    def day_of_month(self) -> cython.int:
        """Return the number of days since the 1st day of the month `<'int'>`.

        ## Equivalent
        >>> dt.day
        """
        return self.access_day()

    @cython.ccall
    def month_name(self, locale: object = None) -> str:
        """Return the month name with specified locale `<'str'>`.

        :param locale `<'str/None'>`: The locale to use for month name. Defaults to `None`.

            - Locale determining the language in which to return the month name.
              If `None` uses English locale (`'en_US'`).
            - Use the command `locale -a` on Unix systems terminal to
              find locale language code.

        :return `<'str'>`: The month name.
        """
        if locale is None:
            locale = "en_US"
        try:
            return _format_date(self, format="MMMM", locale=locale)
        except Exception as err:
            errors.raise_argument_error(self._cls(), "month_name(locale)", None, err)

    # . weekday
    @property
    def weekday(self) -> int:
        """The weekday (0=Mon...6=Sun) `<'int'>`."""
        return self.access_weekday()

    @cython.ccall
    @cython.exceptval(check=False)
    def access_weekday(self) -> cython.int:
        """Return the weekday (0=Mon...6=Sun) `<'int'>`."""
        return utils.ymd_weekday(
            self.access_year(), self.access_month(), self.access_day()
        )

    @cython.ccall
    @cython.exceptval(check=False)
    def is_weekday(self, weekday: int | str) -> cython.bint:
        """Check whether is the exact `weekday` `<'bool'>`.

        :param weekday `<'int/str/None'>`: Weekday value.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').

        :return `<'bool'>`: True if `weekday` is recognized and matched
            with the instance's weekday; Otherwise False.
        """
        return self.access_weekday() == _parse_weekday(weekday, None, False)

    @cython.ccall
    def weekday_name(self, locale: object = None) -> str:
        """Return the weekday name with specified locale `<'str'>`.

        :param locale `<'str/None'>`: The locale to use for weekday name. Defaults to `None`.

            - Locale determining the language in which to return the weekday name.
              If `None` uses English locale (`'en_US'`).
            - Use the command `locale -a` on Unix systems terminal to
              find locale language code.

        :return `<'str'>`: The weekday name.
        """
        if locale is None:
            locale = "en_US"
        try:
            return _format_date(self, format="EEEE", locale=locale)
        except Exception as err:
            errors.raise_argument_error(self._cls(), "weekday_name(locale)", None, err)

    # . day
    @property
    def day(self) -> int:
        """The day (1-31) `<'int'>`."""
        return datetime.datetime_day(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_day(self) -> cython.int:
        """Return the day (1-31) `<'int'>`."""
        return datetime.datetime_day(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def is_day(self, day: cython.int) -> cython.bint:
        """Check whether is the exact `day` `<'bool'>`."""
        return self.access_day() == day

    # . time
    @property
    def hour(self) -> int:
        """The hour (0-23) `<'int'>`."""
        return datetime.datetime_hour(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_hour(self) -> cython.int:
        """Return the hour (0-23) `<'int'>`."""
        return datetime.datetime_hour(self)

    @property
    def minute(self) -> int:
        """The minute (0-59) `<'int'>`."""
        return datetime.datetime_minute(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_minute(self) -> cython.int:
        """Return the minute (0-59) `<'int'>`."""
        return datetime.datetime_minute(self)

    @property
    def second(self) -> int:
        """The second (0-59) `<'int'>`."""
        return datetime.datetime_second(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_second(self) -> cython.int:
        """Return the second (0-59) `<'int'>`."""
        return datetime.datetime_second(self)

    @property
    def millisecond(self) -> int:
        """The millisecond (0-999) part from microsecond `<'int'>`."""
        return self.access_millisecond()

    @cython.ccall
    @cython.exceptval(check=False)
    def access_millisecond(self) -> cython.int:
        """Return the millisecond (0-999) part from microsecond `<'int'>`."""
        return self.access_microsecond() // 1000

    @property
    def microsecond(self) -> int:
        """The microsecond (0-999999) `<'int'>`."""
        return datetime.datetime_microsecond(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_microsecond(self) -> cython.int:
        """Return the microsecond (0-999999) `<'int'>`."""
        return datetime.datetime_microsecond(self)

    # Timezone -----------------------------------------------------------------------------
    @property
    def tz_available(self) -> set[str]:
        """The available timezone names `<'set[str]'>`.

        ## Equivalent
        >>> zoneinfo.available_timezones()
        """
        return _available_timezones()

    @property
    def tz(self) -> object:
        """The timezone information `<'tzinfo/None'>`.

        - Alias of `tzinfo`
        """
        return self.access_tzinfo()

    @property
    def tzinfo(self) -> object:
        """The timezone information `<'tzinfo/None'>`."""
        return datetime.datetime_tzinfo(self)

    @cython.ccall
    def access_tzinfo(self) -> object:
        """Return the timezone information `<'tzinfo/None'>`."""
        return datetime.datetime_tzinfo(self)

    @property
    def fold(self) -> int:
        """The fold value (0 or 1) for ambiguous times `<'int'>`.

        - Use to disambiguates local times during
          daylight saving time (DST) transitions.
        """
        return datetime.datetime_fold(self)

    @cython.ccall
    @cython.exceptval(check=False)
    def access_fold(self) -> cython.int:
        """Return the fold value (0 or 1) for ambiguous times `<'int'>`.

        - Use to disambiguates local times during
          daylight saving time (DST) transitions.
        """
        return datetime.datetime_fold(self)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_local(self) -> cython.bint:
        """Check whether is in the local timezone `<'bool'>`.

        - Naive datetime always return `False`.
        """
        return self.access_tzinfo() is utils.tz_local()

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_utc(self) -> cython.bint:
        """Check whether is in the UTC timezone `<'bool'>`.

        - Naive datetime always return `False`.
        """
        return self.access_tzinfo() is utils.UTC

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_dst(self) -> cython.bint:
        """Check whether is in Dayligh Saving Time (DST) `<'bool'>.

        - Naive datetime always return `False`.
        """
        dst: datetime.timedelta = utils.dt_dst(self)
        return False if dst is None else bool(utils.td_to_us(dst))

    @cython.ccall
    def tzname(self) -> str:
        """Return the timezone name `<'str/None'>`.

        - Naive datetime always return `None`.
        """
        return utils.dt_tzname(self)

    @cython.ccall
    def utcoffset(self) -> datetime.timedelta:
        """Return the UTC offset `<'datetime.timedelta/None'>`.

        The offset is positive for timezones east of
        UTC and negative for timezones west of UTC.

        - Naive datetime always return `None`.
        """
        return utils.dt_utcoffset(self)

    @cython.ccall
    def utcoffset_seconds(self) -> object:
        """Return the UTC offset in seconds `<'int/None'>`.

        The offset is positive for timezones east of
        UTC and negative for timezones west of UTC.

        - Naive datetime always return `None`.
        """
        tz = self.access_tzinfo()
        if tz is None:
            return None
        ss: cython.int = utils.tz_utcoffset_sec(tz, self)
        return None if ss == utils.NULL_TZOFFSET else ss

    @cython.ccall
    def dst(self) -> datetime.timedelta:
        """Return the Daylight Saving Time (DST) offset `<'datetime.timedelta/None'>`.

        - This is purely informational, the DST offset has already
          been added to the UTC offset returned by 'utcoffset()'.
        - Naive datetime always return `None`.
        """
        return utils.dt_dst(self)

    @cython.ccall
    def astimezone(self, tz: datetime.tzinfo | str | None = None) -> _Pydt:
        """Convert to another timezone `<'Pydt'>`.

        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` the system `local` timezone is used.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime representing the `same` datetime
            expressed in the target timezone. For naive datetime and `tz is None`,
            `localizes` the datetime to the system local zone.
        """
        tz = utils.tz_parse(tz)
        return utils.dt_astimezone(self, tz, self._cls())

    @cython.ccall
    def tz_localize(self, tz: datetime.tzinfo | str | None) -> _Pydt:
        """Localize timezone-naive datetime to the target timezone;
        or timezone-aware datetime to timezone naive (without moving
        the date & time fields) `<'Pydt'>`.

        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` Localize to timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime localized to the target timezone.

        ## Equivalent
        >>> pandas.Timestamp.tz_localize(tz)
        """
        # Timezone-aware
        tz = utils.tz_parse(tz)
        my_tz = self.access_tzinfo()
        if my_tz is not None:
            if tz is not None:
                errors.raise_argument_error(
                    self._cls(),
                    "tz_localize(tz)",
                    "Datetime '%s' is already timezone-aware.\n"
                    "Use 'tz_convert()' or 'tz_switch()' method "
                    "to convert to the target timezone." % self,
                )
            # . localize: aware => naive
            return utils.dt_replace_tz(self, None, self._cls())

        # Timezone-naive
        if tz is None:
            return self
        # . localize: naive => aware
        return utils.dt_replace_tz(self, tz, self._cls())

    @cython.ccall
    def tz_convert(self, tz: datetime.tzinfo | str | None) -> _Pydt:
        """Convert timezone-aware datetime to another timezone `<'Pydt'>`.

        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` Convert to UTC timezone and localize to timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pydt'>`: The resulting datetime representing the `same`
            datetime expressed in the target timezone.

        ## Equivalent
        >>> pandas.Timestamp.tz_convert(tz)
        """
        # Validate
        if self.access_tzinfo() is None:
            errors.raise_argument_error(
                self._cls(),
                "tz_convert(tz)",
                "Datetime '%s' is timezone-naive.\n"
                "Use 'tz_localize()' method to localize timezone, or "
                "use 'tz_switch()' method to convert to the target "
                "timezone by providing a base timezone." % self,
            )

        # Convert: aware => None
        tz = utils.tz_parse(tz)
        if tz is None:
            return utils.dt_replace_tz(
                utils.dt_astimezone(self, utils.UTC, None), None, self._cls()
            )

        # Convert: aware => aware
        return utils.dt_astimezone(self, tz, self._cls())

    @cython.ccall
    def tz_switch(
        self,
        targ_tz: datetime.tzinfo | str | None,
        base_tz: datetime.tzinfo | str | None = None,
        naive: cython.bint = False,
    ) -> _Pydt:
        """Switch (convert) the datetime from base timezone to the target timezone `<'Pydt'>`.

        This method extends the functionality of `astimezone()` by allowing
        user to specify a base timezone for timezone-naive instances before
        converting to the target timezone.

        - If the datetime is timezone-aware, the 'base_tz' argument is `ignored`,
          and this method behaves identical to `astimezone()`: converting the
          datetime to the target timezone.
        - If the instance is timezone-naive, it first localizes the datetime
          to the `base_tz` (required), and then converts to the target timezone.

        :param targ_tz `<'tzinfo/str/None'>`: The target timezone.
        :param base_tz `<'tzinfo/str/None'>`: The base timezone for timezone-naive datetime. Defaults to `None`.
        :param naive `<'bool'>`: If 'True', returns timezone-naive instance after conversion. Defaults to `False`.
        :returns `<'Pydt'>`: The resulting datetime representing the `same` datetime
            expressed in the target timezone; optionally timezone-naive.
        """
        # Timezone-aware
        to_tz = utils.tz_parse(targ_tz)
        my_tz = self.access_tzinfo()
        if my_tz is not None:
            # . target timezone is None
            if to_tz is None:
                return utils.dt_replace_tz(self, None, self._cls())
            # . target timezone is my_tz
            elif to_tz is my_tz:
                if naive:
                    return utils.dt_replace_tz(self, None, self._cls())
                else:
                    return self  # exit
            # . my_tz => target timezone
            else:
                if naive:
                    dt = utils.dt_astimezone(self, to_tz, None)
                    return utils.dt_replace_tz(dt, None, self._cls())
                else:
                    return utils.dt_astimezone(self, to_tz, self._cls())

        # Timezone-naive
        # . target timezone is None
        if to_tz is None:
            return self  # exit
        # . base is None
        base_tz = utils.tz_parse(base_tz)
        if base_tz is None:
            errors.raise_argument_error(
                self._cls(),
                "tz_switch(...)",
                "Datetime '%s' is timezone-naive.\n"
                "Cannot convert timezone-naive datetime to the "
                "target timezone without a base timezone (base_tz)." % self,
            )
        # . base timezone is target timezone
        if base_tz is to_tz:
            if naive:
                return self  # exit
            else:
                return utils.dt_replace_tz(self, to_tz, self._cls())
        # . localize to base, then convert to target timezone
        else:
            dt = utils.dt_replace_tz(self, base_tz, None)
            if naive:
                dt = utils.dt_astimezone(dt, to_tz, None)
                return utils.dt_replace_tz(dt, None, self._cls())
            else:
                return utils.dt_astimezone(dt, to_tz, self._cls())

    # Arithmetic ---------------------------------------------------------------------------
    @cython.ccall
    def add(
        self,
        years: cython.int = 0,
        quarters: cython.int = 0,
        months: cython.int = 0,
        weeks: cython.int = 0,
        days: cython.int = 0,
        hours: cython.int = 0,
        minutes: cython.int = 0,
        seconds: cython.int = 0,
        milliseconds: cython.int = 0,
        microseconds: cython.int = 0,
    ) -> _Pydt:
        """Add relative delta to the datetime `<'Pydt'>`.

        :param years `<'int'>`: Relative years. Defaults to `0`.
        :param quarters `<'int'>`: Relative quarters (3 months). Defaults to `0`.
        :param months `<'int'>`: Relative months. Defaults to `0`.
        :param weeks `<'int'>`: Relative weeks (7 days). Defaults to `0`.
        :param days `<'int'>`: Relative days. Defaults to `0`.
        :param hours `<'int'>`: Relative hours. Defaults to `0`.
        :param minutes `<'int'>`: Relative minutes. Defaults to `0`.
        :param seconds `<'int'>`: Relative seconds. Defaults to `0`.
        :param milliseconds `<'int'>`: Relative milliseconds (`1000 us`). Defaults to `0`.
        :param microseconds `<'int'>`: Relative microseconds. Defaults to `0`.
        :returns `<'Pydt'>`: The resulting datetime after adding the relative delta.
        """
        try:
            # fmt: off
            return utils.dt_add_delta(self,
                years, quarters, months, weeks, days,
                hours, minutes, seconds, milliseconds, microseconds,
                -1 ,-1, -1, -1, -1,-1, -1, -1, -1, self._cls()
            )
            # fmt: on
        except Exception as err:
            errors.raise_argument_error(self._cls(), "add(...)", None, err)

    @cython.ccall
    def sub(
        self,
        years: cython.int = 0,
        quarters: cython.int = 0,
        months: cython.int = 0,
        weeks: cython.int = 0,
        days: cython.int = 0,
        hours: cython.int = 0,
        minutes: cython.int = 0,
        seconds: cython.int = 0,
        milliseconds: cython.int = 0,
        microseconds: cython.int = 0,
    ) -> _Pydt:
        """Subtract relative delta from the datetime `<'Pydt'>`.

        :param years `<'int'>`: Relative years. Defaults to `0`.
        :param quarters `<'int'>`: Relative quarters (3 months). Defaults to `0`.
        :param months `<'int'>`: Relative months. Defaults to `0`.
        :param weeks `<'int'>`: Relative weeks (7 days). Defaults to `0`.
        :param days `<'int'>`: Relative days. Defaults to `0`.
        :param hours `<'int'>`: Relative hours. Defaults to `0`.
        :param minutes `<'int'>`: Relative minutes. Defaults to `0`.
        :param seconds `<'int'>`: Relative seconds. Defaults to `0`.
        :param milliseconds `<'int'>`: Relative milliseconds (`1000 us`). Defaults to `0`.
        :param microseconds `<'int'>`: Relative microseconds. Defaults to `0`.
        :returns `<'Pydt'>`: The resulting datetime after subtracting the relative delta.
        """
        try:
            # fmt: off
            return utils.dt_add_delta(self,
                -years, -quarters, -months, -weeks, -days,
                -hours, -minutes, -seconds, -milliseconds, -microseconds,
                -1 ,-1, -1, -1, -1,-1, -1, -1, -1, self._cls()
            )
            # fmt: on
        except Exception as err:
            errors.raise_argument_error(self._cls(), "sub(...)", None, err)

    @cython.ccall
    def diff(
        self,
        dtobj: object,
        unit: str,
        absolute: cython.bint = False,
        inclusive: str = "one",
    ) -> cython.longlong:
        """Compute the delta difference between the instance and another datetime `<'int'>`.

        The delta is computed in the specified datetime 'unit' and
        adjusted based on the `inclusive` argument to determine the
        inclusivity of the start and end times.

        :param dtobj `<'object'>`: A datetime-like object, supports:

            - `<'str'>`                 → parses into datetime.
            - `<'datetime.datetime'>`   → accepts `as-is`.
            - `<'datetime.date'>`       → converts to timezone-naive datetime with the same date fields.
            - `<'int/float'>`           → interprets as `seconds since Unix epoch` and converts to timezone-naive datetime
                                          (fractional seconds as microseconds).
            - `<'np.datetime64'>`       → converts to timezone-naive datetime; resolution finer than microseconds is truncated.

        :param unit `<'str'>`: The unit to compute the delta difference.
            Supports: `'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us'`.

        :param absolute `<'bool'>`: If 'True', compute the absolute difference. Defaults to `False`.

        :param inclusive `<'str'>`: Specifies the inclusivity of the start and end times. Defaults to `'one'`.

            - `'one'`     → Include either the start or end time → `(a - b)`
            - `'both'`:   → Include both the start and end times → `(a - b) + 1 (offset)`
            - `'neither'` → Exclude both the start and end times → `(a - b) - 1 (offset)`

        :returns `<'int'>`: The delta difference between the instance and `dtobj`
            in the specified `unit`, adjusted for inclusivity.
        """
        # Parse 'dtobj' to datetime
        try:
            dt: datetime.datetime = _parse_obj(
                dtobj, None, True, False, False, True, None, None
            )
        except Exception as err:
            errors.raise_argument_error(self._cls(), "diff(dtobj, ...)", None, err)
            return 0  # unreachable: suppress compiler warning

        # Check timezone parity
        my_tz = self.access_tzinfo()
        dt_tz = dt.tzinfo
        my_aware: cython.bint = my_tz is not None
        dt_aware: cython.bint = dt_tz is not None
        if my_aware != dt_aware:
            errors.raise_error(
                errors.MixedTimezoneError,
                self._cls(),
                "diff(dtobj, ...)",
                "Cannot compare naive and aware datetimes:\n"
                "  - datetime1: '%s' %s\n"
                "  - datetime2: '%s' %s" % (self, type(self), dt, type(dt)),
            )

        # Handle inclusive
        if inclusive == "both":
            incl_off: cython.int = 1
        elif inclusive == "one":
            incl_off: cython.int = 0
        elif inclusive == "neither":
            incl_off: cython.int = -1
        else:
            errors.raise_argument_error(
                self._cls(),
                "diff(..., inclusive)",
                "Supports: 'one', 'both' or 'neither'; got '%s'." % inclusive,
            )
            return 0  # unreachable: suppress compiler warning

        # Validate delta 'unit'
        if unit is None:
            errors.raise_argument_error(
                self.__class__,
                "diff(..., unit)",
                "Delta 'unit' cannot be None.",
            )
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 0:
            errors.raise_argument_error(
                self.__class__,
                "diff(..., unit)",
                "Delta 'unit' cannot be an empty string.",
            )

        # Compute difference
        try:
            # . convert to int64[W] on monday
            if unit_len == 1 and str_read(unit, 0) == "W":
                my_val: cython.longlong = utils.dt_as_epoch_W_iso(self, 1, my_aware)
                dt_val: cython.longlong = utils.dt_as_epoch_W_iso(dt, 1, dt_aware)
            # . convert to int64[unit]
            else:
                my_val: cython.longlong = utils.dt_as_epoch(self, unit, my_aware)
                dt_val: cython.longlong = utils.dt_as_epoch(dt, unit, dt_aware)
        except Exception as err:
            errors.raise_argument_error(self._cls(), "diff(..., unit)", None, err)
            return 0  # unreachable: suppress compiler warning
        # . compute relative delta
        delta: cython.longlong = my_val - dt_val

        # Adjust for inclusivity
        # . absolute = True
        if absolute:
            delta = (-delta if delta < 0 else delta) + incl_off
        # . absolute = False & inclusive offset
        elif incl_off != 0:
            delta = delta - incl_off if delta < 0 else delta + incl_off

        # Finished
        return delta

    def __add__(self, o: object) -> Self:
        # timedelta
        if utils.is_td(o):
            return utils.dt_add(
                self,
                datetime.timedelta_days(o),
                datetime.timedelta_seconds(o),
                datetime.timedelta_microseconds(o),
                self._cls(),
            )
        # np.timedelta64
        if utils.is_td64(o):
            o = utils.td64_to_td(o)
            return utils.dt_add(
                self,
                datetime.timedelta_days(o),
                datetime.timedelta_seconds(o),
                datetime.timedelta_microseconds(o),
                self._cls(),
            )
        # unsupported
        return NotImplemented

    def __radd__(self, o: object) -> Self:
        # timedelta
        if utils.is_td(o):
            return utils.dt_add(
                self,
                datetime.timedelta_days(o),
                datetime.timedelta_seconds(o),
                datetime.timedelta_microseconds(o),
                self._cls(),
            )
        # np.timedelta64
        if utils.is_td64(o):
            o = utils.td64_to_td(o)
            return utils.dt_add(
                self,
                datetime.timedelta_days(o),
                datetime.timedelta_seconds(o),
                datetime.timedelta_microseconds(o),
                self._cls(),
            )
        # unsupported
        return NotImplemented

    def __sub__(self, o: object) -> Self | datetime.timedelta:
        # timedelta
        if utils.is_td(o):
            return utils.dt_add(
                self,
                -datetime.timedelta_days(o),
                -datetime.timedelta_seconds(o),
                -datetime.timedelta_microseconds(o),
                self._cls(),
            )
        # np.timedelta64
        elif utils.is_td64(o):
            o = utils.td64_to_td(o)
            return utils.dt_add(
                self,
                -datetime.timedelta_days(o),
                -datetime.timedelta_seconds(o),
                -datetime.timedelta_microseconds(o),
                self._cls(),
            )
        # datetime
        elif utils.is_dt(o):
            pass
        # date
        elif utils.is_date(o):
            o = utils.dt_fr_date(o, None, None)
        # str
        elif isinstance(o, str):
            try:
                o = _parse_obj(o, None, True, False, False, True, None, None)
            except Exception:
                return NotImplemented
        # np.datetime64
        elif utils.is_dt64(o):
            o = utils.dt64_to_dt(o, None, None)
        # unsupported
        else:
            return NotImplemented
        #: from here on, 'o' is datetime

        # Check timezone parity
        m_tz = self.access_tzinfo()
        o_tz = datetime.datetime_tzinfo(o)
        m_aware: cython.bint = m_tz is not None
        o_aware: cython.bint = o_tz is not None
        if m_aware != o_aware:
            errors.raise_error(
                errors.MixedTimezoneError,
                self._cls(),
                "diff(dtobj, ...)",
                "Cannot subtract naive and aware datetimes:\n"
                "  - datetime1: '%s' %s\n"
                "  - datetime2: '%s' %s" % (self, type(self), o, type(o)),
            )

        # Compute delta
        m_us: cython.longlong = utils.dt_to_us(self, m_aware)
        o_us: cython.longlong = utils.dt_to_us(o, o_aware)
        return utils.td_fr_us(m_us - o_us, None)

    # Comparison ---------------------------------------------------------------------------
    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_past(self) -> cython.bint:
        """Check whether is in the past `<'bool'>`.

        ## Equivalent
        >>> self < datetime.datetime.now(self.tzinfo)
        """
        return self < utils.dt_now(self.access_tzinfo())

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_future(self) -> cython.bint:
        """Check whether is in the future `<'bool'>`.

        ## Equivalent
        >>> self > datetime.datetime.now(self.tzinfo)
        """
        return self > utils.dt_now(self.access_tzinfo())

    # Representation -----------------------------------------------------------------------
    def __repr__(self) -> str:
        yy: cython.int = self.access_year()
        mm: cython.int = self.access_month()
        dd: cython.int = self.access_day()
        hh: cython.int = self.access_hour()
        mi: cython.int = self.access_minute()
        ss: cython.int = self.access_second()
        us: cython.int = self.access_microsecond()
        tz: object = self.access_tzinfo()
        fd: cython.int = self.access_fold()

        r: str
        if us == 0:
            r = "%d, %d, %d, %d, %d, %d" % (yy, mm, dd, hh, mi, ss)
        else:
            r = "%d, %d, %d, %d, %d, %d, %d" % (yy, mm, dd, hh, mi, ss, us)
        if tz is not None:
            r += ", tzinfo=%r" % tz
        if fd == 1:
            r += ", fold=1"

        return "%s(%s)" % (self._cls().__name__, r)

    def __str__(self) -> str:
        return self.isoformat(" ")

    def __format__(self, fmt: str) -> str:
        if fmt is None or str_len(fmt) == 0:
            return self.isoformat(" ")
        else:
            return self.strftime(fmt)

    def __hash__(self) -> int:
        return datetime.datetime.__hash__(self)

    def __copy__(self) -> Self:
        return utils.dt_new(
            self.access_year(),
            self.access_month(),
            self.access_day(),
            self.access_hour(),
            self.access_minute(),
            self.access_second(),
            self.access_microsecond(),
            self.access_tzinfo(),
            self.access_fold(),
            self._cls(),
        )

    def __deepcopy__(self, _: dict) -> Self:
        return utils.dt_new(
            self.access_year(),
            self.access_month(),
            self.access_day(),
            self.access_hour(),
            self.access_minute(),
            self.access_second(),
            self.access_microsecond(),
            self.access_tzinfo(),
            self.access_fold(),
            self._cls(),
        )

    # Pickle -------------------------------------------------------------------------------
    def __reduce__(self) -> str | tuple:
        return datetime.datetime.__reduce__(self)

    def __reduce_ex__(self, protocol: object, /) -> str | tuple:
        return datetime.datetime.__reduce_ex__(self, protocol)


class Pydt(_Pydt):
    """A drop-in replacement for the standard `<'datetime.datetime'>`
    class, providing additional functionalities for more convenient
    datetime operations:

    - 1. rich calendar arithmetic (to_month, to_start_of, to_first_of, etc.)
    - 2. powerful parsing (parse, ISO, ordinal, isoweek, etc.)
    - 3. explicit, safe timezone conversion with fold & DST normalization.
    """

    def __new__(
        cls,
        year: int = 1,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: datetime.tzinfo | str | None = None,
        *,
        fold: int = 1,
    ) -> Pydt:
        """A drop-in replacement for the standard `<'datetime.datetime'>`
        class, providing additional functionalities for more convenient
        datetime operations:

        - 1. rich calendar arithmetic (to_month, to_start_of, to_first_of, etc.)
        - 2. powerful parsing (parse, ISO, ordinal, isoweek, etc.)
        - 3. explicit, safe timezone conversion with fold & DST normalization.

        :param year `<'int'>`: Year value (1-9999). Defaults to `1`.
        :param month `<'int'>`: Month value (1-12). Defaults to `1`.
        :param day `<'int'>`: Day value (1-31). Defaults to `1`.
        :param hour `<'int'>`: Hour value (0-23). Defaults to `0`.
        :param minute `<'int'>`: Minute value (0-59). Defaults to `0`.
        :param second `<'int'>`: Second value (0-59). Defaults to `0`.
        :param microsecond `<'int'>`: Microsecond value (0-999999). Defaults to `0`.
        :param tzinfo `<'tzinfo/str/None'>`: The timezone. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param fold `<'int'>`: Fold value (0 or 1) for ambiguous times. Defaults to `1`.
        """
        return cls._new(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
            tzinfo=tzinfo,
            fold=fold,
        )
