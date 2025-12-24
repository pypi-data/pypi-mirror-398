# cython: language_level=3
# cython: wraparound=False
# cython: boundscheck=False

from __future__ import annotations

# Cython imports
import cython
from cython.cimports import numpy as np  # type: ignore
from cython.cimports.cpython import datetime  # type: ignore
from cython.cimports.cytimes import errors, utils  # type: ignore

np.import_array()
np.import_umath()
datetime.import_datetime()

# Python imports
import datetime
from typing_extensions import Self
from dateutil.relativedelta import relativedelta
from cytimes import errors, utils

__all__ = ["Delta"]


# Contants ------------------------------------------------------------------------------------
# . weekday
_WEEKDAY_REPRS: tuple[str, ...] = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")


# Utils ---------------------------------------------------------------------------------------
@cython.cfunc
@cython.inline(True)
def _delta_fr_relativedelta(rd: relativedelta) -> Delta:
    """(internal) Build `Delta` from `dateutil.relativedelta` `<'Delta'>`.

    :param rd `<'relativedelta'>`: Source relativedelta.
    :returns `<'Delta'>`: The resulting `Delta`.
    :raises `<'TypeError'>`: If the `rd` is not an instance of relativedelta.

    ## Notice
    The `weekday.n` from `relativedelta` is ignored.
    """
    if not isinstance(rd, relativedelta):
        errors.raise_error(
            errors.InvalidRelativeDelta,
            Delta,
            "from_relativedelta(rd)",
            "Expects an instance of 'dateutil.relativedelta', "
            "instead got %s." % type(rd),
        )
    rd = rd.normalized()
    return Delta(
        rd.years,
        0,
        rd.months,
        0,
        rd.days,
        rd.hours,
        rd.minutes,
        rd.seconds,
        0,
        rd.microseconds,
        rd.year if rd.year is not None else -1,
        rd.month if rd.month is not None else -1,
        rd.day if rd.day is not None else -1,
        rd.weekday.weekday if rd.weekday is not None else -1,
        rd.hour if rd.hour is not None else -1,
        rd.minute if rd.minute is not None else -1,
        rd.second if rd.second is not None else -1,
        -1,
        rd.microsecond if rd.microsecond is not None else -1,
    )


# Delta ---------------------------------------------------------------------------------------
@cython.cclass
class Delta:
    """Represent the difference between two datetime objects at both relative
    and absolute levels. The `<'Delta'>` class supports arithmetic operations
    and is compatible with various datetime and timedelta types.
    """

    _years: cython.int
    _months: cython.int
    _days: cython.longlong
    _hours: cython.int
    _minutes: cython.int
    _seconds: cython.int
    _microseconds: cython.int
    _year: cython.int
    _month: cython.int
    _day: cython.int
    _weekday: cython.int
    _hour: cython.int
    _minute: cython.int
    _second: cython.int
    _microsecond: cython.int
    _hashcode: cython.Py_ssize_t

    def __init__(
        self,
        years: cython.int = 0,
        quarters: cython.int = 0,
        months: cython.int = 0,
        weeks: cython.int = 0,
        days: cython.longlong = 0,
        hours: cython.longlong = 0,
        minutes: cython.longlong = 0,
        seconds: cython.longlong = 0,
        milliseconds: cython.longlong = 0,
        microseconds: cython.longlong = 0,
        year: cython.int = -1,
        month: cython.int = -1,
        day: cython.int = -1,
        weekday: cython.int = -1,
        hour: cython.int = -1,
        minute: cython.int = -1,
        second: cython.int = -1,
        millisecond: cython.int = -1,
        microsecond: cython.int = -1,
    ):
        """The difference between two datetime objects at both relative
        and absolute levels. The `<'Delta'>`class supports arithmetic
        operations and is compatible with various datetime and timedelta
        types.

        ## Absolute Deltas (Replace specified fields)

        :param year `<'int'>`: Absolute year. Defaults to `SENTINEL` (no change).
        :param month `<'int'>`: Absolute month. Defaults to `SENTINEL` (no change).
        :param day `<'int'>`: Absolute day. Defaults to `SENTINEL` (no change).
        :param weekday `<'int'>`: Absolute weekday (0=Mon...6=Sun). Defaults to `SENTINEL` (no change).
        :param hour `<'int'>`: Absolute hour. Defaults to `SENTINEL` (no change).
        :param minute `<'int'>`: Absolute minute. Defaults to `SENTINEL` (no change).
        :param second `<'int'>`: Absolute second. Defaults to `SENTINEL` (no change).
        :param millisecond `<'int'>`: Absolute millisecond. Defaults to `SENTINEL` (no change).
            Overrides `microsecond` millisecond part if both are provided.
        :param microsecond `<'int'>`: Absolute microsecond. Defaults to `SENTINEL` (no change).

        ## Relative Deltas (Add to specified fields)

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

        ## Arithmetic Operations
        - Addition (`+`):
            - With datetime instance or subclass (`datetime.datetime`, `cytimes.Pydt`, `pandas.Timestamp`, etc):
                - Applies absolute deltas first (excluding 'weekday'), then adds relative deltas.
                - Adjusts the Y/M/D to the absolute 'weekday' if specified.
                - Returns the original subclass when possible, or fallback to `<'datetime.datetime'>`.
            - With date instance or subclass (`datetime.date`, `pendulum.Date`, etc):
                - Similar to datetime addition, returns the original subclass
                  when possible, or fallback to `<'datetime.date'>`.
            - With delta object (`datetime.timedelta`, `cytimes.Delta`, `pandas.Timedelta`, etc):
                - Sums corresponding relative delta fields of both objects.
                - For delta objects with absolute delta fields (`cytimes.Delta`, `dateutil.relativedelta`),
                  the right operand's absolute values overwrite the left's.
                - Returns `<'cytimes.Delta'>`.

        - Subtraction (`-`):
            - With datetime instance or subclass (`datetime.datetime`, `cytimes.Pydt`, `pandas.Timestamp`, etc):
                - Only support `RIGHT` operand (i.e., datetime - Delta).
                - Similar to addition, but subtracts the relative deltas instead.
                - Returns the original subclass when possible, or fallback to `<'datetime.datetime'>`.
            - With date instance or subclass (`datetime.date`, `pendulum.Date`, etc):
                - Only support `RIGHT` operand (i.e., date - Delta).
                - Similar to datetime subtraction, returns the original subclass
                  when possible, or fallback to `<'datetime.date'>`.
            - With delta object (`datetime.timedelta`, `cytimes.Delta`, `pandas.Timedelta`, etc):
                - Subtracts corresponding relative delta fields (left - right).
                - For delta objects with absolute delta fields (`cytimes.Delta`, `dateutil.relativedelta`),
                  the left operand's absolute values are kept.
                - Returns `<'cytimes.Delta'>`.

        - Negation and Absolute Value:
            - `-Delta` negates the relative delta fields.
            - `abs(Delta)` converts the relative delta fields to absolute value.
            - Absolute delta fields remain unchanged.
            - Returns `<'cytimes.Delta'>`.

        ## Compatibility with `relativedelta`
        - Supports direct addition and subtraction with `<'relativedelta'>`,
          returns `<'cytimes.Delta'>`.
        - Arithmetic operations yield equivalent results when `relativedelta`'s
          `weekday` is `None`.

        ## Compatibility with `np.datetime64/np.timedelta64`
        - Supports left operand addition and subtraction with `numpy.timedelta64`
          (i.e., Delta - timedelta64), returns `<'cytimes.Delta'>`.
        - Supports left operand addition with `numpy.datetime64`
          (i.e., Delta + datetime64), returns `<'datetime.datetime'>`.
        - Resolution is limited to microseconds; higher resolutions are truncated.
        """
        # Relative delta
        q: cython.longlong
        r: cython.longlong
        # . normalize microseconds
        microseconds += milliseconds * 1_000
        if not 0 <= microseconds < 1_000_000:
            with cython.cdivision(True):
                q = microseconds / 1_000_000
                r = microseconds % 1_000_000
            if r < 0:
                q -= 1
                r += 1_000_000
            seconds += q
            microseconds = r
        self._microseconds = microseconds
        # . normalize seconds
        if not 0 <= seconds < 60:
            with cython.cdivision(True):
                q = seconds / 60
                r = seconds % 60
            if r < 0:
                q -= 1
                r += 60
            minutes += q
            seconds = r
        self._seconds = seconds
        # . normalize minutes
        if not 0 <= minutes < 60:
            with cython.cdivision(True):
                q = minutes / 60
                r = minutes % 60
            if r < 0:
                q -= 1
                r += 60
            hours += q
            minutes = r
        self._minutes = minutes
        # . normalize hours
        if not 0 <= hours < 24:
            with cython.cdivision(True):
                q = hours / 24
                r = hours % 24
            if r < 0:
                q -= 1
                r += 24
            days += q
            hours = r
        self._hours = hours
        # . days
        self._days = days + weeks * 7
        # . normalize months
        months += quarters * 3
        if not 0 <= months < 12:
            with cython.cdivision(True):
                q = months / 12
                r = months % 12
            if r < 0:
                q -= 1
                r += 12
            years += q
            months = r
        self._months = months
        # . years
        self._years = years

        # Absolute delta
        self._year = min(year, 9_999) if year > 0 else -1
        self._month = min(month, 12) if month > 0 else -1
        self._day = min(day, 31) if day > 0 else -1
        self._weekday = min(weekday, 6) if weekday >= 0 else -1
        self._hour = min(hour, 23) if hour >= 0 else -1
        self._minute = min(minute, 59) if minute >= 0 else -1
        self._second = min(second, 59) if second >= 0 else -1
        self._microsecond = utils.combine_absolute_ms_us(millisecond, microsecond)

        # Initiate hashcode
        self._hashcode = -1

    @classmethod
    def from_relativedelta(cls, rd: relativedelta) -> Delta:
        """Build `Delta` from `dateutil.relativedelta` `<'Delta'>`.

        :param rd `<'relativedelta'>`: Source relativedelta.
        :returns `<'Delta'>`: The resulting `Delta`.
        :raises `<'TypeError'>`: If the `rd` is not an instance of relativedelta.

        ## Notice
        The `weekday.n` from `relativedelta` is ignored.
        """
        return _delta_fr_relativedelta(rd)

    # Property: relative delta -----------------------------------------------
    @property
    def years(self) -> int:
        """The relative years `<'int'>`."""
        return self._years

    @property
    def months(self) -> int:
        """The relative months `<'int'>`."""
        return self._months

    @property
    def days(self) -> int:
        """The relative days `<'int'>`."""
        return self._days

    @property
    def hours(self) -> int:
        """The relative hours `<'int'>`."""
        return self._hours

    @property
    def minutes(self) -> int:
        """The relative minutes `<'int'>`."""
        return self._minutes

    @property
    def seconds(self) -> int:
        """The relative seconds `<'int'>`."""
        return self._seconds

    @property
    def microseconds(self) -> int:
        """The relative microseconds `<'int'>`."""
        return self._microseconds

    # Properties: absolute delta ---------------------------------------------
    @property
    def year(self) -> int | None:
        """The absolute year `<'int/None'>`."""
        return None if self._year == -1 else self._year

    @property
    def month(self) -> int | None:
        """The absolute month `<'int/None'>`."""
        return None if self._month == -1 else self._month

    @property
    def day(self) -> int | None:
        """The absolute day `<'int/None'>`."""
        return None if self._day == -1 else self._day

    @property
    def weekday(self) -> int | None:
        """The absolute weekday (0=Mon...6=Sun) `<'int/None'>`."""
        return None if self._weekday == -1 else self._weekday

    @property
    def hour(self) -> int | None:
        """The absolute hour `<'int/None'>`."""
        return None if self._hour == -1 else self._hour

    @property
    def minute(self) -> int | None:
        """The absolute minute `<'int/None'>`."""
        return None if self._minute == -1 else self._minute

    @property
    def second(self) -> int | None:
        """The absolute second `<'int/None'>`."""
        return None if self._second == -1 else self._second

    @property
    def microsecond(self) -> int | None:
        """The absolute microsecond `<'int/None'>`."""
        return None if self._microsecond == -1 else self._microsecond

    # Arithmetic: addition ---------------------------------------------------
    def __add__(self, o: object) -> object:
        """Left addition `self + o`.

        - Addition with datetime instance or subclass (`datetime.datetime`, `cytimes.Pydt`, `pandas.Timestamp`, etc):
            - Applies absolute deltas first (excluding 'weekday'), then adds relative deltas.
            - Adjusts the Y/M/D to the absolute 'weekday' if specified.
            - Returns the original subclass when possible, or fallback to `<'datetime.datetime'>`.

        - Addition with date instance or subclass (`datetime.date`, `pendulum.Date`, etc):
            - Similar to datetime addition, returns the original subclass when possible,
              or fallback to `<'datetime.date'>`.

        - Addition with delta object (`datetime.timedelta`, `cytimes.Delta`, `pandas.Timedelta`, etc):
            - Sums corresponding relative delta fields of both objects.
            - For delta objects with absolute delta fields (`cytimes.Delta`, `dateutil.relativedelta`),
              the right operand's absolute values overwrite the left's.
            - Returns `<'cytimes.Delta'>`.
        """
        # . common
        if utils.is_dt(o):
            return self._add_datetime(o)
        if utils.is_date(o):
            return self._add_date(o)
        if isinstance(o, Delta):
            return self._add_delta(o)
        if utils.is_td(o):
            return self._add_timedelta(o)
        if isinstance(o, relativedelta):
            return self._add_delta(_delta_fr_relativedelta(o))
        # . uncommon
        if utils.is_dt64(o):
            return self._add_datetime(utils.dt64_to_dt(o, None, None))
        if utils.is_td64(o):
            return self._add_timedelta(utils.td64_to_td(o, None))
        # . unsupported
        return NotImplemented

    @cython.cfunc
    @cython.inline(True)
    def _add_date(self, o: datetime.date) -> datetime.date:
        """(internal) Left addition with `datetime.date` instance or subclass.
        Returns the original subclass when possible, or fallback to `<'datetime.date'>`.

        ## Concept
        >>> self + date
        """
        return utils.date_add_delta(
            o,
            self._years,
            0,
            self._months,
            0,
            self._days,
            self._hours,
            self._minutes,
            self._seconds,
            0,
            self._microseconds,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
            None if utils.is_date_exact(o) else o.__class__,
        )

    @cython.cfunc
    @cython.inline(True)
    def _add_datetime(self, o: datetime.datetime) -> datetime.datetime:
        """(internal) Left addition with `datetime.datetime` instance or subclass.
        Returns the original subclass when possible, or fallback to `<'datetime.datetime'>`.

        ## Concept
        >>> self + datetime
        """
        return utils.dt_add_delta(
            o,
            self._years,
            0,
            self._months,
            0,
            self._days,
            self._hours,
            self._minutes,
            self._seconds,
            0,
            self._microseconds,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
            None if utils.is_dt_exact(o) else o.__class__,
        )

    @cython.cfunc
    @cython.inline(True)
    def _add_timedelta(self, o: datetime.timedelta) -> Delta:
        """(internal) Left addition with `datetime.timedelta` instance or subclass.
        Returns `<'Delta'>`.

        ## Concept
        >>> self + timedelta
        """
        return Delta(
            self._years,
            0,
            self._months,
            0,
            self._days + o.day,
            self._hours,
            self._minutes,
            self._seconds + o.second,
            0,
            self._microseconds + o.microsecond,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
        )

    @cython.cfunc
    @cython.inline(True)
    def _add_delta(self, o: Delta) -> Delta:
        """(internal) Left addition with another `Delta` instance. Returns `<'Delta'>`.

        ## Concept
        >>> self + delta
        """
        return Delta(
            o._years + self._years,
            0,
            o._months + self._months,
            0,
            o._days + self._days,
            o._hours + self._hours,
            o._minutes + self._minutes,
            o._seconds + self._seconds,
            0,
            o._microseconds + self._microseconds,
            o._year if o._year != -1 else self._year,
            o._month if o._month != -1 else self._month,
            o._day if o._day != -1 else self._day,
            o._weekday if o._weekday != -1 else self._weekday,
            o._hour if o._hour != -1 else self._hour,
            o._minute if o._minute != -1 else self._minute,
            o._second if o._second != -1 else self._second,
            -1,
            o._microsecond if o._microsecond != -1 else self._microsecond,
        )

    # Arithmetic: right addition ---------------------------------------------
    def __radd__(self, o: object) -> object:
        """Right addition `o + self`.

        - Addition with datetime instance or subclass (`datetime.datetime`, `cytimes.Pydt`, `pandas.Timestamp`, etc):
            - Applies absolute deltas first (excluding 'weekday'), then adds relative deltas.
            - Adjusts the Y/M/D to the absolute 'weekday' if specified.
            - Returns the original subclass when possible, or fallback to `<'datetime.datetime'>`.

        - Addition with date instance or subclass (`datetime.date`, `pendulum.Date`, etc):
            - Similar to datetime addition, returns the original subclass when possible,
              or fallback to `<'datetime.date'>`.

        - Addition with delta object (`datetime.timedelta`, `cytimes.Delta`, `pandas.Timedelta`, etc):
            - Sums corresponding relative delta fields of both objects.
            - For delta objects with absolute delta fields (`cytimes.Delta`, `dateutil.relativedelta`),
              the right operand's absolute values overwrite the left's.
            - Returns `<'cytimes.Delta'>`.
        """
        # . common
        if utils.is_dt(o):
            return self._add_datetime(o)
        if utils.is_date(o):
            return self._add_date(o)
        if utils.is_td(o):
            return self._add_timedelta(o)
        if isinstance(o, relativedelta):
            return _delta_fr_relativedelta(o)._add_delta(self)
        # . uncommon
        # TODO: numpy datetime-like object
        # np.datetime64 and np.timedelta64 are converted to
        # datetime and timedelta or integer [ns] before reaching
        if utils.is_dt64(o):
            return self._add_datetime(utils.dt64_to_dt(o, None, None))
        if utils.is_td64(o):
            return self._add_timedelta(utils.td64_to_td(o, None))
        # . unsupported
        return NotImplemented

    # Arithmetic: subtraction ------------------------------------------------
    def __sub__(self, o: object) -> Self:
        """Left subtraction `self - o`.

        - Subtraction with delta object (`datetime.timedelta`, `cytimes.Delta`, `pandas.Timedelta`, etc):
            - Subtracts corresponding relative delta fields (left - right).
            - For delta objects with absolute delta fields (`cytimes.Delta`, `dateutil.relativedelta`),
              the left operand's absolute values are kept.
            - Returns `<'cytimes.Delta'>`.
        """
        # . common
        if isinstance(o, Delta):
            return self._sub_delta(o)
        if utils.is_td(o):
            return self._sub_timedelta(o)
        if isinstance(o, relativedelta):
            return self._sub_delta(_delta_fr_relativedelta(o))
        # . uncommon
        if utils.is_td64(o):
            return self._sub_timedelta(utils.td64_to_td(o, None))
        # . unsupported
        return NotImplemented

    @cython.cfunc
    @cython.inline(True)
    def _sub_timedelta(self, o: datetime.timedelta) -> Delta:
        """(internal) Left subtraction with `datetime.timedelta` instance or subclass.
        Returns `<'Delta'>`.

        ## Concept
        >>> self - timedelta
        """
        return Delta(
            self._years,
            0,
            self._months,
            0,
            self._days - o.day,
            self._hours,
            self._minutes,
            self._seconds - o.second,
            0,
            self._microseconds - o.microsecond,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
        )

    @cython.cfunc
    @cython.inline(True)
    def _sub_delta(self, o: Delta) -> Delta:
        """(internal) Left subtraction with another `Delta` instance. Returns `<'Delta'>`.

        ## Concept
        >>> self - delta
        """
        return Delta(
            self._years - o._years,
            0,
            self._months - o._months,
            0,
            self._days - o._days,
            self._hours - o._hours,
            self._minutes - o._minutes,
            self._seconds - o._seconds,
            0,
            self._microseconds - o._microseconds,
            self._year if self._year != -1 else o._year,
            self._month if self._month != -1 else o._month,
            self._day if self._day != -1 else o._day,
            self._weekday if self._weekday != -1 else o._weekday,
            self._hour if self._hour != -1 else o._hour,
            self._minute if self._minute != -1 else o._minute,
            self._second if self._second != -1 else o._second,
            -1,
            self._microsecond if self._microsecond != -1 else o._microsecond,
        )

    # Arithmetic: right subtraction ------------------------------------------
    def __rsub__(self, o: object) -> object:
        """Right subtraction `o - self`.

        - Subtraction with datetime instance or subclass (`datetime.datetime`, `cytimes.Pydt`, `pandas.Timestamp`, etc):
            - Similar to addition, but subtracts the relative deltas instead.
            - Returns the original subclass when possible, or fallback to `<'datetime.datetime'>`.

        - Subtraction with date instance or subclass (`datetime.date`, `pendulum.Date`, etc):
            - Similar to datetime subtraction, returns the original subclass when possible,
              or fallback to `<'datetime.date'>`.

        - Subtraction with delta object (`datetime.timedelta`, `cytimes.Delta`, `pandas.Timedelta`, etc):
            - Subtracts corresponding relative delta fields (left - right).
            - For delta objects with absolute delta fields (`cytimes.Delta`, `dateutil.relativedelta`),
              the left operand's absolute values are kept.
            - Returns `<'cytimes.Delta'>`.
        """
        # . common
        if utils.is_dt(o):
            return self._rsub_datetime(o)
        if utils.is_date(o):
            return self._rsub_date(o)
        if utils.is_td(o):
            return self._rsub_timedelta(o)
        if isinstance(o, relativedelta):
            return _delta_fr_relativedelta(o)._sub_delta(self)
        # . uncommon
        # TODO: numpy datetime-like object
        # np.datetime64 and np.timedelta64 are converted to
        # datetime and timedelta or integer [ns] before reaching
        if utils.is_dt64(o):
            return self._rsub_datetime(utils.dt64_to_dt(o, None, None))
        if utils.is_td64(o):
            return self._rsub_timedelta(utils.td64_to_td(o, None))
        # . unsupported
        return NotImplemented

    @cython.cfunc
    @cython.inline(True)
    def _rsub_date(self, o: datetime.date) -> datetime.date:
        """(internal) Right subtraction with `datetime.date` instance or subclass.
        Returns the original subclass when possible, or fallback to `<'datetime.date'>`.

        ## Concept
        >>> self - date
        """
        return utils.date_add_delta(
            o,
            -self._years,
            0,
            -self._months,
            0,
            -self._days,
            -self._hours,
            -self._minutes,
            -self._seconds,
            0,
            -self._microseconds,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
            None if utils.is_date_exact(o) else o.__class__,
        )

    @cython.cfunc
    @cython.inline(True)
    def _rsub_datetime(self, o: datetime.datetime) -> datetime.datetime:
        """(internal) Right subtraction with `datetime.datetime` instance or subclass.
        Returns the original subclass when possible, or fallback to `<'datetime.datetime'>`.

        ## Concept
        >>> self - datetime
        """
        return utils.dt_add_delta(
            o,
            -self._years,
            0,
            -self._months,
            0,
            -self._days,
            -self._hours,
            -self._minutes,
            -self._seconds,
            0,
            -self._microseconds,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
            None if utils.is_dt_exact(o) else o.__class__,
        )

    @cython.cfunc
    @cython.inline(True)
    def _rsub_timedelta(self, o: datetime.timedelta) -> Delta:
        """(internal) Right subtraction with `datetime.timedelta` instance or subclass.
        Returns `<'Delta'>`.

        ## Concept
        >>> self - timedelta
        """
        return Delta(
            -self._years,
            0,
            -self._months,
            0,
            -self._days + o.day,
            -self._hours,
            -self._minutes,
            -self._seconds + o.second,
            0,
            -self._microseconds + o.microsecond,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
        )

    # Arithmetic: negation ---------------------------------------------------
    def __neg__(self) -> Self:
        """Negation operation `<'Delta'>`.

        - Negates all relative delta fields.
        - Absolute delta fields remain unchanged.

        ## Concept
        >>> -self
        """
        return Delta(
            -self._years,
            0,
            -self._months,
            0,
            -self._days,
            -self._hours,
            -self._minutes,
            -self._seconds,
            0,
            -self._microseconds,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
        )

    # Arithmetic: absolute ---------------------------------------------------
    def __abs__(self) -> Self:
        """Absolute operation `<'Delta'>`.

        Applies absolute value to the relative delta fields. This implementation uses
        a `vector sign` policy: if `years < 0` then both years and months flip sign;
        if `days < 0` then day/hour/minute/second/microsecond all flip sign together.
        Absolute fields are unchanged.

        ## Concept
        >>> abs(self)
        """
        # Years & Months
        yy: cython.int = self._years
        mm: cython.int = self._months
        if yy < 0:
            yy, mm = -yy, -mm
        # Days & Times
        dd: cython.longlong = self._days
        hh: cython.int = self._hours
        mi: cython.int = self._minutes
        ss: cython.int = self._seconds
        us: cython.int = self._microseconds
        if dd < 0:
            dd, hh, mi, ss, us = -dd, -hh, -mi, -ss, -us
        # Construct
        return Delta(
            yy,
            0,
            mm,
            0,
            dd,
            hh,
            mi,
            ss,
            0,
            us,
            self._year,
            self._month,
            self._day,
            self._weekday,
            self._hour,
            self._minute,
            self._second,
            -1,
            self._microsecond,
        )

    # Comparison -------------------------------------------------------------
    def __eq__(self, o: object) -> bool:
        """Equality comparison `self == o`.

        - Supports comparison with `datetime.timedelta` instance or subclass,
          `Delta`, and `dateutil.relativedelta.`
        - Equal means two instance should yield identical result when added to
          or subtracted from a datetime/date instance.

        ## Concept
        >>> self == o
        """
        # . common
        if isinstance(o, Delta):
            return self._eq_delta(o)
        if utils.is_td(o):
            return self._eq_timedelta(o)
        if isinstance(o, relativedelta):
            return self._eq_delta(_delta_fr_relativedelta(o))
        # . uncommon
        if utils.is_td64(o):
            return self._eq_timedelta(utils.td64_to_td(o, None))
        # . unsupported
        return NotImplemented

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def _eq_timedelta(self, o: datetime.timedelta) -> cython.bint:
        """(internal) Check if equals to a `datetime.timedelta` instance or subclass.

        ## Concept
        >>> self == timedelta
        """
        # Assure no extra delta
        if not (
            self._years == 0
            and self._months == 0
            and self._year == -1
            and self._month == -1
            and self._day == -1
            and self._weekday == -1
            and self._hour == -1
            and self._minute == -1
            and self._second == -1
            and self._microsecond == -1
        ):
            return False

        # Total microseconds: self
        dd: cython.longlong = self._days
        ss: cython.longlong = self._seconds
        ss += self._hours * 3_600 + self._minutes * 60
        us: cython.longlong = self._microseconds
        m_us: cython.longlong = (dd * 86_400 + ss) * 1_000_000 + us

        # Total microseconds: object
        dd: cython.longlong = o.day
        ss: cython.longlong = o.second
        us: cython.longlong = o.microsecond
        o_us: cython.longlong = (dd * 86_400 + ss) * 1_000_000 + us

        # Comparison
        return m_us == o_us

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def _eq_delta(self, o: Delta) -> cython.bint:
        """(internal) Check if equals to another `Delta`.

        ## Concept
        >>> self == delta
        """
        return (
            self._years == o._years
            and self._months == o._months
            and self._days == o._days
            and self._hours == o._hours
            and self._minutes == o._minutes
            and self._seconds == o._seconds
            and self._microseconds == o._microseconds
            and self._year == o._year
            and self._month == o._month
            and self._day == o._day
            and self._weekday == o._weekday
            and self._hour == o._hour
            and self._minute == o._minute
            and self._second == o._second
            and self._microsecond == o._microsecond
        )

    def __bool__(self) -> bool:
        """Returns `True` if has any meaningful relative or absolute delta values `<'bool'>`."""
        return (
            self._years != 0
            or self._months != 0
            or self._days != 0
            or self._hours != 0
            or self._minutes != 0
            or self._seconds != 0
            or self._microseconds != 0
            or self._year != -1
            or self._month != -1
            or self._day != -1
            or self._weekday != -1
            or self._hour != -1
            or self._minute != -1
            or self._second != -1
            or self._microsecond != -1
        )

    # Representation ---------------------------------------------------------
    def __repr__(self) -> str:
        reprs: list = []

        # Relative delta
        if self._years != 0:
            reprs.append("years=%d" % self._years)
        if self._months != 0:
            reprs.append("months=%d" % self._months)
        if self._days != 0:
            reprs.append("days=%d" % self._days)
        if self._hours != 0:
            reprs.append("hours=%d" % self._hours)
        if self._minutes != 0:
            reprs.append("minutes=%d" % self._minutes)
        if self._seconds != 0:
            reprs.append("seconds=%d" % self._seconds)
        if self._microseconds != 0:
            reprs.append("microseconds=%d" % self._microseconds)

        # Absolute delta
        if self._year != -1:
            reprs.append("year=%d" % self._year)
        if self._month != -1:
            reprs.append("month=%d" % self._month)
        if self._day != -1:
            reprs.append("day=%d" % self._day)
        if self._weekday != -1:
            reprs.append("weekday=%s" % _WEEKDAY_REPRS[self._weekday])
        if self._hour != -1:
            reprs.append("hour=%d" % self._hour)
        if self._minute != -1:
            reprs.append("minute=%d" % self._minute)
        if self._second != -1:
            reprs.append("second=%d" % self._second)
        if self._microsecond != -1:
            reprs.append("microsecond=%d" % self._microsecond)

        # Create
        return "<'%s' (%s)>" % (self.__class__.__name__, ", ".join(reprs))

    def __hash__(self) -> int:
        if self._hashcode == -1:
            self._hashcode = hash(
                (
                    self._years,
                    self._months,
                    self._days,
                    self._hours,
                    self._minutes,
                    self._seconds,
                    self._microseconds,
                    self._year,
                    self._month,
                    self._day,
                    self._weekday,
                    self._hour,
                    self._minute,
                    self._second,
                    self._microsecond,
                )
            )
        return self._hashcode
