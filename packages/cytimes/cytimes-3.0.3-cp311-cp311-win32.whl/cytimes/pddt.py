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
from typing import Any, Hashable
from typing_extensions import Self
import datetime
import numpy as np
import pandas as pd
from pandas import DatetimeIndex
from pandas.core.arrays.datetimes import DatetimeArray
from pandas._libs.lib import no_default as _no_default
from zoneinfo import available_timezones as _available_timezones
from cytimes.pydt import Pydt
from cytimes.parser import (
    Configs,
    parse_obj as _parse_obj,
    parse_month as _parse_month,
    parse_weekday as _parse_weekday,
)
from cytimes import errors, utils

__all__ = ["Pddt"]


# Utils ---------------------------------------------------------------------------------------
@cython.cfunc
@cython.inline(True)
@cython.exceptval(-1, check=False)
def _parse_size(cls: object, size: object) -> cython.Py_ssize_t:
    """(internal) Parse the `size` object to an integer to represent the size of an array `<'int'>`.

    :param cls `<'type'>`: The class object calling this function.
    :param size `<'int/str/float/bytes/Array-like'>`: The size object.
    :returns `<'int'>`: The integer representing the array size.

    ## Notice
    - For `int`, `str`, `float`, `bytes', converts to an integer using `int()`.
    - For other types, try to get the length of the object to represent the array size.
    """
    # int
    if isinstance(size, int):
        value: cython.Py_ssize_t = size

    # str / float / bytes
    elif isinstance(size, (float, str, bytes)):
        try:
            value: cython.Py_ssize_t = int(size)
        except Exception as err:
            # fmt: off
            errors.raise_argument_error(cls, "size",
                "Cannot convert '%s' %s to integer." 
                % (size, type(size)), err)
            # fmt: on
            return -1  # unreachable: suppress compiler warning

    # Array-like
    else:
        try:
            value: cython.Py_ssize_t = len(size)
        except Exception as err:
            # fmt: off
            errors.raise_argument_error(cls, "size",
                "Cannot get the length of '%s' %s." 
                % (size, type(size)), err)
            # fmt: on
            return -1  # unreachable: suppress compiler warning

    # Non-negative check
    if value < 1:
        # fmt: off
        errors.raise_argument_error(cls, "size",
            "Array size must be greater than 0, instead got %d." % value)
        # fmt: on
    return value


@cython.cfunc
@cython.inline(True)
def _parse_freq(freq: object) -> object:
    """(internal) Parse the frequency object `<'object'>`.

    :param freq `<'object'>`: The frequency object.
    :returns `<'object'>`: The normalize frequency object.

    ## Notice
    This function is designed to only normalize `str` frequency
    aliases, and only modifies the following input:

    - 'm' -> 'min'
    """
    if isinstance(freq, str) and str_len(freq) == 1 and str_read(freq, 0) == "m":
        return "min"
    else:
        return freq


@cython.cfunc
@cython.inline(True)
def _parse_us_from_iso_dict(cls: object, iso: dict) -> cython.longlong:
    """(internal) Parse the ISO dictionary to total microseconds since Unix Epoch `<'int'>`.

    :param cls `<'type'>`: The class object calling this function.
    :param iso `<'dict'>`: The dictionary containing `'year'`, `'week'`and `'weekday'` (or `'day'`) keys.
    :returns `<'int'>`: The total microseconds since Unix Epoch.
    """
    # Year
    year = iso.get("year", None)
    if not isinstance(year, int):
        if year is None:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Dictionary must contain 'year' key for ISO year value.")
            # fmt: on
        else:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Value for 'year' must be an integer, instead got %s %s." 
                % (year, type(year)))
            # fmt: on

    # Week
    week = iso.get("week", None)
    if not isinstance(week, int):
        if week is None:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Dictionary must contain 'week' key for ISO week value.")
            # fmt: on
        else:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Value for 'week' must be an integer, instead got %s %s." 
                % (week, type(week)))
            # fmt: on

    # Weekday
    weekday = iso.get("weekday", iso.get("day", None))
    if not isinstance(weekday, int):
        if weekday is None:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Dictionary must contain 'weekday' key for ISO weekday value.")
            # fmt: on
        else:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Value for 'weekday' must be an integer, instead got %s %s." 
                % (weekday, type(weekday)))
            # fmt: on

    # Compute microseconds (since Unix Epoch)
    _ymd = utils.ymd_fr_iso(year, week, weekday)
    value: cython.longlong = utils.ymd_to_ord(_ymd.year, _ymd.month, _ymd.day)
    return (value - utils.EPOCH_DAY) * utils.US_DAY


@cython.cfunc
@cython.inline(True)
def _parse_us_from_doy_dict(cls: object, doy: dict) -> cython.longlong:
    """(internal) Parse the day-of-year dictionary to total microseconds since Unix Epoch `<'int'>`.

    :param cls `<'type'>`: The class object calling this function.
    :param doy `<'dict'>`: The dictionary containing `'year'` and `'doy'` (or `'day'`) keys.
    :returns `<'int'>`: The total microseconds since Unix Epoch.
    """
    # Year
    year = doy.get("year", None)
    if not isinstance(year, int):
        if year is None:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Dictionary must contain 'year' key for day-of-year value.")
            # fmt: on
        else:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Value for 'year' must be an integer, instead got %s %s." 
                % (year, type(year)))
            # fmt: on

    # Day-of-year
    day_of_year = doy.get("doy", doy.get("day", None))
    if not isinstance(day_of_year, int):
        if day_of_year is None:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Dictionary must contain 'doy' key for day-of-year value.")
            # fmt: on
        else:
            # fmt: off
            errors.raise_argument_error(cls, "iso",
                "Value for 'doy' must be an integer, instead got %s %s." 
                % (day_of_year, type(day_of_year)))
            # fmt: on

    # Compute microseconds (since Unix Epoch)
    _ymd = utils.ymd_fr_doy(year, day_of_year)
    value: cython.longlong = utils.ymd_to_ord(_ymd.year, _ymd.month, _ymd.day)
    return (value - utils.EPOCH_DAY) * utils.US_DAY


# Pddt (Pandas Datetime) ----------------------------------------------------------------------
class Pddt(DatetimeIndex):
    """A drop-in replacement for Pandas `<'DatetimeIndex'>` with extended parsing,
    timezone normalization, resolution control, and delta-aware arithmetic.

    `Pddt` behaves like `DatetimeIndex` in all common operations, while adding:

    - Robust datetime parsing (via custom parser).
    - Nanosecond/microsecond/millisecond/second unit conversion (`as_unit`).
    - Vectorized calendar operations (year/month/quarter shifting & replacing).
    - High-performance datetime arithmetic (`add`, `sub`).

    ## Important Note
    `Pddt` is `datetime64[us]` focused. It will try to retain nanosecond resolution
    when possible, but will automatically downcast to microsecond resolution
    if the value exceeds the bounds of `datetime64[ns]`. This behavior applies
    to all `Pddt` methods.
    """

    def __new__(
        cls,
        data: object,
        freq: object | None = None,
        tz: datetime.tzinfo | str | None = None,
        ambiguous: object = "raise",
        yearfirst: bool = True,
        dayfirst: bool = False,
        as_unit: str = None,
        copy: bool = False,
        name: Hashable | None = None,
        cfg: Configs = None,
    ) -> Self:
        """A drop-in replacement for Pandas `<'DatetimeIndex'>` with extended parsing,
        timezone normalization, resolution control, and delta-aware arithmetic.

        `Pddt` behaves like `DatetimeIndex` in all common operations, while adding:

        - Robust datetime parsing (via custom parser).
        - Nanosecond/microsecond/millisecond/second unit conversion (`as_unit`).
        - Vectorized calendar operations (year/month/quarter shifting & replacing).
        - High-performance datetime arithmetic (`add`, `sub`).

        ## Important Note
        `Pddt` is `datetime64[us]` focused. It will try to retain nanosecond resolution
        when possible, but will automatically downcast to microsecond resolution
        if the value exceeds the bounds of `datetime64[ns]`. This behavior applies
        to all `Pddt` methods.

        :param data `<'Array-Like'>`: An array-like (1-dimensional) data containing datetime information.
            Such as: `tuple`, `list`, `np.ndarray`, `DatetimeIndex`, `Series`, etc.

        :param freq `<'str/timedelta/BaseOffset/None'>`: The frequency of the 'data'. Defaults to `None`.

            - `<'str'>` A frequency string (e.g. `'D', 'h', 's', 'ms'`), or `'infer'` for auto-detection.
            - `<'timedelta'>` A datetime.timedelta instance.
            - `<'BaseOffset'>` A pandas date offset instance.

        :param tz `<'tzinfo/str/None'>`: The optional target timezone. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param ambiguous `<'str/ndarray[bool]'>`: Specified how ambiguous times should be handled. Defaults to `'raise'`.

            - `'raise'` will raise an `AmbiguousTimeError` if there are ambiguous times.
            - `'infer'` will attempt to infer fall dst-transition hours based on order.
            - `'NaT'` will yield NaT where there are ambiguous times.
            - `<'ndarray[bool]'>` where True signifies a DST time, False signifies a non-DST
                time (note that this flag is only applicable for ambiguous times)

        :param yearfirst `<'bool/None'>`: Parse the first ambiguous Y/M/D value as year. Defaults to `True`.

        :param dayfirst `<'bool/None'>`: Parse the first ambiguous Y/M/D values as day. Defaults to `False`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param copy `<'bool'>`: Whether to make a copy of the 'data'. Defaults to `False`.

        :param name `<'Hashable/None'>`: The name assigned to the index. Defaults to `None`.

        :param cfg `<'Configs/None'>`: The Parser configuration. Defaults to `None`.
            Only applicable to datetime-string parsing. If `None`, uses the module's default `Configs`.
        """
        return cls._new(
            data,
            freq=freq,
            tz=tz,
            ambiguous=ambiguous,
            yearfirst=yearfirst,
            dayfirst=dayfirst,
            as_unit=as_unit,
            copy=copy,
            name=name,
            cfg=cfg,
        )

    # Constructor --------------------------------------------------------------------------
    @classmethod
    def _new(
        cls,
        data: object,
        freq: object | None = None,
        tz: datetime.tzinfo | str | None = None,
        ambiguous: object = "infer",
        yearfirst: bool = True,
        dayfirst: bool = False,
        as_unit: str = None,
        copy: bool = False,
        name: Hashable | None = None,
        cfg: Configs = None,
    ) -> Self:
        """(internal) Create a new `Pddt` instance."""
        # Parse timezone
        tz = utils.tz_parse(tz)

        # Adjust frequency
        if freq is None:
            freq = _no_default
        else:
            freq = _parse_freq(freq)

        # Base approach: datetime64[ns]
        try:
            return cls._new_native(
                data,
                freq=freq,
                tz=tz,
                ambiguous=ambiguous,
                yearfirst=yearfirst,
                dayfirst=dayfirst,
                as_unit=as_unit,
                copy=copy,
                name=name,
            )

        # Out of bounds / Parsing / Overflow -> Fallback: cytimes parser
        # datetime[us] + Optional Timezone
        except (errors.OutOfBoundsError, errors.ParserFailedError):
            return cls._new_parser(
                data,
                freq=freq,
                tz=tz,
                ambiguous=ambiguous,
                yearfirst=yearfirst,
                dayfirst=dayfirst,
                as_unit=as_unit,
                copy=copy,
                name=name,
                cfg=cfg,
            )

        # Ambiguous Time -> Fallback: cytimes parser
        # datetime[us] + Optional Timezone
        except errors.AmbiguousTimeError:
            if ambiguous == "raise":
                raise
            return cls._new_parser(
                data,
                freq=freq,
                tz=tz,
                ambiguous=ambiguous,
                yearfirst=yearfirst,
                dayfirst=dayfirst,
                as_unit=as_unit,
                copy=copy,
                name=name,
                cfg=cfg,
            )

        # Handle mixed timezones: datetime64[ns] + UTC
        except errors.MixedTimezoneError:
            return cls._new_native(
                data,
                freq=freq,
                tz=utils.UTC,  # UTC timezone
                ambiguous=ambiguous,
                yearfirst=yearfirst,
                dayfirst=dayfirst,
                as_unit=as_unit,
                copy=copy,
                name=name,
            )

    @classmethod
    def _new_native(
        cls,
        data: object,
        freq: object | None = None,
        tz: datetime.tzinfo = None,
        ambiguous: object = "infer",
        yearfirst: bool = True,
        dayfirst: bool = False,
        as_unit: str = None,
        copy: bool = False,
        name: Hashable | None = None,
    ) -> Self:
        """(internal) Create a new `Pddt` instance using native Pandas `DatetimeIndex`.

        This method attempts to create a `Pddt` instance using Pandas `DatetimeIndex`.
        If any exceptions related to datetime bounds, parsing, or timezone ambiguities
        occur, they are caught and re-raised as `Pddt` specific exceptions.
        """
        try:
            pt = DatetimeIndex.__new__(
                cls,
                data=data,
                freq=freq,
                tz=_no_default if tz is None else tz,
                ambiguous=ambiguous,
                dayfirst=dayfirst,
                yearfirst=yearfirst,
                dtype=None,
                copy=copy,
                name=name,
            )
        except errors.PdOutOfBoundsDatetime as err:
            raise errors.OutOfBoundsError(err) from err
        except (errors.PytzAmbiguousTimeError, errors.PytzNonExistentTimeError) as err:
            raise errors.AmbiguousTimeError(err) from err
        except errors.PdDateParseError as err:
            raise errors.ParserFailedError(err) from err
        except OverflowError as err:
            msg: str = str(err)
            if "too large to convert to C long" in msg:
                raise errors.OutOfBoundsError(err) from err
            raise err
        except TypeError as err:
            msg: str = str(err)
            if "mixed timezones" in msg:
                raise errors.MixedTimezoneError(err) from err
            raise err
        except ValueError as err:
            msg: str = str(err)
            if "mix tz-aware" in msg:
                raise errors.MixedTimezoneError(err) from err
            if "unless utc=True" not in msg:
                raise errors.MixedTimezoneError(err) from err
            raise err

        # Convert to specified unit
        return pt if as_unit is None else pt.as_unit(as_unit)

    @classmethod
    def _new_parser(
        cls,
        data: object,
        freq: object | None = None,
        tz: datetime.tzinfo = None,
        ambiguous: object = "infer",
        yearfirst: bool | None = True,
        dayfirst: bool | None = False,
        as_unit: str = None,
        copy: bool = False,
        name: Hashable | None = None,
        cfg: Configs = None,
    ) -> Self:
        """(internal) Create a new `Pddt` instance using `cytimes` parser.

        This method is a fallback approach that utilizes the `cytimes` parser
        to construct the `Pddt` instance. It is invoked when the native Pandas
        `DatetimeIndex` constructor fails due to datetime bounds, parsing issues,
        or timezone ambiguities.
        """
        # . get array size
        try:
            arr_size: cython.Py_ssize_t = len(data)
        except Exception as err:
            raise TypeError(
                "%s(...) must be called with a collection of some kind, "
                "%s was passed" % (cls.__name__, type(data)),
            ) from err
        # . setup array
        arr: np.ndarray = np.PyArray_EMPTY(1, [arr_size], np.NPY_TYPES.NPY_INT64, 0)
        arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
        # . setup parser
        has_tz: cython.bint = tz is not None
        tmp_tz = tz if has_tz else utils.UTC
        infer: cython.bint = ambiguous == "infer"
        i: cython.Py_ssize_t = 0
        try:
            for obj in data:
                # . parse datetime object
                dt: datetime.datetime = _parse_obj(
                    obj, None, yearfirst, dayfirst, False, True, cfg, None
                )
                # . normalize timezone [aware]
                if dt.tzinfo is not None:
                    dt = utils.dt_astimezone(dt, tmp_tz, None)
                    if tz is None:
                        tz = utils.UTC
                # . infer ambiguous time [naive]
                elif infer and has_tz:
                    dt = utils.dt_replace_tz_fold(dt, tz, 1, None)
                    dt = utils.dt_normalize_tz(dt, None)
                # . assign to array
                arr_p[i] = utils.dt_to_us(dt, False)  # without timezone
                i += 1
            arr = arr.astype(utils.DT64_DTYPE_US)  # convert to datetime64[us]
        except Exception as err:
            raise ValueError(
                "Invalid '%s.__new__(data, ...)' input.\n%s" % (cls.__name__, err)
            ) from err
        # . new instance
        return cls._new_native(
            arr,
            freq=freq,
            tz=tz,
            ambiguous=ambiguous,
            dayfirst=dayfirst,
            yearfirst=yearfirst,
            as_unit=as_unit,
            copy=copy,
            name=name,
        )

    @classmethod
    def date_range(
        cls,
        start: object | None = None,
        end: object | None = None,
        periods: int | None = None,
        freq: object | None = "D",
        tz: datetime.tzinfo | str | None = None,
        normalize: bool = False,
        inclusive: str = "both",
        unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct a fixed-frequency index `<'Pddt'>`.

        Construct datetime index from the range of equally spaced time points (where the
        difference between any two adjacent points is specified by the given frequency)
        such that they all satisfy `start <[=] x <[=] end`, where the first one and the
        last one are, resp., the first and last time points in that range that fall on
        the boundary of `freq` (if given as a frequency string) or that are valid for
        `freq` (if given as a :class:`pandas.tseries.offsets.DateOffset`). (If exactly
        one of `start`, `end`, or `freq` is *not* specified, this missing parameter can
        be computed given `periods`, the number of timesteps in the range. See the note below.)

        :param start `<'Datetime-Like/None'>`: Left bound for generating the index. Defaults to `None`.
        :param end `<'Datetime-Like/None'>`: Right bound for generating the index. Defaults to `None`.
        :param periods `<'int/None'>`: Number of periods to generate. Defaults to `None`.
        :param freq `<'str/timedelta/BaseOffset/None'>`: The frequency of the index. Defaults to `'D'`.

            - `<'str'>` A frequency string (e.g. `'D', 'h', 's', 'ms'`), or `'infer'` for auto-detection.
            - `<'timedelta'>` A datetime.timedelta instance.
            - `<'BaseOffset'>` A pandas date offset instance.
            - `<'None'>` Infer the frequency from the input data.

        :param tz `<'tzinfo/str/None'>`: The optional target timezone. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param normalize `<'bool'>`: Normalize the start/end dates to midnight
            (time fields set to 0). Defaults to `False`.

        :param inclusive `<'str'>`: Include boundaries. Defaults to `'both'`.

            - `'left'` Include the left boundary.
            - `'right'` Include the right boundary.
            - `'both'` Include both boundaries.
            - `'neither'` Exclude both boundaries.

        :param unit `<'str/None'>`: Specify the desired resolution of the result. Defaults to `None`.
            Supported datetime units: 's', 'ms', 'us', 'ns'.

        :param name `<'Hashable/None'>`: The name assigned to the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.

        ## Equivalent
        >>> Pddt(pd.date_range(...))
        """
        if freq is None and (periods is None or start is None or end is None):
            freq = "D"
        try:
            dtarr = DatetimeArray._generate_range(
                start=start,
                end=end,
                periods=periods,
                freq=freq,
                tz=utils.tz_parse(tz),
                normalize=normalize,
                inclusive=inclusive,
                unit=unit,
            )
        # fmt: off
        except errors.PdOutOfBoundsDatetime as err:
            errors.raise_error(errors.OutOfBoundsError, cls, "date_range(...)", 
                "Try to set 'unit' to a lower resolution.", err)
            return  # unreachable: suppress compiler warning
        except (errors.PytzAmbiguousTimeError, errors.PytzNonExistentTimeError) as err:
            errors.raise_error(errors.AmbiguousTimeError, cls, "date_range(...)", None, err)
            return  # unreachable: suppress compiler warning
        except Exception as err:
            errors.raise_argument_error(cls, "date_range(...)", None, err)
            return  # unreachable: suppress compiler warning
        # fmt: on
        return cls._new(dtarr, name=name)

    @classmethod
    def parse(
        cls,
        data: object,
        freq: object | None = None,
        tz: datetime.tzinfo | str | None = None,
        ambiguous: object = "raise",
        yearfirst: bool = True,
        dayfirst: bool = False,
        as_unit: str = None,
        copy: bool = False,
        name: Hashable | None = None,
        cfg: Configs = None,
    ) -> Self:
        """Parse from an array-like (1-dimensional) data `<'Pddt'>`.

        :param data `<'Array-Like'>`: An array-like (1-dimensional) data containing datetime information.
            Such as: `tuple`, `list`, `np.ndarray`, `DatetimeIndex`, `Series`, etc.

        :param freq `<'str/timedelta/BaseOffset/None'>`: The frequency of the 'data'. Defaults to `None`.

            - `<'str'>` A frequency string (e.g. `'D', 'h', 's', 'ms'`), or `'infer'` for auto-detection.
            - `<'timedelta'>` A datetime.timedelta instance.
            - `<'BaseOffset'>` A pandas date offset instance.

        :param tz `<'tzinfo/str/None'>`: The optional target timezone. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param ambiguous `<'str/ndarray[bool]'>`: Specified how ambiguous times should be handled. Defaults to `'raise'`.

            - `'raise'` will raise an `AmbiguousTimeError` if there are ambiguous times.
            - `'infer'` will attempt to infer fall dst-transition hours based on order.
            - `'NaT'` will yield NaT where there are ambiguous times.
            - `<'ndarray[bool]'>` where True signifies a DST time, False signifies a non-DST
                time (note that this flag is only applicable for ambiguous times)

        :param yearfirst `<'bool/None'>`: Parse the first ambiguous Y/M/D value as year. Defaults to `True`.

        :param dayfirst `<'bool/None'>`: Parse the first ambiguous Y/M/D values as day. Defaults to `False`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param copy `<'bool'>`: Whether to make a copy of the 'data'. Defaults to `False`.

        :param name `<'Hashable/None'>`: The name assigned to the index. Defaults to `None`.

        :param cfg `<'Configs/None'>`: The Parser configuration. Defaults to `None`.
            Only applicable to datetime-string parsing. If `None`, uses the module's default `Configs`.

        :returns `<'Pddt'>`: The resulting datetime index.
        """
        return cls(
            data,
            freq=freq,
            tz=tz,
            ambiguous=ambiguous,
            yearfirst=yearfirst,
            dayfirst=dayfirst,
            as_unit=as_unit,
            copy=copy,
            name=name,
            cfg=cfg,
        )

    @classmethod
    def now(
        cls,
        size: int | Any,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from the current datetime with optional timezone `<'Pddt'>`.

        :param size `<'int/Any'>`: The target size of the index.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.

        :param tz `<'tzinfo/str/None'>`: The optional timezone. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (naive when `tz` is None).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        """
        tz = utils.tz_parse(tz)
        size_i: cython.Py_ssize_t = _parse_size(cls, size)
        dt: datetime.datetime = utils.dt_now(tz, None)
        us: cython.longlong = utils.dt_to_us(dt, False)
        arr: np.ndarray = utils.dt64arr_fr_int64(us, size_i, "us")
        return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

    @classmethod
    def utcnow(
        cls,
        size: int | Any,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from the current `UTC` datetime (timezone-aware) `<'Pddt'>`.

        :param size `<'int/Any'>`: The target size of the index.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (timezone-aware).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        """
        return cls.now(size, tz=utils.UTC, as_unit=as_unit, name=name)

    @classmethod
    def today(
        cls,
        size: int | Any,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from the current `local` datetime (timezone-naive) `<'Pddt'>`.

        :param size `<'int/Any'>`: The target size of the index.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (timezone-naive).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.

        ## Equivalent
        >>> Pddt.now(size, tz=None)
        """
        return cls.now(size, tz=None, as_unit=as_unit, name=name)

    @classmethod
    def combine(
        cls,
        size: int | Any,
        date: datetime.date | str | None = None,
        time: datetime.time | str | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Combine date and time into a new datetime index `<'Pddt'>`.

        :param size `<'int/Any'>`: The target size of the index.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.

        :param date `<'date/str/None'>`: A date-like object. Defaults to `None`.
            If None, uses today's `local` date.

        :param time `<'time/str/None'>`: A time-like object. Defaults to `None`.
            If None, uses `00:00:00.000000`.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive (when `time` has no timezone info, see `Notes`).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.

        ## Notes
        - Both `date` and `time` supports datetime-like object (please refer
          to `Pydt.parse()` method for details), but only the corresponding date
          or time fields are used for combination.
        - If `tz` is `None`, but `time` contains timezone information, the
          resulting datetime will be timezone-aware using `time`'s timezone.
        - If `tz` is specified (not `None`), it `overrides` any timezone
          information in `time`.
        """
        # Timezone & size
        tz = utils.tz_parse(tz)
        size_i: cython.Py_ssize_t = _parse_size(cls, size)

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

        # Combine datetime
        dt: datetime.datetime = utils.dt_combine(date, time, tz, None)
        us: cython.longlong = utils.dt_to_us(dt, False)
        arr: np.ndarray = utils.dt64arr_fr_int64(us, size_i, "us")
        return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

    @classmethod
    def fromordinal(
        cls,
        ordinal: int | object,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from Gregorian ordinal days `<'Pddt'>`.

        :param ordinal `<'int/Array-like'>`: The ordinal days to construct with.

            - `<'int'>` The integer representing the Gregorian ordinal day.
            - `<'Array-like'>` An array-like object containing elements representing the ordinal days.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `ordinal` is an integer). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `ordinal` is an array-like object.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive (when `time` has no timezone info, see `Notes`).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (naive when `tz` is None).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        """
        # Integer
        if isinstance(ordinal, int):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromordinal(size)",
                    "When 'ordinal' is an integer, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            value: cython.longlong = int(ordinal)
            value = (value - utils.EPOCH_DAY) * utils.US_DAY
            # . new instance
            arr: np.ndarray = utils.dt64arr_fr_int64(value, size_i, "us")
            return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

        # list / tuple
        if isinstance(ordinal, (list, tuple)):
            # . construct ndarray[int64] - unit: us
            size_i: cython.Py_ssize_t = len(ordinal)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for o in ordinal:
                try:
                    value: cython.longlong = int(o)
                except Exception as err:
                    errors.raise_argument_error(
                        cls,
                        "fromordinal(ordinal)",
                        "Expects integer element from %s, got '%s' %s."
                        % (type(ordinal).__name__, o, type(o)),
                        err,
                    )
                    return  # unreachable: suppress compiler warning
                arr_p[i] = (value - utils.EPOCH_DAY) * utils.US_DAY
                i += 1
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # pd.Index (DatetimeIndex) / pd.Series
        if isinstance(ordinal, (pd.Index, pd.Series)):
            ordinal = ordinal.values

        # numpy.ndarray
        if isinstance(ordinal, np.ndarray):
            # . validate 1-D array
            arr: np.ndarray = ordinal
            if arr.ndim != 1:
                errors.raise_argument_error(
                    cls,
                    "fromordinal(ordinal)",
                    "Expects a 1-dimensional array, got %d-dim." % arr.ndim,
                )
            # . convert to ndarray[int64] - unit: us
            if utils.is_arr_int(arr) or utils.is_arr_uint(arr):
                arr = utils.arr_add(arr, -utils.EPOCH_DAY, True)
            elif utils.is_dt64arr(arr):
                arr = utils.dt64arr_as_int64_D(arr, -1, 0, True)
            else:
                errors.raise_argument_error(
                    cls,
                    "fromordinal(ordinal)",
                    "Unsupported array dtype [%s]." % arr.dtype,
                )
            arr = utils.arr_mul(arr, utils.US_DAY, 0, False)
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # Unsupported type
        errors.raise_type_error(
            cls,
            "fromordinal(ordinal)",
            "Unsupported 'ordinal' data type %s." % type(ordinal),
        )

    @classmethod
    def fromseconds(
        cls,
        seconds: int | float | object,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from seconds since the epoch `<'Pddt'>`.

        :param seconds `<'int/float/Array-like'>`: The seconds to construct with.

            - `<'int/float'>` A numeric value representing seconds since epoch.
            - `<'Array-like'>` An array-like object containing elements representing the seconds.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `seconds` is a float or integer ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `seconds` is an array-like object.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive (when `time` has no timezone info, see `Notes`).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (naive when `tz` is None).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        - Unlike `fromtimestamp()`, this method never assumes local time when
          `tz is None`, and interprets `seconds` as-is without any local-time conversion.
        - When `tz` is specified, the timezone is simply `attached` without any conversion.
        """
        # Integer / Float
        if isinstance(seconds, (int, float)):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromseconds(size)",
                    "When 'seconds' is a float or integer, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            value: cython.double = float(seconds)
            us: cython.longlong = utils.sec_to_us(value)
            # . new instance
            arr: np.ndarray = utils.dt64arr_fr_int64(us, size_i, "us")
            return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

        # list / tuple
        if isinstance(seconds, (list, tuple)):
            # . construct ndarray[int64] - unit: us
            size_i: cython.Py_ssize_t = len(seconds)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for o in seconds:
                try:
                    value: cython.double = float(o)
                except Exception as err:
                    errors.raise_argument_error(
                        cls,
                        "fromseconds(seconds)",
                        "Expects float or integer element from %s, got '%s' %s."
                        % (type(seconds).__name__, o, type(o)),
                        err,
                    )
                    return  # unreachable: suppress compiler warning
                arr_p[i] = utils.sec_to_us(value)
                i += 1
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # pd.Index (DatetimeIndex) / pd.Series
        if isinstance(seconds, (pd.Index, pd.Series)):
            seconds = seconds.values

        # numpy.ndarray
        if isinstance(seconds, np.ndarray):
            # . validate 1-D array
            arr: np.ndarray = seconds
            if arr.ndim != 1:
                errors.raise_argument_error(
                    cls,
                    "fromseconds(seconds)",
                    "Expects a 1-dimensional array, got %d-dim." % arr.ndim,
                )
            # . convert to ndarray[int64] - unit: us
            if utils.is_arr_float(arr):
                arrf: np.ndarray = utils.arr_assure_float64(arr, False)
                arrf_p = cython.cast(
                    cython.pointer(np.npy_float64), np.PyArray_DATA(arrf)
                )
                size_i: cython.Py_ssize_t = arrf.shape[0]
                arr = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
                arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
                i: cython.Py_ssize_t
                for i in range(size_i):
                    arr_p[i] = utils.sec_to_us(arrf_p[i])
            elif utils.is_arr_int(arr) or utils.is_arr_uint(arr):
                arr = utils.arr_mul(arr, utils.US_SECOND, 0, True)
            elif utils.is_dt64arr(arr):
                arr = utils.dt64arr_as_int64_us(arr, -1, 0, True)
            else:
                errors.raise_argument_error(
                    cls,
                    "fromseconds(seconds)",
                    "Unsupported array dtype [%s]." % arr.dtype,
                )
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # Unsupported type
        errors.raise_type_error(
            cls,
            "fromseconds(seconds)",
            "Unsupported 'seconds' data type %s." % type(seconds),
        )

    @classmethod
    def frommicroseconds(
        cls,
        us: int | object,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from microseconds since the epoch `<'Pddt'>`.

        :param us `<'int/Array-like'>`: The microseconds to construct with.

            - `<'int'>` The integer representing microseconds since epoch.
            - `<'Array-like'>` An array-like object containing elements representing the microseconds.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `us` is an integer ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `us` is an array-like object.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive (when `time` has no timezone info, see `Notes`).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (naive when `tz` is None).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        - Unlike `fromtimestamp()`, this method never assumes local time when
          `tz is None`, and interprets `us` as-is without any local-time conversion.
        - When `tz` is specified, the timezone is simply `attached` without any conversion.
        """
        # Integer
        if isinstance(us, int):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "frommicroseconds(size)",
                    "When 'us' is an integer, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            value: cython.longlong = int(us)
            # . new instance
            arr: np.ndarray = utils.dt64arr_fr_int64(value, size_i, "us")
            return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

        # list / tuple
        if isinstance(us, (list, tuple)):
            # . construct ndarray[int64] - unit: us
            size_i: cython.Py_ssize_t = len(us)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for o in us:
                try:
                    value: cython.longlong = int(o)
                except Exception as err:
                    errors.raise_argument_error(
                        cls,
                        "frommicroseconds(us)",
                        "Expects integer element from %s, got '%s' %s."
                        % (type(us).__name__, o, type(o)),
                        err,
                    )
                    return  # unreachable: suppress compiler warning
                arr_p[i] = value
                i += 1
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # pd.Index (DatetimeIndex) / pd.Series
        if isinstance(us, (pd.Index, pd.Series)):
            us = us.values

        # numpy.ndarray
        if isinstance(us, np.ndarray):
            # . validate 1-D array
            arr: np.ndarray = us
            if arr.ndim != 1:
                errors.raise_argument_error(
                    cls,
                    "frommicroseconds(us)",
                    "Expects a 1-dimensional ndarray, got %d-dim." % arr.ndim,
                )
            # . convert to ndarray[int64] - unit: us
            if utils.is_arr_int(arr) or utils.is_arr_uint(arr):
                arr = utils.arr_assure_int64(arr, True)
            elif utils.is_dt64arr(arr):
                arr = utils.dt64arr_as_int64_us(arr, -1, 0, True)
            else:
                errors.raise_argument_error(
                    cls,
                    "frommicroseconds(us)",
                    "Unsupported array dtype [%s]." % arr.dtype,
                )
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # Unsupported type
        errors.raise_type_error(
            cls,
            "frommicroseconds(us)",
            "Unsupported 'us' data type %s." % type(us),
        )

    @classmethod
    def fromtimestamp(
        cls,
        ts: int | float | object,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from POSIX timestamps optionally converted to a timezone `<'Pddt'>`.

        :param ts `<'int/float/Array-like'>`: The POSIX timestamps to construct with.

            - `<'int/float'>` A numeric value representing the timestamp.
            - `<'Array-like'>` An array-like object containing elements representing the timestamps.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `ts` is a float or integer ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `ts` is an array-like object.

        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` naive `local` time (assumes local timezone).
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (naive when `tz` is None).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        """
        # Parse timezone
        tz = utils.tz_parse(tz)

        # Integer / Float
        if isinstance(ts, (int, float)):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromtimestamp(ts)",
                    "When 'ts' is a float or integer, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            value: cython.double = float(ts)
            try:
                dt: datetime.datetime = utils.dt_fr_ts(value, tz, None)
            except Exception as err:
                errors.raise_argument_error(
                    cls,
                    "fromtimestamp(ts)",
                    "Cannot convert timestamp '%s' to datetime." % value,
                    err,
                )
                return  # unreachable: suppress compiler warning
            us: cython.longlong = utils.dt_to_us(dt, False)
            # . new instance
            arr: np.ndarray = utils.dt64arr_fr_int64(us, size_i, "us")
            return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

        # list / tuple
        if isinstance(ts, (list, tuple)):
            # . construct ndarray[int64] - unit: us
            size_i: cython.Py_ssize_t = len(ts)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for o in ts:
                try:
                    value: cython.double = float(o)
                except Exception as err:
                    errors.raise_argument_error(
                        cls,
                        "fromtimestamp(ts)",
                        "Expects float or integer element from %s, got '%s' %s."
                        % (type(ts).__name__, o, type(o)),
                        err,
                    )
                    return  # unreachable: suppress compiler warning
                try:
                    dt: datetime.datetime = utils.dt_fr_ts(value, tz, None)
                except Exception as err:
                    errors.raise_argument_error(
                        cls,
                        "fromtimestamp(ts)",
                        "Cannot convert %s element '%s' to datetime."
                        % (type(ts).__name__, value),
                        err,
                    )
                    return  # unreachable: suppress compiler warning
                arr_p[i] = utils.dt_to_us(dt, False)
                i += 1
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # pd.Index (DatetimeIndex) / pd.Series
        if isinstance(ts, (pd.Index, pd.Series)):
            ts = ts.values

        # numpy.ndarray
        if isinstance(ts, np.ndarray):
            # . validate 1-D array
            arr: np.ndarray = ts
            if arr.ndim != 1:
                errors.raise_argument_error(
                    cls,
                    "fromtimestamp(ts)",
                    "Expects a 1-dimensional array, got %d-dim." % arr.ndim,
                )
            # . convert to ndarray[int64] - unit: us
            if (
                utils.is_arr_float(arr)
                or utils.is_arr_int(arr)
                or utils.is_arr_uint(arr)
            ):
                arrf: np.ndarray = utils.arr_assure_float64(arr, False)
                arrf_p = cython.cast(
                    cython.pointer(np.npy_float64), np.PyArray_DATA(arrf)
                )
                size_i: cython.Py_ssize_t = arrf.shape[0]
                arr = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
                arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
                i: cython.Py_ssize_t
                for i in range(size_i):
                    try:
                        dt = utils.dt_fr_ts(arrf_p[i], tz, None)
                    except Exception as err:
                        errors.raise_argument_error(
                            cls,
                            "fromtimestamp(ts)",
                            "Cannot convert array element '%s' to datetime."
                            % arrf_p[i],
                            err,
                        )
                        return  # unreachable: suppress compiler warning
                    arr_p[i] = utils.dt_to_us(dt, False)
            elif utils.is_dt64arr(arr):
                arr = utils.dt64arr_as_int64_us(arr, -1, 0, True)
            else:
                errors.raise_argument_error(
                    cls,
                    "fromtimestamp(ts)",
                    "Unsupported array dtype [%s]." % arr.dtype,
                )
            # . new instance
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # Unsupported type
        errors.raise_type_error(
            cls,
            "fromtimestamp(ts)",
            "Unsupported 'ts' data type %s." % type(ts),
        )

    @classmethod
    def utcfromtimestamp(
        cls,
        ts: int | float | object,
        size: int | Any | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct a UTC-aware index from POSIX timestamps (timezone-aware) `<'Pddt'>`.

        :param ts `<'int/float/Array-like'>`: The POSIX timestamps to construct with.

            - `<'int/float'>` A numeric value representing the timestamp.
            - `<'Array-like'>` An array-like object containing elements representing the timestamps.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `ts` is a float or integer ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `ts` is an array-like object.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index (timezone-aware).

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.

        ## Equivalent
        >>> Pddt.fromtimestamp(ts, size=size, tz=utils.UTC)
        """
        return cls.fromtimestamp(
            ts, size=size, tz=utils.UTC, as_unit=as_unit, name=name
        )

    @classmethod
    def fromisoformat(
        cls,
        dtstr: str | object,
        size: int | Any | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from ISO format strings `<'Pddt'>`.

        :param dtstr `<'str/Array-like'>`: The ISO format datetime string(s) to construct with.

            - `<'str'>` A ISO format datetime string.
            - `<'Array-like'>` An array-like object containing elements representing the datetime strings.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `dtstr` is a literal string ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `dtstr` is an array-like object.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.
        """
        # String -> list[str]
        if isinstance(dtstr, str):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromisoformat(size)",
                    "When 'dtstr' is a literal string, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            dtstr = [dtstr for _ in range(size_i)]

        # Array-like
        try:
            return cls._new(dtstr, as_unit=as_unit, name=name)
        except Exception as err:
            errors.raise_argument_error(cls, "fromisoformat(...)", None, err)

    @classmethod
    def fromisocalendar(
        cls,
        iso: dict | list | tuple | pd.DataFrame,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from ISO calendar values `<'Pddt'>`.

        :param iso `<'dict/list/tuple/DataFrame'>`: The ISO calendar values to construct with.

            - `<'dict'>` A dictionary containing the ISO calendar values with keys:
                `'year'`, `'week'` and `'weekday'` (or `'day'`).
            - `<'list/tuple'>` A list or tuple of dictionaries, each containing the ISO calendar values.
            - `<'DataFrame'>` A pandas DataFrame with columns: `'year'`, `'week'` and `'weekday'` (or `'day'`).

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `iso` is a dict ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `iso` is a dictionary.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        """
        # dict
        if isinstance(iso, dict):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromisocalendar(iso)",
                    "When 'iso' is a dictionary, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            us: cython.longlong = _parse_us_from_iso_dict(cls, iso)
            arr: np.ndarray = utils.dt64arr_fr_int64(us, size_i, "us")
            return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

        # list / tuple
        if isinstance(iso, (list, tuple)):
            size_i: cython.Py_ssize_t = len(iso)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for o in iso:
                if isinstance(o, dict):
                    us: cython.longlong = _parse_us_from_iso_dict(cls, o)
                else:
                    errors.raise_argument_error(
                        cls,
                        "fromisocalendar(iso)",
                        "Expects dict element from %s, got '%s' %s."
                        % (type(iso).__name__, o, type(o)),
                    )
                    return  # unreachable: suppress compiler warning
                arr_p[i] = us
                i += 1
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # DataFrame
        if isinstance(iso, pd.DataFrame):
            size_i: cython.Py_ssize_t = len(iso)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for row in iso.to_dict(orient="records"):
                arr_p[i] = _parse_us_from_iso_dict(cls, row)
                i += 1
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # Unsupported type
        errors.raise_type_error(
            cls,
            "fromisocalendar(iso)",
            "Unsupported 'iso' data type %s." % type(iso),
        )

    @classmethod
    def fromdayofyear(
        cls,
        doy: dict | list | tuple | pd.DataFrame,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from day-of-year values `<'Pddt'>`.

        :param doy `<'dict/list/tuple/DataFrame'>`: The day-of-year values to construct with.

            - `<'dict'>` A dictionary containing the day-of-year values with keys:
                `'year'` and `'doy'` (or `'day'`).
            - `<'list/tuple'>` A list or tuple of dictionaries, each containing the day-of-year values.
            - `<'DataFrame'>` A pandas DataFrame with columns: `'year'` and `'doy'` (or `'day'`).

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `doy` is a dict ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `doy` is a dictionary.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        """
        # dict
        if isinstance(doy, dict):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromdayofyear(doy)",
                    "When 'doy' is a dictionary, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            us: cython.longlong = _parse_us_from_doy_dict(cls, doy)
            arr: np.ndarray = utils.dt64arr_fr_int64(us, size_i, "us")
            return cls._new(arr, tz=tz, as_unit=as_unit, name=name)

        # list / tuple
        if isinstance(doy, (list, tuple)):
            size_i: cython.Py_ssize_t = len(doy)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for o in doy:
                if isinstance(o, dict):
                    us: cython.longlong = _parse_us_from_doy_dict(cls, o)
                else:
                    errors.raise_argument_error(
                        cls,
                        "fromdayofyear(doy)",
                        "Expects dict element from %s, got '%s' %s."
                        % (type(doy).__name__, o, type(o)),
                    )
                    return  # unreachable: suppress compiler warning
                arr_p[i] = us
                i += 1
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # DataFrame
        if isinstance(doy, pd.DataFrame):
            size_i: cython.Py_ssize_t = len(doy)
            arr: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_INT64, 0)
            arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
            i: cython.Py_ssize_t = 0
            for row in doy.to_dict(orient="records"):
                arr_p[i] = _parse_us_from_doy_dict(cls, row)
                i += 1
            return cls._new(
                arr.astype(utils.DT64_DTYPE_US), tz=tz, as_unit=as_unit, name=name
            )

        # Unsupported type
        errors.raise_type_error(
            cls,
            "fromdayofyear(doy)",
            "Unsupported 'doy' data type %s." % type(doy),
        )

    @classmethod
    def fromdate(
        cls,
        date: datetime.date | object,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from instances of date `<'Pddt'>`.

        :param date `<'date/Array-like'>`: The date-like object(s) to construct with.

            - `<'datetime.date'>` An instance or subclass of `datetime.date`.
            - `<'Array-like'>` An array-like object containing elements of date-like objects.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `date` is a date instance ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `date` is an array-like object.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.
        """
        # date
        if utils.is_date(date):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromdate(size)",
                    "When 'date' is a date instance, 'size' must be specified.",
                )
            size_i = _parse_size(cls, size)
            date = [date for _ in range(size_i)]

        # Array-like
        try:
            return cls._new(date, tz=tz, as_unit=as_unit, name=name)
        except Exception as err:
            errors.raise_argument_error(cls, "fromdate(...)", None, err)

    @classmethod
    def fromdatetime(
        cls,
        dt: datetime.datetime | np.datetime64 | object,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from instances of datetime `<'Pddt'>`.

        :param dt `<'Datetime-Like/Array-like'>`: The datetime-like object(s) to construct with.

            - `<'datetime.datetime'>` An instance or subclass of `datetime.datetime`.
            - `<'np.datetime64'>` An instance of `np.datetime64`.
            - `<'Array-like'>` An array-like object containing elements of the datetime-like objects.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `dt` is a datetime-like object). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `dt` is an array-like object.

        :param tz `<'tzinfo/str/None'>`: The optional timezone to `attach`. Defaults to `None`.

            - `<'None'>` Timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.
        """
        # datetime / datetime64 / str
        if isinstance(dt, (datetime.datetime, np.datetime64, str)):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "fromdatetime(size)",
                    "When 'dt' is a datetime-like instance, 'size' must be specified.",
                )
            size_i = _parse_size(cls, size)
            dt = [dt for _ in range(size_i)]

        # Array-like
        try:
            return cls._new(dt, tz=tz, as_unit=as_unit, name=name)
        except Exception as err:
            errors.raise_argument_error(cls, "fromdatetime(...)", None, err)

    @classmethod
    def fromdatetime64(
        cls,
        dt64: datetime.datetime | np.datetime64 | object,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from instances of datetime `<'Pddt'>`.

        - Alias of `fromdatetime()`.
        """
        return cls.fromdatetime(dt64, size=size, tz=tz, as_unit=as_unit, name=name)

    @classmethod
    def strptime(
        cls,
        dtstr: str | object,
        fmt: str,
        size: int | Any | None = None,
        as_unit: str = None,
        name: Hashable | None = None,
    ) -> Self:
        """Construct an index from parsing datetime-strings `<'Pddt'>`.

        :param dtstr `<'str/Array-like'>`: The datetime string(s) to construct with.

            - `<'str'>` A datetime string.
            - `<'Array-like'>` An array-like object containing elements of the datetime strings.

        :param format `<'str'>`: The format used to parse the strings.

        :param size `<'int/Any/None'>`: The target size of the index
            (required when `dtstr` is a literal string ). Defaults to `None`.

            - `<'int'>` A positive integer number.
            - `<'Any'>` Takes the `len(size)` value as the index size.
            - `<'None'>` Ignored when `dtstr` is an array-like object.

        :param as_unit `<'str/None'>`: Convert to specified datetime unit after construction. Defaults to `None`.
            Supports: `'s'`, `'ms'`, `'us'`, `'ns'`.

        :param name `<'Hashable/None'>`: Optional name of the index. Defaults to `None`.

        :returns `<'Pddt'>`: The resulting datetime index.

        ## Notice
        - This method only construct `datetime64[us]` index (microsecond resolution).
        - Parameter `as_unit` converts it to other datetime units after construction.
        """
        # String
        if isinstance(dtstr, str):
            if size is None:
                errors.raise_argument_error(
                    cls,
                    "strptime(dtstr)",
                    "When 'dtstr' is a literal string, 'size' must be specified.",
                )
            size_i: cython.Py_ssize_t = _parse_size(cls, size)
            try:
                dt = datetime.datetime.strptime(dtstr, fmt)
            except Exception as err:
                errors.raise_argument_error(cls, "strptime(dtstr, fmt)", None, err)
                return  # unreachable: suppress compiler warning
            return cls._new([dt for _ in range(size_i)], as_unit=as_unit, name=name)

        # Array-like
        if isinstance(dtstr, (list, tuple, pd.Index, pd.Series, np.ndarray)):
            dts: list = []
            for o in dtstr:
                try:
                    dt = datetime.datetime.strptime(o, fmt)
                except Exception as err:
                    errors.raise_argument_error(
                        cls,
                        "strptime(dtstr, fmt)",
                        "Connot parse element '%s' from %s."
                        % (o, type(dtstr).__name__),
                        err,
                    )
                    return  # unreachable: suppress compiler warning
                dts.append(dt)
            return cls._new(dts, as_unit=as_unit, name=name)

        # Unsupported type
        errors.raise_type_error(
            cls,
            "strptime(dtstr)",
            "Unsupported 'dtstr' data type %s." % type(dtstr),
        )

    # Convertor ----------------------------------------------------------------------------
    def ctime(self) -> pd.Index[str]:
        """Return ctime-stype string index `<'Index[str]'>`.

        - ctime-stype: 'Tue Oct 1 08:19:05 2024'
        """
        return self.strftime("%a %b %d %H:%M:%S %Y")

    def strftime(self, fmt: str) -> pd.Index[str]:
        """Format to index of strings according to the given format `<'str'>`.

        :param fmt `<'str'>`: The format, e.g.: `'%d/%m/%Y, %H:%M:%S'`.
        :returns `<'Index[str]'>`: The formatted index of strings.
        """
        try:
            return DatetimeIndex.strftime(self, fmt)
        except Exception as err:
            errors.raise_argument_error(self.__class__, "strftime(fmt)", None, err)

    def isoformat(self, sep: str = "T") -> pd.Index[str]:
        """Return the date and time formatted according to ISO format `<'str'>`.

        :param sep `<'str'>`: The separator between date and time components. Defaults to `'T'`.
        :returns `<'Index[str]'>`: Index of ISO formatted strings.
        """
        return self.strftime(f"%Y-%m-%d{sep}%H:%M:%S.%f%z")

    def timedf(self) -> pd.DataFrame:
        """Return `local` time DataFrame compatible with `time.localtime()` `<'DataFrame'>`.

        ## Example
        >>> pt.timedf()
        ```
        _  tm_year  tm_mon  tm_mday  tm_hour  tm_min  tm_sec  tm_wday  tm_yday
        0     2025      11       12       18      12      42        2      316
        ...
        ```
        """
        arr: np.ndarray = self.values_naive
        unit: cython.int = utils.get_arr_nptime_unit(arr)
        return pd.DataFrame(
            {
                "tm_year": utils.dt64arr_year(arr, unit, 0, True),
                "tm_mon": utils.dt64arr_month(arr, unit, 0, True),
                "tm_mday": utils.dt64arr_day(arr, unit, 0, True),
                "tm_hour": utils.dt64arr_hour(arr, unit, 0, True),
                "tm_min": utils.dt64arr_minute(arr, unit, 0, True),
                "tm_sec": utils.dt64arr_second(arr, unit, 0, True),
                "tm_wday": utils.dt64arr_weekday(arr, unit, 0, True),
                "tm_yday": utils.dt64arr_day_of_year(arr, unit, True),
            },
        )

    def utctimedf(self) -> pd.DataFrame:
        """Return `UTC` time DataFrame compatible with `time.gmtime()` `<'DataFrame'>`.

        ## Example
        >>> pt.timedf()
        ```
        _  tm_year  tm_mon  tm_mday  tm_hour  tm_min  tm_sec  tm_wday  tm_yday
        0     2025      11       12       10      12      42        2      316
        ...
        ```
        """
        tz: object = self.tzinfo
        if tz is None or tz is utils.UTC:
            return self.timedf()
        else:
            return self.tz_convert(utils.UTC).timedf()

    def toordinal(self) -> pd.Index[np.int64]:
        """Return an index of proleptic Gregorian ordinals from the dates `<'Index[int64]'>`.

        - Only the year, month and day values contribute to the result.
        - '0001-01-01' is day 1.
        """
        arr = utils.dt64arr_to_ord(self.values_naive, -1, 0, True)
        return pd.Index(arr, name="ordinal")

    def toseconds(self, utc: cython.bint = False) -> pd.Index[np.float64]:
        """Return an index of total seconds since epoch `<'Index[float64]'>`.

        :param utc `<'bool'>`: Whether to subtract the UTC offset. Defaults to `False`.

            - When `True` and the datetime index is `timezone-aware`, subtract
              the UTC offset first (i.e., normalize to UTC) before computing the
              epoch difference.
            - For `naive` datetime index this flag is ignored.

        :returns `<'Index[float64]'>`: Seconds since epoch.

        ## Notes
        - Unlike `timestamp()`, this method never assumes local time for
          naive datetimes index. Naive values are interpreted `as-is`
          without any local-time conversion.
        - For aware datetime index, offset handling (including DST folds/gaps)
          follows the attached timezone.
        """
        if self.tzinfo is None:
            arr = self.values
        elif not utc:
            arr = self.values_naive
        else:
            arr = self.tz_convert(utils.UTC).values_naive
        return pd.Index(utils.dt64arr_to_ts(arr, -1, True), name="seconds")

    def tomicroseconds(self, utc: cython.bint = False) -> pd.Index[np.int64]:
        """Return an index of total microseconds since epoch `<'Index[float64]'>`.

        :param utc `<'bool'>`: Whether to subtract the UTC offset. Defaults to `False`.

            - When `True` and the datetime index is `timezone-aware`, subtract
              the UTC offset first (i.e., normalize to UTC) before computing the
              epoch difference.
            - For `naive` datetime index this flag is ignored.

        :returns `<'Index[float64]'>`: Microseconds since epoch.

        ## Notes
        - Unlike `timestamp()`, this method never assumes local time for
          naive datetimes index. Naive values are interpreted `as-is`
          without any local-time conversion.
        - For aware datetime index, offset handling (including DST folds/gaps)
          follows the attached timezone.
        """
        if self.tzinfo is None:
            arr = self.values
        elif not utc:
            arr = self.values_naive
        else:
            arr = self.tz_convert(utils.UTC).values_naive
        return pd.Index(
            utils.dt64arr_as_int64_us(arr, -1, 0, True), name="microseconds"
        )

    def timestamp(self) -> pd.Index[np.float64]:
        """Return an index of POSIX timestamps `<'Index[float64]'>`."""
        # fmt: off
        if self.tzinfo is None:
            arr = self.tz_localize(utils.tz_local(), "infer", "shift_forward").values
        else:
            arr = self.values
        # fmt: on
        return pd.Index(utils.dt64arr_to_ts(arr, -1, True), name="timestamp")

    def datetime(self) -> np.ndarray[Pydt]:
        """Return an array of datetime `<'ndarray[Pydt]'>`.

        - Alias of `to_pydatetime()`, but returns array of `Pydt` instead of `datetime.datetime`.
        """
        # Convert to microseconds array
        arr: np.ndarray = utils.dt64arr_as_int64_us(self.values_naive, -1, 0, True)
        arr_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(arr))
        size_i: cython.Py_ssize_t = arr.shape[0]

        # Setup output array
        tz: object = self.tzinfo
        out: np.ndarray = np.PyArray_EMPTY(1, [size_i], np.NPY_TYPES.NPY_OBJECT, 0)
        i: cython.Py_ssize_t
        v: np.npy_int64
        for i in range(size_i):
            v = arr_p[i]
            # Preserve NaT
            if v == utils.LLONG_MIN:
                out[i] = utils.NAT
                continue
            # Create Pydt
            out[i] = Pydt.frommicroseconds(v, tz)

        return out

    def date(self) -> np.ndarray[datetime.date]:
        """Return an array of date `<'ndarray[date]'>`."""
        return super(Pddt, self).date

    def time(self) -> np.ndarray[datetime.time]:
        """Return an array of time (without timezone information) `<'ndarray[time]'>`."""
        return super(Pddt, self).time

    def timetz(self) -> np.ndarray[datetime.time]:
        """Return an array of time (with the same timezone information) `<'ndarray[time]'>`."""
        return super(Pddt, self).timetz

    # Manipulator --------------------------------------------------------------------------
    def replace(
        self,
        year: cython.int = -1,
        month: cython.int = -1,
        day: cython.int = -1,
        hour: cython.int = -1,
        minute: cython.int = -1,
        second: cython.int = -1,
        microsecond: cython.int = -1,
        nanosecond: cython.int = -1,
        tzinfo: datetime.tzinfo | str | None = -1,
    ) -> Self:
        """Replace the specified datetime fields with new values `<'Pddt'>`.

        :param year `<'int'>`: Absolute year. Defaults to `SENTINEL` (no change).
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
        :param nanosecond `<'int'>`: Absolute nanosecond. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..999].
        :param tzinfo `<'tzinfo/None'>`: The timeone. Defaults to `SENTINEL` (no change).

            - `<'None'>`: removes tzinfo (makes datetime index naive).
            - `<'str'>`: Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>`: A subclass of `datetime.tzinfo`.

        :returns `<'Pddt'>`: The resulting datetime index after applying the specified field replacements.

        ## Behavior
        - Replacements are `component-wise`:
            * Any of the date fields may be left as `<= 0` to keep original values.
            * Any of the time fields may be left as `< 0` to keep original values.
            * If `tzinfo` is left as `SENTINEL`, the original timezone is retained.
        - Day values are `clamped` to the maximum valid day in the resulting month.
        - Only time components within the index resolution are modified;
          e.g., when index is in `'s'` resolution, `microsecond` and `nanosecond`
          replacements are ignored.
        - Timezone handling:
            * If `tzinfo` is `SENTINEL`, the original timezone is retained.
            * If `tzinfo` is `None`, the resulting datetime index will be localized to `naive`,
              without affecting the datetime values.
            * If `tzinfo` is specified and different from the original timezone,
              the resulting datetime index will be replaced with the new timezone,
              preserving the original datetime values.

        ## Equivalent
        >>> datetime.datetime.replace()
        """
        # Fast-path
        # . retain timezone
        if isinstance(tzinfo, int):
            return self.to_datetime(
                year, month, day, hour, minute, second, microsecond, nanosecond
            )
        # . same timezone
        tzinfo: object = utils.tz_parse(tzinfo)
        tz: object = self.tzinfo
        if tzinfo is tz:
            return self.to_datetime(
                year, month, day, hour, minute, second, microsecond, nanosecond
            )

        # Replace datetime (timezone-naive)
        pt = self if tz is None else self.tz_localize(None)
        pt = pt.to_datetime(
            year, month, day, hour, minute, second, microsecond, nanosecond
        )

        # Replace timezone
        # . timezone-aware -> naive
        if tzinfo is None:
            return pt.tz_localize(None)
        # . timezone-naive/aware -> aware
        return pt.tz_localize(tzinfo, "infer", "shift_forward")

    # . year
    def to_curr_year(
        self,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> Self:
        """Adjust the date to the specified month and day in the current year `<'Pddt'>`.

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pddt'>`: The adjusted datetime index in the current year.

        ## Example
        >>> pt.to_curr_year(month="Feb", day=31)    # The last day of February in the current year
        >>> pt.to_curr_year(month=11)               # The same day of November in the current year
        >>> pt.to_curr_year(day=1)                  # The 1st day of the current month
        """
        # Fast-path: no month adjustment
        mm: cython.int = _parse_month(month, None, True)
        if mm == -1:
            return self.to_curr_month(day)

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[Y] -> int64[M]
        dateY = utils.dt64arr_as_int64_Y(arr, my_reso, 0, True)
        dateM = utils.dt64arr_as_int64_M(dateY, utils.DT_NPY_UNIT_YY, mm - 1, False)
        # . retain original days -> int64[D]
        if day < 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min_arr(delta, utils.dt64arr_day(arr, my_reso), 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . 1st day -> int64[D]
        elif day == 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)
        # . days before 29
        elif day < 29:
            dateD = utils.dt64arr_as_int64_D(
                dateM, utils.DT_NPY_UNIT_MM, day - 1, False
            )
        # . days before 31 -> int64[D]
        elif day < 31:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min(delta, day, 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . last day -> int64[D]
        else:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_prev_year(
        self,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> Self:
        """Adjust the date to the specified month and day in the previous year `<'Pddt'>`.

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pddt'>`: The adjusted datetime index in the previous year.

        ## Example
        >>> pt.to_prev_year(month="Feb", day=31)    # The last day of February in the previous year
        >>> pt.to_prev_year(month=11)               # The same day of November in the previous year
        >>> pt.to_prev_year(day=1)                  # The 1st day of the previous month
        """
        return self.to_year(-1, month, day)

    def to_next_year(
        self,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> Self:
        """Adjust the date to the specified month and day in the next year `<'Pddt'>`.

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pddt'>`: The adjusted datetime index in the next year.

        ## Example
        >>> pt.to_next_year(month="Feb", day=31)    # The last day of February in the next year
        >>> pt.to_next_year(month=11)               # The same day of November in the next year
        >>> pt.to_next_year(day=1)                  # The 1st day of the next month
        """
        return self.to_year(1, month, day)

    def to_year(
        self,
        offset: cython.int,
        month: int | str | None = None,
        day: cython.int = -1,
    ) -> Self:
        """Adjust the date to the specified month and day in the year (+/-) offset `<'Pddt'>`.

        :param offset `<'int'>`: The year offset (+/-).

        :param month `<'int/str/None'>`: Month value. Defaults to `None`.

            - `<'int'>` Month number (1=Jan...12=Dec).
            - `<'str'>` Month name (case-insensitive), e.g., 'Jan', 'februar', '三月'.
            - `<'None'>` Retains the original month.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pddt'>`: The adjusted datetime index.

        ## Example
        >>> pt.to_year(-2, "Feb", 31)  # The last day of February, two years ago
        >>> pt.to_year(2, 11)          # The same day of November, two years later
        >>> pt.to_year(2, day=1)       # The 1st day of the current month, two years later
        """
        # Fast-path: no offset
        if offset == 0:
            return self.to_curr_year(month, day)

        # Access datetime array & info
        mm: cython.int = _parse_month(month, None, True)
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[Y] + offset -> int64[M]
        dateY = utils.dt64arr_as_int64_Y(arr, my_reso, offset, True)
        dateM = utils.dt64arr_as_int64_M(dateY, utils.DT_NPY_UNIT_YY, 0, False)
        # . retain original month -> int64[M]
        if mm == -1:
            delta = utils.dt64arr_month(arr, my_reso, 0, True)
            dateM = utils.arr_add_arr(dateM, delta, -1, False)
        # . replace with new month -> int64[M]
        else:
            dateM = utils.arr_add(dateM, mm - 1, False)
        # . retain original days -> int64[D]
        if day < 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min_arr(delta, utils.dt64arr_day(arr, my_reso), 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . 1st day -> int64[D]
        elif day == 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)
        # . days before 29
        elif day < 29:
            dateD = utils.dt64arr_as_int64_D(
                dateM, utils.DT_NPY_UNIT_MM, day - 1, False
            )
        # . days before 31 -> int64[D]
        elif day < 31:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min(delta, day, 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . last day -> int64[D]
        else:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    # . quarter
    def to_curr_quarter(self, month: cython.int = -1, day: cython.int = -1) -> Self:
        """Adjust the date to the specified month-of-quarter and day in the current quarter. `<'Pddt'>`.

        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pddt'>`: The adjusted datetime index in the current quarter.

        ## Example
        >>> pt.to_curr_quarter(month=1, day=31) # The last day of the 1st quarter month in the current quarter
        >>> pt.to_curr_quarter(month=2)         # The same day of the 2nd quarter month in the current quarter
        >>> pt.to_curr_quarter(day=1)           # The 1st day of the current month-of-quarter in the current quarter
        """
        # Fast-path: no month adjustment
        if month < 1:
            return self.to_curr_month(day)

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[Q] -> int64[M] + offset
        dateQ = utils.dt64arr_as_int64_Q(arr, my_reso, 0, True)
        dateM = utils.arr_mul(dateQ, 3, min(month, 3) - 1, False)
        # . retain original days -> int64[D]
        if day < 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min_arr(delta, utils.dt64arr_day(arr, my_reso), 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . 1st day -> int64[D]
        elif day == 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)
        # . days before 29
        elif day < 29:
            dateD = utils.dt64arr_as_int64_D(
                dateM, utils.DT_NPY_UNIT_MM, day - 1, False
            )
        # . days before 31 -> int64[D]
        elif day < 31:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min(delta, day, 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . last day -> int64[D]
        else:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_prev_quarter(self, month: cython.int = -1, day: cython.int = -1) -> Self:
        """Adjust the date to the specified month-of-quarter and day in the previous quarter. `<'Pddt'>`.

        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pddt'>`: The adjusted datetime index in the previous quarter.

        ## Example
        >>> pt.to_prev_quarter(month=1, day=31) # The last day of the 1st quarter month in the previous quarter
        >>> pt.to_prev_quarter(month=2)         # The same day of the 2nd quarter month in the previous quarter
        >>> pt.to_prev_quarter(day=1)           # The 1st day of the current month-of-quarter in the previous quarter
        """
        return self.to_quarter(-1, month, day)

    def to_next_quarter(self, month: cython.int = -1, day: cython.int = -1) -> Self:
        """Adjust the date to the specified month-of-quarter and day in the next quarter. `<'Pddt'>`.

        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pddt'>`: The adjusted datetime index in the next quarter.

        ## Example
        >>> pt.to_next_quarter(month=1, day=31) # The last day of the 1st quarter month in the next quarter
        >>> pt.to_next_quarter(month=2)         # The same day of the 2nd quarter month in the next quarter
        >>> pt.to_next_quarter(day=1)           # The 1st day of the current month-of-quarter in the next quarter
        """
        return self.to_quarter(1, month, day)

    def to_quarter(
        self,
        offset: cython.int,
        month: cython.int = -1,
        day: cython.int = -1,
    ) -> Self:
        """Adjust the date to the specified month-of-quarter and day in the quarter (+/-) offset `<'Pddt'>`.

        :param offset `<'int'>`: The quarter offset (+/-).
        :param month `<'int'>`: Month of the quarter, automatically clamped to `[1..3]`.
            Defaults to `SENTINEL` (retains the original month-of-quarter).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pddt'>`: The adjusted datetime index.

        ## Example
        >>> pt.to_quarter(-2, 1, 31)  # The last day of the 1st quarter month, two quarters ago
        >>> pt.to_quarter(2, 2)       # The same day of the 2nd quarter month, two quarters later
        >>> pt.to_quarter(2, day=1)   # The 1st day of the current month-of-quarter, two quarters later
        """
        # Fast-path: no offset
        if offset == 0:
            return self.to_curr_quarter(month, day)

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[M]
        # . retain original month-of-quarter
        if month < 1:
            dateM = utils.dt64arr_as_int64_M(arr, my_reso, offset * 3, True)
        # . replace with new month-of-quarter
        else:
            dateQ = utils.dt64arr_as_int64_Q(arr, my_reso, 0, True)
            dateM = utils.arr_mul(dateQ, 3, offset * 3 + min(month, 3) - 1, False)
        # . retain original days -> int64[D]
        if day < 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min_arr(delta, utils.dt64arr_day(arr, my_reso), 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . 1st day -> int64[D]
        elif day == 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)
        # . days before 29
        elif day < 29:
            dateD = utils.dt64arr_as_int64_D(
                dateM, utils.DT_NPY_UNIT_MM, day - 1, False
            )
        # . days before 31 -> int64[D]
        elif day < 31:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min(delta, day, 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . last day -> int64[D]
        else:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    # . month
    def to_curr_month(self, day: cython.int = -1) -> Self:
        """Adjust the date to the specified day of the current month `<'Pddt'>`.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pddt'>`: The adjusted datetime index in the current month.

        ## Example
        >>> pt.to_curr_month(31)  # The last day of the current month
        >>> pt.to_curr_month(1)   # The 1st day of the current month
        """
        # Fast-path: no adjustment
        if day < 1:
            return self  # exit

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[M]
        dateM = utils.dt64arr_as_int64_M(arr, my_reso, 0, True)
        # . 1st day -> int64[D]
        if day == 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)
        # . days before 29 -> int64[D]
        elif day < 29:
            dateD = utils.dt64arr_as_int64_D(
                dateM, utils.DT_NPY_UNIT_MM, day - 1, False
            )
        # . days before 31 -> int64[D]
        elif day < 31:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min(delta, day, 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . last day -> int64[D]
        else:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_prev_month(self, day: cython.int = -1) -> Self:
        """Adjust the date to the specified day of the previous month `<'Pddt'>`.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pddt'>`: The adjusted datetime index in the previous month.

        ## Example
        >>> pt.to_prev_month(31)  # The last day of the previous month
        >>> pt.to_prev_month(1)   # The 1st day of the previous month
        """
        return self.to_month(-1, day)

    def to_next_month(self, day: cython.int = -1) -> Self:
        """Adjust the date to the specified day of the next month `<'Pddt'>`.

        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.

        :returns `<'Pddt'>`: The adjusted datetime index in the next month.

        ## Example
        >>> pt.to_next_month(31)  # The last day of the next month
        >>> pt.to_next_month(1)   # The 1st day of the next month
        """
        return self.to_month(1, day)

    def to_month(self, offset: cython.int, day: cython.int = -1) -> Self:
        """Adjust the date to the specified day of the month (+/-) offset `<'Pddt'>`.

        :param offset `<'int'>`: The month offset (+/-).
        :param day `<'int'>`: Day value (1-31). Defaults to `SENTINEL` (no change).
            The final day value is automatically clamped to the maximum days in the month.
        :returns `<'Pddt'>`: The adjusted datetime index.

        ## Example
        >>> pt.to_month(-2, 31)  # The last day of the month, two months ago
        >>> pt.to_month(2, 1)    # The 1st day of the month, two months later
        """
        # Fast-path: no offset
        if offset == 0:
            return self.to_curr_month(day)

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[M] + offset
        dateM = utils.dt64arr_as_int64_M(arr, my_reso, offset, True)
        # . retain original days -> int64[D]
        if day < 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min_arr(delta, utils.dt64arr_day(arr, my_reso), 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . 1st day -> int64[D]
        elif day == 1:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)
        # . days before 29 -> int64[D]
        elif day < 29:
            dateD = utils.dt64arr_as_int64_D(
                dateM, utils.DT_NPY_UNIT_MM, day - 1, False
            )
        # . days before 31 -> int64[D]
        elif day < 31:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            delta = utils.arr_min(delta, day, 0, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)
        # . last day -> int64[D]
        else:
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, True)
            delta = utils.dt64arr_days_in_month(dateM, utils.DT_NPY_UNIT_MM, False)
            dateD = utils.arr_add_arr(dateD, delta, -1, False)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    # . weekday
    def to_monday(self) -> Self:
        """Adjust the date to the `Monday` of the current week `<'Pddt'>`."""
        return self._to_curr_weekday(0)

    def to_tuesday(self) -> Self:
        """Adjust the date to the `Tuesday` of the current week `<'Pddt'>`."""
        return self._to_curr_weekday(1)

    def to_wednesday(self) -> Self:
        """Adjust the date to the `Wednesday` of the current week `<'Pddt'>`."""
        return self._to_curr_weekday(2)

    def to_thursday(self) -> Self:
        """Adjust the date to the `Thursday` of the current week `<'Pddt'>`."""
        return self._to_curr_weekday(3)

    def to_friday(self) -> Self:
        """Adjust the date to the `Friday` of the current week `<'Pddt'>`."""
        return self._to_curr_weekday(4)

    def to_saturday(self) -> Self:
        """Adjust the date to the `Saturday` of the current week `<'Pddt'>`."""
        return self._to_curr_weekday(5)

    def to_sunday(self) -> Self:
        """Adjust the date to the `Sunday` of the current week `<'Pddt'>`."""
        return self._to_curr_weekday(6)

    def to_curr_weekday(self, weekday: int | str | None = None) -> Self:
        """Adjust the date to the specific weekday of the current week `<'Pddt'>`.

        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pddt'>`: The adjusted datetime index in the current week.

        ## Example
        >>> pt.to_curr_weekday(0)      # The Monday of the current week
        >>> pt.to_curr_weekday("Tue")  # The Tuesday of the current week
        """
        return self._to_curr_weekday(_parse_weekday(weekday, None, True))

    def to_prev_weekday(self, weekday: int | str | None = None) -> Self:
        """Adjust the date to the specific weekday of the previous week `<'Pddt'>`.

        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pddt'>`: The adjusted datetime index in the previous week.

        ## Example
        >>> pt.to_prev_weekday(0)      # The Monday of the previous week
        >>> pt.to_prev_weekday("Tue")  # The Tuesday of the previous week
        """
        return self.to_weekday(-1, weekday)

    def to_next_weekday(self, weekday: int | str | None = None) -> Self:
        """Adjust the date to the specific weekday of the next week `<'Pddt'>`.

        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pddt'>`: The adjusted datetime index in the next week.

        ## Example
        >>> pt.to_next_weekday(0)      # The Monday of the next week
        >>> pt.to_next_weekday("Tue")  # The Tuesday of the next week
        """
        return self.to_weekday(1, weekday)

    def to_weekday(self, offset: cython.int, weekday: int | str | None = None) -> Self:
        """Adjust the date to the specific weekday of the week (+/-) offset `<'Pddt'>`.

        :param offset `<'int'>`: The week offset (+/-).

        :param weekday `<'int/str/None'>`: Weekday value. Defaults to `None`.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').
            - `<'None'>` Retains the original weekday.

        :returns `<'Pddt'>`: The adjusted datetime index.

        ## Example
        >>> pt.to_weekday(-2, 0)     # The Monday of the week, two weeks ago
        >>> pt.to_weekday(2, "Tue")  # The Tuesday of the week, two weeks later
        >>> pt.to_weekday(2)         # The same weekday of the week, two weeks later
        """
        # Fast-path: no offset
        wkd: cython.int = _parse_weekday(weekday, None, True)
        if offset == 0:
            return self._to_curr_weekday(wkd)

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[D]
        dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
        # . retain original weekday
        if wkd == -1:
            dateD = utils.arr_add(dateD, offset * 7, False)
        # . replace with new weekday
        else:
            delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
            dateD = utils.arr_sub_arr(dateD, delta, offset * 7 + wkd, False)
            #: days - weekday + target_weekday + (offset * 7)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def _to_curr_weekday(self, weekday: cython.int) -> Self:
        """(internal) Adjust the date to the specific weekday of the current week `<'Pddt'>`.

        :param weekday `<'int'>`: Weekday number (0=Mon...6=Sun).
            Automatically clamped to [0..6]. If negative, no adjustment is made.
        :returns `<'Pddt'>`: The adjusted datetime index in the current week.
        """
        # Fast-path: no adjustment
        if weekday < 0:
            return self

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[D]
        dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
        delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
        dateD = utils.arr_sub_arr(dateD, delta, min(weekday, 6), False)
        #: days - weekday + target_weekday

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    # . day
    def to_yesterday(self) -> Self:
        """Adjust the date to `Yesterday` `<'Pddt'>`."""
        return self.to_day(-1)

    def to_tomorrow(self) -> Self:
        """Adjust the date to `Tomorrow` `<'Pddt'>`."""
        return self.to_day(1)

    def to_day(self, offset: cython.int) -> Self:
        """Adjust the date to day (+/-) offset `<'Pddt'>`.

        :param offset `<'int'>`: The day offset (+/-).
        :returns `<'Pddt'>`: The adjusted datetime index.

        ## Example
        >>> pt.to_day(-10)  # 10 days ago
        >>> pt.to_day(10)   # 10 days later
        """
        # Fast-path: no offset
        if offset == 0:
            return self

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # Adjust dates -> int64[D]
        dateD = utils.dt64arr_as_int64_D(arr, my_reso, offset, True)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    # . date&time
    def normalize(self):
        """Set the time fields to midnight (00:00:00) `<'Pddt'>`.

        - This method is useful in cases, when the time does not matter.
        - The timezone is unaffected.
        """
        return self.to_time(0, 0, 0, 0, 0)

    def snap(self, freq: object) -> Self:
        """Snap to nearest occurring frequency `<'Pddt'>`.

        Examples
        --------
        >>> idx = Pddt(['2023-01-01', '2023-01-02', '2023-02-01', '2023-02-02'])
        >>> idx
        Pddt(['2023-01-01', '2023-01-02', '2023-02-01', '2023-02-02'],
        dtype='datetime64[ns]', freq=None)
        >>> idx.snap('MS')
        Pddt(['2023-01-01', '2023-01-01', '2023-02-01', '2023-02-01'],
        dtype='datetime64[ns]', freq=None)
        """
        try:
            return self._new(DatetimeIndex.snap(self, freq))
        except Exception as err:
            errors.raise_argument_error(self.__class__, "snap(freq)", None, err)

    def to_datetime(
        self,
        year: cython.int = -1,
        month: cython.int = -1,
        day: cython.int = -1,
        hour: cython.int = -1,
        minute: cython.int = -1,
        second: cython.int = -1,
        microsecond: cython.int = -1,
        nanosecond: cython.int = -1,
    ) -> Self:
        """Adjust the date and time fields with new values,
        without affecting the timezone `<'Pddt'>`.

        :param year `<'int'>`: Absolute year. Defaults to `SENTINEL` (no change).
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
        :param nanosecond `<'int'>`: Absolute nanosecond. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..999].
        :returns `<'Pddt'>`: The resulting datetime with new specified field values.

        ## Behavior
        - Replacements are `component-wise`:
            * Any of the date fields may be left as `<= 0` to keep original values.
            * Any of the time fields may be left as `< 0` to keep original values.
        - Day values are `clamped` to the maximum valid day in the resulting month.
        - Only time components within the index resolution are modified;
          e.g., when index is in `'s'` resolution, `microsecond` and `nanosecond`
          replacements are ignored.

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
        # Fast-path
        # fmt: off
        if year <= 0 and month <= 0 and day <= 0:
            return self.to_time(hour, minute, second, microsecond, nanosecond)
        if hour < 0 and minute < 0 and second < 0 and microsecond < 0 and nanosecond < 0:
            return self.to_date(year, month, day)
        # fmt: on

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Replace dates -> int64[D]
        dateD = utils.dt64arr_replace_dates(arr, year, month, day, my_reso)

        # Set time to zero
        if (
            hour == 0
            and minute == 0
            and second == 0
            and microsecond == 0
            and nanosecond == 0
        ):
            # Combine dates & times
            # . my_unit[ns] & out of ns range -> int64[us]
            if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
                dateD, utils.DT_NPY_UNIT_DD
            ):
                arr = utils.arr_mul(dateD, utils.US_DAY, 0, False)
                dtype = utils.DT64_DTYPE_US
            # . my_unit safe -> int64[my_unit]
            else:
                arr = utils.dt64arr_as_int64(
                    dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
                )
                dtype = utils.nptime_unit_str2dt64(my_unit)

        # Replace times -> int64[my_unit]
        else:
            times = utils.dt64arr_replace_times(
                arr, hour, minute, second, microsecond, nanosecond, my_reso
            )

            # Combine dates & times
            # . my_unit[ns] & out of ns range -> int64[us]
            if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
                dateD, utils.DT_NPY_UNIT_DD
            ):
                dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
                times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
                dtype = utils.DT64_DTYPE_US
            # . my_unit safe -> int64[my_unit]
            else:
                dates = utils.dt64arr_as_int64(
                    dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
                )
                dtype = utils.nptime_unit_str2dt64(my_unit)
            arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_date(
        self,
        year: cython.int = -1,
        month: cython.int = -1,
        day: cython.int = -1,
    ) -> Self:
        """Adjust the date with new values, without affecting other fields `<'Pddt'>`.

        :param year `<'int'>`: Absolute year. Defaults to `SENTINEL` (no change).
        :param month `<'int'>`: Absolute month. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..12].
        :param day `<'int'>`: Absolute day. Defaults to `SENTINEL` (no change).
            If specified (greater than `0`), clamps to [1..maximum days the resulting month].
        :returns `<'Pddt'>`: The resulting datetime index with new specified date field values.

        ## Behavior
        - Replacements are `component-wise`: any of the date fields may be left
          as `<= 0` to keep original values.
        - Day values are `clamped` to the maximum valid day in the resulting month.

        ## Equivalent
        >>> pt.replace(year=year, month=month, day=day)
        """
        # Fast-path
        if year <= 0:
            # Repalce day
            if month <= 0:
                return self.to_curr_month(day)
            # Replace month & day
            return self.to_curr_year(month, day)

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso)  # int64[my_unit]

        # Replace date -> int64[D]
        dateD = utils.dt64arr_replace_dates(arr, year, month, day, my_reso)

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_time(
        self,
        hour: cython.int = -1,
        minute: cython.int = -1,
        second: cython.int = -1,
        microsecond: cython.int = -1,
        nanosecond: cython.int = -1,
    ) -> Self:
        """Adjust the time fields with new values, without affecting other fields `<'Pddt'>`.

        :param hour `<'int'>`: Absolute hour. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..23].
        :param minute `<'int'>`: Absolute minute. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param second `<'int'>`: Absolute second. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..59].
        :param microsecond `<'int'>`: Absolute microsecond. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..999999].
        :param nanosecond `<'int'>`: Absolute nanosecond. Defaults to `SENTINEL` (no change).
            If specified (greater than or equal to `0`), clamps to [0..999].
        :returns `<'Pddt'>`: The resulting datetime index with new specified time field values.

        ## Behavior
        - Replacements are `component-wise`: any of time fields may be left as `< 0`
          to keep original values.
        - Only time components within the index resolution are modified;
          e.g., when index is in `'s'` resolution, `microsecond` and `nanosecond`
          replacements are ignored.

        ## Equivalent
        >>> pt.replace(
                hour=hour,
                minute=minute,
                second=second,
                microsecond=microsecond,
                nanosecond=nanosecond,
            )
        """
        # Fast-path: no changes
        if (
            hour < 0
            and minute < 0
            and second < 0
            and microsecond < 0
            and nanosecond < 0
        ):
            return self

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate dates -> int64[D]
        dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)

        # Set time to zero
        if (
            hour == 0
            and minute == 0
            and second == 0
            and microsecond == 0
            and nanosecond == 0
        ):
            # Combine dates & times
            # . my_unit[ns] & out of ns range -> int64[us]
            if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
                dateD, utils.DT_NPY_UNIT_DD
            ):
                arr = utils.arr_mul(dateD, utils.US_DAY, 0, False)
                dtype = utils.DT64_DTYPE_US
            # . my_unit safe -> int64[my_unit]
            else:
                arr = utils.dt64arr_as_int64(
                    dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
                )
                dtype = utils.nptime_unit_str2dt64(my_unit)

        # Replace times -> int64[my_unit]
        else:
            times = utils.dt64arr_replace_times(
                arr, hour, minute, second, microsecond, nanosecond, my_reso
            )

            # Combine dates & times
            # . my_unit[ns] & out of ns range -> int64[us]
            if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
                dateD, utils.DT_NPY_UNIT_DD
            ):
                dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
                times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
                dtype = utils.DT64_DTYPE_US
            # . my_unit safe -> int64[my_unit]
            else:
                dates = utils.dt64arr_as_int64(
                    dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
                )
                dtype = utils.nptime_unit_str2dt64(my_unit)
            arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_first_of(self, unit: str) -> Self:
        """Adjust the date fields to the first day of the specified datetime unit,
        without affecting the time fields `<'Pddt'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → First day of the year: `YYYY-01-01`
            - `'Q'` → First day of the quarter: `YYYY-MM-01`
            - `'M'` → First day of the month: `YYYY-MM-01`
            - `'W'` → First day (Monday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → First day of the specifed month: `YYYY-MM-01`

        :returns `<'Pddt'>`: The adjusted datetime index.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self.__class__,
                "to_first_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W' or Month name; got None.",
            )
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 0:
            errors.raise_argument_error(
                self.__class__,
                "to_first_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W' or Month name; got empty string.",
            )

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso, 0, True)

        # To weekday -> int64[D]
        ch0: cython.Py_UCS4 = str_read(unit, 0)
        if ch0 == "W" and unit_len == 1:
            dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
            delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
            dateD = utils.arr_sub_arr(dateD, delta, 0, False)

        # To month -> int64[M] -> int64[D]
        elif ch0 == "M" and unit_len == 1:
            dateM = utils.dt64arr_as_int64_M(arr, my_reso, 0, True)
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)

        # To quarter -> int64[Q] -> int64[M] -> int64[D]
        elif ch0 == "Q" and unit_len == 1:
            dateQ = utils.dt64arr_as_int64_Q(arr, my_reso, 0, True)
            dateM = utils.arr_mul(dateQ, 3, 0, False)
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)

        # To year -> int64[Y] -> int64[D]
        elif ch0 == "Y" and unit_len == 1:
            dateY = utils.dt64arr_as_int64_Y(arr, my_reso, 0, True)
            dateD = utils.dt64arr_as_int64_D(dateY, utils.DT_NPY_UNIT_YY, 0, False)

        # Special
        else:
            # Month name -> int64[Y] -> int64[M] -> int64[D]
            val: cython.int = _parse_month(unit, None, False)
            if val != -1:
                dateY = utils.dt64arr_as_int64_Y(arr, my_reso, 0, True)
                dateM = utils.arr_mul(dateY, 12, val - 1, False)
                dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, 0, False)

            # Unsupported unit
            else:
                errors.raise_argument_error(
                    self.__class__,
                    "to_first_of(unit)",
                    "Supports: 'Y', 'Q', 'M', 'W' or Month name; got '%s'." % unit,
                )
                return  # unreachable: suppress compiler warning

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_last_of(self, unit: str) -> Self:
        """Adjust the date fields to the last day of the specified datetime unit,
        without affecting the time fields `<'Pddt'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → Last day of the year: `YYYY-12-31`
            - `'Q'` → Last day of the quarter: `YYYY-MM-(30..31)`
            - `'M'` → Last day of the month: `YYYY-MM-(28..31)`
            - `'W'` → Last day (Sunday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → Last day of the specifed month: `YYYY-MM-(28..31)`

        :returns `<'Pddt'>`: The adjusted datetime index.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self.__class__,
                "to_last_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W' or Month name; got None.",
            )
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 0:
            errors.raise_argument_error(
                self.__class__,
                "to_last_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W' or Month name; got empty string.",
            )

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)

        # Seperate times -> int64[my_unit]
        times = utils.dt64arr_times(arr, my_reso)  # int64[my_unit]

        # To weekday -> int64[D]
        ch0: cython.Py_UCS4 = str_read(unit, 0)
        if ch0 == "W" and unit_len == 1:
            dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
            delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
            dateD = utils.arr_sub_arr(dateD, delta, 6, False)
            #: days - weekday + 6

        # To month -> int64[M]+1 -> int64[D]-1
        elif ch0 == "M" and unit_len == 1:
            dateM = utils.dt64arr_as_int64_M(arr, my_reso, 1, True)
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, -1, False)

        # To quarter -> int64[Q]+1 -> int64[M] -> int64[D]-1
        elif ch0 == "Q" and unit_len == 1:
            dateQ = utils.dt64arr_as_int64_Q(arr, my_reso, 1, True)
            dateM = utils.arr_mul(dateQ, 3, 0, False)
            dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, -1, False)

        # To year -> int64[Y]+1 -> int64[D]-1
        elif ch0 == "Y" and unit_len == 1:
            dateY = utils.dt64arr_as_int64_Y(arr, my_reso, 1, True)
            dateD = utils.dt64arr_as_int64_D(dateY, utils.DT_NPY_UNIT_YY, -1, False)

        # Special
        else:
            # Month name -> int64[Y] -> int64[M]+1 -> int64[D]-1
            val: cython.int = _parse_month(unit, None, False)
            if val != -1:
                dateY = utils.dt64arr_as_int64_Y(arr, my_reso, 0, True)
                dateM = utils.arr_mul(dateY, 12, val, False)
                dateD = utils.dt64arr_as_int64_D(dateM, utils.DT_NPY_UNIT_MM, -1, False)

            # Unsupported unit
            else:
                errors.raise_argument_error(
                    self.__class__,
                    "to_last_of(unit)",
                    "Supports: 'Y', 'Q', 'M', 'W' or Month name; got '%s'." % unit,
                )
                return  # unreachable: suppress compiler warning

        # Combine dates & times
        # . my_unit[ns] & out of ns range -> int64[us]
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            dateD, utils.DT_NPY_UNIT_DD
        ):
            dates = utils.arr_mul(dateD, utils.US_DAY, 0, False)
            times = utils.arr_div_floor(times, utils.NS_MICROSECOND, 0, False)
            dtype = utils.DT64_DTYPE_US
        # . my_unit safe -> int64[my_unit]
        else:
            dates = utils.dt64arr_as_int64(
                dateD, my_unit, utils.DT_NPY_UNIT_DD, 0, False
            )
            dtype = utils.nptime_unit_str2dt64(my_unit)
        arr = utils.arr_add_arr(dates, times, 0, False)  # int64

        # New instance
        return self._new(arr.astype(dtype), tz=self.tz, name=self.name)

    def to_start_of(self, unit: str) -> Self:
        """Adjust the date & time fields to the start of the specified datetime unit `<'Pddt'>`.

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
            - `'us'` → Start of microsecond: `YYYY-MM-DD hh:mm:ss.uuuuuu`
            - `'ns'` → Return the instance `as-is`.
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                     → Start of the specifed month: `YYYY-MM-01 00:00:00`
            - `Weekday` (e.g., `'Mon'`, `'Tuesday'`, `'星期三'`)
                     → Start of the specifed weekday: `YYYY-MM-DD 00:00:00`

        :returns `<'Pddt'>`: The adjusted datetime index.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self.__class__,
                "to_start_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us', 'ns' "
                "or Month/Weekday name; got None.",
            )
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 0:
            errors.raise_argument_error(
                self.__class__,
                "to_start_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us', 'ns' "
                "or Month/Weekday name; got empty string.",
            )

        # Fast-path: 'ns' as-is
        ch0: cython.Py_UCS4 = str_read(unit, 0)
        if ch0 == "n" and unit_len == 2 and str_read(unit, 1) == "s":
            return self  # exit

        # General approach: 'Y', 'M', 'D', 'h', 'm', 's', 'ms', 'us'
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)
        to_reso: cython.int
        if (
            #: 'Y', 'M', 'D', 'h', 'm', 's'
            (unit_len == 1 and ch0 in ("Y", "M", "D", "h", "m", "s"))
            #: 'ms', 'us'
            or (unit_len == 2 and ch0 in ("m", "u") and str_read(unit, 1) == "s")
            #: 'min'
            or (
                unit_len == 3
                and ch0 == "m"
                and str_read(unit, 1) == "i"
                and str_read(unit, 2) == "n"
            )
        ):
            to_reso = utils.nptime_unit_str2int(unit)
            if my_reso <= to_reso:
                return self  # exit: already at or finer than target resolution
            arr: np.ndarray = self.values_naive
            arr = utils.dt64arr_as_int64(arr, unit, my_reso, 0, True)
            arr = utils.dt64arr_as_unit(arr, my_unit, to_reso, False, False)
            return self._new(arr, tz=self.tz, name=self.name)

        # To weekday -> int64[D]-weekday
        arr: np.ndarray = self.values_naive
        if ch0 == "W" and unit_len == 1:
            dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
            delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
            dates = utils.arr_sub_arr(dateD, delta, 0, False)
            to_reso = utils.DT_NPY_UNIT_DD

        # To quarter -> int64[Q] -> int64[M]
        elif ch0 == "Q" and unit_len == 1:
            dateQ = utils.dt64arr_as_int64_Q(arr, my_reso, 0, True)
            dates = utils.arr_mul(dateQ, 3, 0, False)
            to_reso = utils.DT_NPY_UNIT_MM

        # Special
        else:
            val: cython.int
            # Month name -> int64[Y] -> int64[M]
            if (val := _parse_month(unit, None, False)) != -1:
                dateY = utils.dt64arr_as_int64_Y(arr, my_reso, 0, True)
                dates = utils.dt64arr_as_int64_M(
                    dateY, utils.DT_NPY_UNIT_YY, val - 1, False
                )
                to_reso = utils.DT_NPY_UNIT_MM

            # Weekday name -> int64[D]
            elif (val := _parse_weekday(unit, None, False)) != -1:
                dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
                delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
                dates = utils.arr_sub_arr(dateD, delta, val, False)
                to_reso = utils.DT_NPY_UNIT_DD
                #: days - weekday + val

            # Unsupported unit
            else:
                errors.raise_argument_error(
                    self.__class__,
                    "to_start_of(unit)",
                    "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us', 'ns' "
                    "or Month/Weekday name; got '%s'." % unit,
                )
                return  # unreachable: suppress compiler warning

        # New instance
        arr = utils.dt64arr_as_unit(dates, my_unit, to_reso, False, False)
        return self._new(arr, tz=self.tz, name=self.name)

    def to_end_of(self, unit: str) -> Self:
        """Adjust the date & time fields to the end of the specified datetime unit `<'Pddt'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'`  → End of year: `YYYY-12-31 23:59:59.999999999`
            - `'Q'`  → End of quarter: `YYYY-MM-(30..31) 23:59:59.999999999`
            - `'M'`  → End of month: `YYYY-MM-(28..31) 23:59:59.999999999`
            - `'W'`  → End of week (Sunday): `YYYY-MM-DD 23:59:59.999999999`
            - `'D'`  → End of day: `YYYY-MM-DD 23:59:59.999999999`
            - `'h'`  → End of hour: `YYYY-MM-DD hh:59:59.999999999`
            - `'m'`  → End of minute: `YYYY-MM-DD hh:mm:59.999999999`
            - `'s'`  → End of second: `YYYY-MM-DD hh:mm:ss.999999999`
            - `'ms'` → End of millisecond: `YYYY-MM-DD hh:mm:ss.uuu999999`
            - `'us'` → End of millisecond: `YYYY-MM-DD hh:mm:ss.uuuuuu999`
            - `'ns'` → Return the instance `as-is`.
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                     → End of the specifed month: `YYYY-MM-(28..31) 23:59:59.999999`
            - `Weekday` (e.g., `'Mon'`, `'Tuesday'`, `'星期三'`)
                     → End of the specifed weekday: `YYYY-MM-DD 23:59:59.999999`

        :returns `<'Pddt'>`: The adjusted datetime index.
        """
        # Guard
        if unit is None:
            errors.raise_argument_error(
                self.__class__,
                "to_end_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us', 'ns' "
                "or Month/Weekday name; got None.",
            )
        unit_len: cython.Py_ssize_t = str_len(unit)
        if unit_len == 0:
            errors.raise_argument_error(
                self.__class__,
                "to_end_of(unit)",
                "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us', 'ns' "
                "or Month/Weekday name; got empty string.",
            )

        # Fast-path: 'ns' as-is
        ch0: cython.Py_UCS4 = str_read(unit, 0)
        if ch0 == "n" and unit_len == 2 and str_read(unit, 1) == "s":
            return self  # exit

        # Access datetime array & info
        arr: np.ndarray = self.values_naive

        # General approach: 'Y', 'M', 'D', 'h', 'm', 's', 'ms', 'us'
        my_unit: str = self.unit
        my_reso: cython.int = utils.nptime_unit_str2int(my_unit)
        to_reso: cython.int
        if (
            #: 'Y', 'M', 'D', 'h', 'm', 's'
            (unit_len == 1 and ch0 in ("Y", "M", "D", "h", "m", "s"))
            #: 'ms', 'us'
            or (unit_len == 2 and ch0 in ("m", "u") and str_read(unit, 1) == "s")
            #: 'min'
            or (
                unit_len == 3
                and ch0 == "m"
                and str_read(unit, 1) == "i"
                and str_read(unit, 2) == "n"
            )
        ):
            to_reso = utils.nptime_unit_str2int(unit)
            if my_reso <= to_reso:
                return self  # exit: already at or finer than target resolution
            arr: np.ndarray = self.values_naive
            arr = utils.dt64arr_as_int64(arr, unit, my_reso, 1, True)  # +1
            arr = utils.dt64arr_as_unit(arr, my_unit, to_reso, False, False)
            arr = utils.arr_add(arr, -1, False)  # -1 -> jump to the end
            return self._new(arr, tz=self.tz, name=self.name)

        # To weekday -> int64[D]-weekday+1week
        arr: np.ndarray = self.values_naive
        if ch0 == "W" and unit_len == 1:
            dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
            delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
            dates = utils.arr_sub_arr(dateD, delta, 7, False)
            to_reso = utils.DT_NPY_UNIT_DD

        # To quarter -> int64[Q]+1 -> int64[M]
        elif ch0 == "Q" and unit_len == 1:
            dateQ = utils.dt64arr_as_int64_Q(arr, my_reso, 1, True)
            dates = utils.arr_mul(dateQ, 3, 0, False)
            to_reso = utils.DT_NPY_UNIT_MM

        # Special
        else:
            val: cython.int
            # Month name -> int64[Y] -> int64[M]+MM (MM is 0-based; so no +1)
            if (val := _parse_month(unit, None, False)) != -1:
                dateY = utils.dt64arr_as_int64_Y(arr, my_reso, 0, True)
                dates = utils.dt64arr_as_int64_M(
                    dateY, utils.DT_NPY_UNIT_YY, val, False
                )
                to_reso = utils.DT_NPY_UNIT_MM

            # Weekday name -> int64[D]-weekday+DD+1
            elif (val := _parse_weekday(unit, None, False)) != -1:
                dateD = utils.dt64arr_as_int64_D(arr, my_reso, 0, True)
                delta = utils.dt64arr_weekday(dateD, utils.DT_NPY_UNIT_DD, 0, True)
                dates = utils.arr_sub_arr(dateD, delta, val + 1, False)
                to_reso = utils.DT_NPY_UNIT_DD

            # Invalid
            else:
                errors.raise_argument_error(
                    self.__class__,
                    "to_end_of(unit)",
                    "Supports: 'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us', 'ns' "
                    "or Month/Weekday name; got '%s'." % unit,
                )
                return  # unreachable: suppress compiler warning

        # New instance
        arr = utils.dt64arr_as_unit(dates, my_unit, to_reso, False, False)
        arr = utils.arr_add(arr, -1, False)  # -1 -> jump to the end
        return self._new(arr, tz=self.tz, name=self.name)

    def is_first_of(self, unit: str) -> pd.Index[bool]:
        """Element-wise check whether the date fields are on the first day
        of the specified datetime unit `<'Index[bool]'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → First day of the year: `YYYY-01-01`
            - `'Q'` → First day of the quarter: `YYYY-MM-01`
            - `'M'` → First day of the month: `YYYY-MM-01`
            - `'W'` → First day (Monday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → First day of the specifed month: `YYYY-MM-01`

        :return `<'Index[bool]'>`: True if the element is on the first day
            of the specified datetime unit; Otherwise False.
        """
        # To first of
        pt = self.to_first_of(unit)

        # Compare dates
        pt_dateD = utils.dt64arr_as_int64_D(pt.values, -1, True)
        my_dateD = utils.dt64arr_as_int64_D(self.values, -1, True)
        return pd.Index(utils.arr_eq_arr(my_dateD, pt_dateD), name="is_first_of")

    def is_last_of(self, unit: str) -> pd.Index[bool]:
        """Element-wise check whether the date fields are on the last day
        of the specified datetime unit `<'Index[bool]'>`.

        :param unit `<'str'>`: The datetime unit:

            - `'Y'` → Last day of the year: `YYYY-12-31`
            - `'Q'` → Last day of the quarter: `YYYY-MM-(30..31)`
            - `'M'` → Last day of the month: `YYYY-MM-(28..31)`
            - `'W'` → Last day (Sunday) of the week: `YYYY-MM-DD`
            - `Month` (e.g., `'Jan'`, `'February'`, `'三月'`)
                    → Last day of the specifed month: `YYYY-MM-(28..31)`

        :return `<'Index[bool]'>`: True if the element is on the last day
            of the specified datetime unit; Otherwise False.
        """
        # To last of
        pt = self.to_last_of(unit)

        # Compare dates
        pt_dateD = utils.dt64arr_as_int64_D(pt.values, -1, True)
        my_dateD = utils.dt64arr_as_int64_D(self.values, -1, True)
        return pd.Index(utils.arr_eq_arr(my_dateD, pt_dateD), name="is_last_of")

    def is_start_of(self, unit: str) -> pd.Index[bool]:
        """Element-wise check whether date & time fileds are the
        start of the specified datetime unit `<'Index[bool]'>`.

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

        :return `<'Index[bool]'>`: True if the element is at the start
            of the specified datetime unit; Otherwise False.
        """
        # To start of
        pt = self.to_start_of(unit)

        # Compare values
        pt_unit: str = pt.unit
        pt_reso: cython.int = utils.nptime_unit_str2int(pt_unit)
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)
        if pt_reso == my_reso:
            arr = utils.arr_eq_arr(self.values, pt.values)
        else:
            arr = utils.arr_eq_arr(
                utils.dt64arr_as_unit(self.values, pt_unit, my_reso, True, True),
                pt.values,
            )
        return pd.Index(arr, name="is_start_of")

    def is_end_of(self, unit: str) -> pd.Index[bool]:
        """Element-wise check whether date & time fileds are the
        end of the specified datetime unit `<'Index[bool]'>`.

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

        :return `<'Index[bool]'>`: True if the element is at the end
            of the specified datetime unit; Otherwise False.
        """
        # To end of
        pt = self.to_end_of(unit)

        # Compare values
        pt_unit: str = pt.unit
        pt_reso: cython.int = utils.nptime_unit_str2int(pt_unit)
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)
        if pt_reso == my_reso:
            arr = utils.arr_eq_arr(self.values, pt.values)
        else:
            arr = utils.arr_eq_arr(
                utils.dt64arr_as_unit(self.values, pt_unit, my_reso, True, True),
                pt.values,
            )
        return pd.Index(arr, name="is_end_of")

    # . round / ceil / floor
    def round(self, unit: str) -> Self:
        """Perform round operation to the specified datetime unit `<'Pddt'>`.

        :param unit `<'str'>`: The datetime unit to round to, supports:
            `'D', 'h', 'm', 's', 'ms', 'us', 'ns'`.
        :returns `<'Pddt'>`: The resulting datetime index.
        """
        # Validate unit
        try:
            to_reso: cython.int = utils.nptime_unit_str2int(unit)
        except Exception as err:
            raise errors.InvalidArgumentError(
                "<'%s'> Invalid 'round(unit)' input.\n"
                "Supports: 'D', 'h', 'm', 's', 'ms', 'us', 'ns'; got %r."
                % (self.__class__.__name__, unit)
            ) from err
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)

        # Fast-path: source is coarser or equal to target
        if my_reso <= to_reso:
            return self  # exit

        # Round operation
        arr: np.ndarray = self.values_naive
        try:
            out: np.ndarray = utils.dt64arr_round(arr, unit, my_reso, True)
        except Exception as err:
            errors.raise_argument_error(self.__class__, "round(unit)", None, err)
            return  # unreachable: suppress compiler warning
        if arr is out:
            return self  # exit

        # New instance
        return self._new(out, tz=self.tz, name=self.name)

    def ceil(self, unit: str) -> Self:
        """Perform ceil operation to the specified datetime unit `<'Pddt'>`.

        :param unit `<'str'>`: The datetime unit to ceil to, supports:
            `'D', 'h', 'm', 's', 'ms', 'us', 'ns'`.
        :returns `<'Pddt'>`: The resulting datetime index.
        """
        # Validate unit
        try:
            to_reso: cython.int = utils.nptime_unit_str2int(unit)
        except Exception as err:
            raise errors.InvalidArgumentError(
                "<'%s'> Invalid 'ceil(unit)' input.\n"
                "Supports: 'D', 'h', 'm', 's', 'ms', 'us', 'ns'; got %r."
                % (self.__class__.__name__, unit)
            ) from err
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)

        # Fast-path: source is coarser or equal to target
        if my_reso <= to_reso:
            return self  # exit

        # Ceil operation
        arr: np.ndarray = self.values_naive
        try:
            out: np.ndarray = utils.dt64arr_ceil(arr, unit, my_reso, True)
        except Exception as err:
            errors.raise_argument_error(self.__class__, "ceil(unit)", None, err)
            return  # unreachable: suppress compiler warning
        if arr is out:
            return self  # exit

        # New instance
        return self._new(out, tz=self.tz, name=self.name)

    def floor(self, unit: str) -> Self:
        """Perform floor operation to the specified datetime unit `<'Pddt'>`.

        :param unit `<'str'>`: The datetime unit to floor to, supports:
            `'D', 'h', 'm', 's', 'ms', 'us', 'ns'`.
        :returns `<'Pddt'>`: The resulting datetime index.
        """
        # Validate unit
        try:
            to_reso: cython.int = utils.nptime_unit_str2int(unit)
        except Exception as err:
            raise errors.InvalidArgumentError(
                "<'%s'> Invalid 'floor(unit)' input.\n"
                "Supports: 'D', 'h', 'm', 's', 'ms', 'us', 'ns'; got %r."
                % (self.__class__.__name__, unit)
            ) from err
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)

        # Fast-path: source is coarser or equal to target
        if my_reso <= to_reso:
            return self  # exit

        # Floor operation
        arr: np.ndarray = self.values_naive
        try:
            out: np.ndarray = utils.dt64arr_floor(arr, unit, my_reso, True)
        except Exception as err:
            errors.raise_argument_error(self.__class__, "floor(unit)", None, err)
            return  # unreachable: suppress compiler warning
        if arr is out:
            return self  # exit

        # New instance
        return self._new(out, tz=self.tz, name=self.name)

    # . fsp (fractional seconds precision)
    def fsp(self, precision: cython.int) -> Self:
        """Adjust to the specified fractional seconds precision `<'Pddt'>`.

        :param precision `<'int'>`: The target fractional seconds precision (0-9).
        :returns `<'Pddt'>`: The datetime index with adjusted fractional seconds precision.
            If the instance's resolution is coarser than the specified
            precision, return `as-is`.
        """
        # Validate
        if precision < 0:
            errors.raise_argument_error(
                self.__class__,
                "fsp(precision)",
                "Fractional seconds precision must be "
                "between 0...9, instead got %d." % precision,
            )
        # Fast-path
        if precision >= 9:
            return self  # exit

        # Calcualte factor
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)
        f: cython.longlong  # fsp factor
        # . nanosecond
        if my_reso == utils.DT_NPY_UNIT_NS:
            f = int(10 ** (9 - precision))
        # . microsecond
        elif my_reso == utils.DT_NPY_UNIT_US:
            if precision >= 6:
                return self  # exit
            f = int(10 ** (6 - precision))
        # . millisecond
        elif my_reso == utils.DT_NPY_UNIT_MS:
            if precision >= 3:
                return self  # exit
            f = int(10 ** (3 - precision))
        # . second
        else:
            return self  # exit

        # Adjust precision
        arr: np.ndarray = self.values_naive
        if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
            arr, utils.DT_NPY_UNIT_NS
        ):
            arr = utils.dt64arr_as_int64_us(arr, my_reso, 0, True)
            arr = arr.astype(utils.DT64_DTYPE_US)
            if precision < 6:
                f //= 1_000
                arr = utils.arr_div_floor_mul(arr, f, f, 0, False)
        else:
            arr = utils.arr_div_floor_mul(arr, f, f, 0, True)
        #: 'arr' is dt64 dtype

        # New instance
        return self._new(arr, tz=self.tz, name=self.name)

    # Calendar -----------------------------------------------------------------------------
    # . iso
    def isocalendar(self) -> pd.DataFrame:
        """Return the ISO calendar `<'DateFrame'>`.

        ## Example:
        >>> pt.isocalendar()
        ```
        _                              year  week  weekday
        1677-09-21 00:12:43.145224193  1677    38        2
        2262-04-11 23:47:16.854775807  2262    15        5
        ```
        """
        arr = utils.dt64arr_isocalendar(self.values_naive)
        return pd.DataFrame(arr, columns=["year", "week", "weekday"], index=self)

    def isoyear(self) -> pd.Index[np.int64]:
        """Return the ISO calendar years `<'Index[int64]'>`."""
        arr = utils.dt64arr_isoyear(self.values_naive)
        return pd.Index(arr, name="isoyear")

    def isoweek(self) -> pd.Index[np.int64]:
        """Return the ISO calendar week numbers (1-53) `<'Index[int64]'>`."""
        arr = utils.dt64arr_isoweek(self.values_naive)
        return pd.Index(arr, name="isoweek")

    def isoweekday(self) -> pd.Index[np.int64]:
        """Return the ISO calendar weekdays (1=Mon...7=Sun) `<'Index[int64]'>`."""
        arr = utils.dt64arr_isoweekday(self.values_naive)
        return pd.Index(arr, name="isoweekday")

    # . year
    @property
    def year(self) -> pd.Index[np.int64]:
        """The years `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_year(self.values_naive), name="year")

    def is_year(self, year: cython.int) -> pd.Index[bool]:
        """Element-wise check whether is the exact `year` `<'Index[bool]'>."""
        return pd.Index(
            utils.arr_eq(utils.dt64arr_year(self.values_naive), year), name="is_year"
        )

    def is_leap_year(self) -> pd.Index[bool]:
        """Element-wise check whether is in leap year `<'Index[bool]'>."""
        return pd.Index(
            utils.dt64arr_is_leap_year(self.values_naive), name="is_leap_year"
        )

    def is_long_year(self) -> pd.Index[bool]:
        """Element-wise check whether is in long year `<'Index[bool]'>`.

        - Long year: maximum ISO week number is 53.
        """
        return pd.Index(
            utils.dt64arr_is_long_year(self.values_naive), name="is_long_year"
        )

    def leap_bt_year(self, year: cython.int) -> pd.Index[np.int64]:
        """Compute the total number of leap years between `year` and each element `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_leap_bt_years(self.values_naive, year),
            name="leap_bt_year",
        )

    def days_in_year(self) -> pd.Index[np.int64]:
        """Return the maximum number of days (365, 366) in the year `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_days_in_year(self.values_naive), name="days_in_year"
        )

    def days_bf_year(self) -> pd.Index[np.int64]:
        """Return the number of days strictly before January 1 of year `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_days_bf_year(self.values_naive), name="days_bf_year"
        )

    def day_of_year(self) -> pd.Index[np.int64]:
        """Return the number of days since the 1st day of the year `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_day_of_year(self.values_naive), name="day_of_year"
        )

    # . quarter
    @property
    def quarter(self) -> pd.Index[np.int64]:
        """The quarters (1-4) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_quarter(self.values_naive), name="quarter")

    def is_quarter(self, quarter: cython.int) -> pd.Index[bool]:
        """Element-wise check whether is the exact `quarter` `<'Index[bool]'>`."""
        return pd.Index(
            utils.arr_eq(utils.dt64arr_quarter(self.values_naive), quarter),
            name="is_quarter",
        )

    def days_in_quarter(self) -> pd.Index[np.int64]:
        """Return the maximum number of days (90-92) in the quarter `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_days_in_quarter(self.values_naive), name="days_in_quarter"
        )

    def days_bf_quarter(self) -> pd.Index[np.int64]:
        """Return the number of days strictly before the first day
        of the calendar quarter `<'Index[int64]'>`.
        """
        return pd.Index(
            utils.dt64arr_days_bf_quarter(self.values_naive), name="days_bf_quarter"
        )

    def day_of_quarter(self) -> pd.Index[np.int64]:
        """Return the number of days since the 1st day of the quarter `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_day_of_quarter(self.values_naive), name="day_of_quarter"
        )

    # . month
    @property
    def month(self) -> pd.Index[np.int64]:
        """The months (1-12) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_month(self.values_naive), name="month")

    def is_month(self, month: str | int) -> pd.Index[bool]:
        """Element-wise check whether is the exact `month` `<'Index[bool]'>`.

        :param month `<'int/str'>`: Month value.

            - `<'int'>`  Month number (1=Jan...12=Dec).
            - `<'str'>`  Month name in lowercase, uppercase or titlecase (e.g., 'Jan', 'februar', '三月').

        :return `<'Index[bool]'>`: True if `month` is recognized and matched
            with index instances' month; Otherwise False.
        """
        mm: cython.int = _parse_month(month, None, True)
        return pd.Index(
            utils.arr_eq(utils.dt64arr_month(self.values_naive), mm), name="is_month"
        )

    def days_in_month(self) -> pd.Index[np.int64]:
        """Return the maximum number of days (28-31) in the month `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_days_in_month(self.values_naive), name="days_in_month"
        )

    def days_bf_month(self) -> pd.Index[np.int64]:
        """Return the number of days strictly before the first day
        of the calendar month `<'Index[int64]'>`.
        """
        return pd.Index(
            utils.dt64arr_days_bf_month(self.values_naive), name="days_bf_month"
        )

    def day_of_month(self) -> pd.Index[np.int64]:
        """Return the number of days since the 1st day of the month `<'Index[int64]'>`.

        ## Equivalent
        >>> pt.day
        """
        return pd.Index(utils.dt64arr_day(self.values_naive), name="day_of_month")

    def month_name(self, locale: str | None = None) -> pd.Index[str]:
        """Return the month names with specified locale `<'Index[str]'>`.

        :param locale `<'str/None'>`: The locale to use for month name. Defaults to `None`.

            - Locale determining the language in which to return the month name.
              If `None` uses English locale (`'en_US'`).
            - Use the command `locale -a` on Unix systems terminal to
              find locale language code.

        :return `<'Index[str]'>`: The month names.
        """
        try:
            return DatetimeIndex.month_name(self, locale=locale)
        except Exception as err:
            errors.raise_argument_error(self.__class__, "month_name(locale)", None, err)

    # . weekday
    @property
    def weekday(self) -> pd.Index[np.int64]:
        """The weekdays (0=Mon...6=Sun) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_weekday(self.values_naive), name="weekday")

    def is_weekday(self, weekday: int | str) -> pd.Index[bool]:
        """Element-wise check whether is the exact `weekday` `<'Index[bool]'>`.

        :param weekday `<'int/str/None'>`: Weekday value.

            - `<'int'>`  Weekday number (0=Mon...6=Sun).
            - `<'str'>`  Weekday name in lowercase, uppercase or titlecase (e.g., 'Mon', 'dienstag', '星期三').

        :return `<'Index[bool]'>`: True if `weekday` is recognized and matched
            with index instances' weekday; Otherwise False.
        """
        wd: cython.int = _parse_weekday(weekday, None, True)
        return pd.Index(
            utils.arr_eq(utils.dt64arr_weekday(self.values_naive), wd),
            name="is_weekday",
        )

    def weekday_name(self, locale: str | None = None) -> pd.Index[str]:
        """Return the weekday names with specified locale `<'Index[str]'>`.

        :param locale `<'str/None'>`: The locale to use for weekday name. Defaults to `None`.

            - Locale determining the language in which to return the weekday name.
              If `None` uses English locale (`'en_US'`).
            - Use the command `locale -a` on Unix systems terminal to
              find locale language code.

        :return `<'Index[str]'>`: The weekday names.

        ## Equivalent
        >>> DatetimeIndex.day_name(locale)
        """
        try:
            return DatetimeIndex.day_name(self, locale=locale)
        except Exception as err:
            errors.raise_argument_error(
                self.__class__, "weekday_name(locale)", None, err
            )

    # . day
    @property
    def day(self) -> pd.Index[np.int64]:
        """The days (1-31) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_day(self.values_naive), name="day")

    def is_day(self, day: cython.int) -> pd.Index[bool]:
        """Element-wise check whether is the exact `day` `<'Index[bool]'>`."""
        return pd.Index(
            utils.arr_eq(utils.dt64arr_day(self.values_naive), day), name="is_day"
        )

    # . time
    @property
    def hour(self) -> pd.Index[np.int64]:
        """The hours (0-23) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_hour(self.values_naive), name="hour")

    @property
    def minute(self) -> pd.Index[np.int64]:
        """The minutes (0-59) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_minute(self.values_naive), name="minute")

    @property
    def second(self) -> pd.Index[np.int64]:
        """The seconds (0-59) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_second(self.values_naive), name="second")

    @property
    def millisecond(self) -> pd.Index[np.int64]:
        """The milliseconds (0-999) `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_millisecond(self.values_naive), name="millisecond"
        )

    @property
    def microsecond(self) -> pd.Index[np.int64]:
        """The microseconds (0-999999) `<'Index[int64]'>`."""
        return pd.Index(
            utils.dt64arr_microsecond(self.values_naive), name="microsecond"
        )

    @property
    def nanosecond(self) -> pd.Index[np.int64]:
        """The nanoseconds (0-999) `<'Index[int64]'>`."""
        return pd.Index(utils.dt64arr_nanosecond(self.values_naive), name="nanosecond")

    # Timezone -----------------------------------------------------------------------------
    @property
    def tz_available(self) -> set[str]:
        """The available timezone names `<'set[str]'>`.

        ## Equivalent
        >>> zoneinfo.available_timezones()
        """
        return _available_timezones()

    def is_local(self) -> bool:
        """Check whether is in the local timezone `<'bool'>`.

        - Naive datetime index always return `False`.
        """
        return self.tzinfo is utils.tz_local()

    def is_utc(self) -> bool:
        """Check whether is in the UTC timezone `<'bool'>`.

        - Naive datetime index always return `False`.
        """
        return self.tzinfo is utils.UTC

    def tzname(self) -> str:
        """Return the timezone name `<'str/None'>`.

        - Naive datetime index always return `None`.
        """
        my_tz = self.tzinfo
        return None if my_tz is None else my_tz.tzname(utils.dt_now())

    def astimezone(
        self,
        tz: datetime.tzinfo | str | None = None,
        ambiguous: object = "raise",
        nonexistent: object = "raise",
    ) -> Self:
        """Convert to another timezone `<'Pddt'>`.

        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` the system `local` timezone is used.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param ambiguous `<'str/ndarray'>`: How to handle ambiguous times. Defaults to `'raise'`.

            - `<'str'>` Accepts: `'infer'`, `'NaT'` or `'raise'` for ambiguous times handling.
            - `<'ndarray'>` A boolean array that specifies ambiguous times (True for DST time).

        :param nonexistent `<'str/timedelta'>`: How to handle nonexistent times. Defaults to `'raise'`.

            - `<'str'>` Accepts `'shift_forward'`, `'shift_backward'`, `'NaT'` or `'raise'`
                for nonexistent times handling.
            - `<'timedelta'>` An instance of timedelta to shift the nonexistent times.

        :returns `<'Pddt'>`: The resulting datetime index representing the `same` index
            expressed in the target timezone. For naive datetime index and `tz is None`,
            `localizes` the index to the system local zone.
        """
        # Resolve target timezone
        to_tz = utils.tz_parse(tz)
        my_tz = self.tzinfo
        if to_tz is None:
            to_tz = utils.tz_local()
            # Fast-exit: naive + local -> localize
            if my_tz is None:
                return self.tz_localize(to_tz, ambiguous, nonexistent)

        # Resolve my timezone
        if my_tz is None:
            my_tz = utils.tz_local()
            pt = self.tz_localize(my_tz, ambiguous, nonexistent)
        else:
            pt = self

        # Fast-exit: exact same timezone
        if my_tz is to_tz:
            return pt  # exit

        # Convert to target timezone
        return pt.tz_convert(to_tz)

    def tz_localize(
        self,
        tz: datetime.tzinfo | str | None,
        ambiguous: object = "raise",
        nonexistent: object = "raise",
    ) -> Self:
        """Localize timezone-naive datetime index to the target timezone;
        or timezone-aware datetime index to timezone naive (without moving
        the date & time fields) `<'Pddt'>`.

        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` Localize to timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :param ambiguous `<'str/ndarray'>`: How to handle ambiguous times. Defaults to `'raise'`.

            - `<'str'>` Accepts: `'infer'`, `'NaT'` or `'raise'` for ambiguous times handling.
            - `<'ndarray'>` A boolean array that specifies ambiguous times (True for DST time).

        :param nonexistent `<'str/timedelta'>`: How to handle nonexistent times. Defaults to `'raise'`.

            - `<'str'>` Accepts `'shift_forward'`, `'shift_backward'`, `'NaT'` or `'raise'`
                for nonexistent times handling.
            - `<'timedelta'>` An instance of timedelta to shift the nonexistent times.

        :returns `<'Pddt'>`: The resulting datetime index localized to the target timezone.
        """
        # Timezone-aware
        tz = utils.tz_parse(tz)
        my_tz = self.tzinfo
        if my_tz is not None:
            if tz is not None:
                errors.raise_argument_error(
                    self.__class__,
                    "tz_localize(tz, ...)",
                    "Datetime index is already timezone-aware.\n"
                    "Use 'tz_convert()' or 'tz_switch()' method "
                    "to convert to tge target timezone.",
                )
            # Localize: aware => naive
            try:
                return DatetimeIndex.tz_localize(self, None)
            # fmt: off
            except errors.PdOutOfBoundsDatetime as err:
                errors.raise_error(errors.OutOfBoundsError, self.__class__, "tz_localize(...)", None, err)
                return  # unreachable: suppress compiler warning
            except (errors.PytzAmbiguousTimeError, errors.PytzNonExistentTimeError) as err:
                errors.raise_error(errors.AmbiguousTimeError, self.__class__, "tz_localize(...)", None, err)
                return  # unreachable: suppress compiler warning
            except Exception as err:
                errors.raise_argument_error(self.__class__, "tz_localize(...)", None, err)
                return  # unreachable: suppress compiler warning
            # fmt: on

        # Timezone-naive
        if tz is None:
            return self  # exit

        # Localize: naive => aware
        #: To prevent 'ns' overflow issue, we manually check if
        #: the values are in safe 'ns' range before localization.
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)
        try:
            if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
                self.values_naive, utils.DT_NPY_UNIT_NS
            ):
                # Cast to 'us' to prevent overflow
                return DatetimeIndex.tz_localize(
                    self.as_unit("us"), tz, ambiguous, nonexistent
                )
                # Localize in original resolution
            else:
                return DatetimeIndex.tz_localize(self, tz, ambiguous, nonexistent)
        # fmt: off
        except errors.PdOutOfBoundsDatetime as err:
            errors.raise_error(errors.OutOfBoundsError, self.__class__, "tz_localize(...)", None, err)
            return  # unreachable: suppress compiler warning
        except (errors.PytzAmbiguousTimeError, errors.PytzNonExistentTimeError) as err:
            errors.raise_error(errors.AmbiguousTimeError, self.__class__, "tz_localize(...)", None, err)
            return  # unreachable: suppress compiler warning
        except Exception as err:
            errors.raise_argument_error(self.__class__, "tz_localize(...)", None, err)
            return  # unreachable: suppress compiler warning
        # fmt: on

    def tz_convert(self, tz: datetime.tzinfo | str | None) -> Self:
        """Convert timezone-aware datetime index to another timezone `<'Pddt'>`.

        :param tz `<'tzinfo/str/None'>`: Target timezone. Defaults to `None`.

            - `<'None'>` Convert to UTC timezone and localize to timezone-naive.
            - `<'str'>` Timezone name; or `'local'` for local timezone.
            - `<'datetime.tzinfo'>` A subclass of `datetime.tzinfo`.

        :returns `<'Pddt'>`: The resulting datetime index representing the
            `same` datetimes expressed in the target timezone.
        """
        # Validate
        my_tz = self.tzinfo
        if my_tz is None:
            errors.raise_argument_error(
                self._cls(),
                "tz_convert(tz)",
                "Datetime index is timezone-naive.\n"
                "Use 'tz_localize()' method to localize timezone, or "
                "use 'tz_switch()' method to convert to the target "
                "timezone by providing a base timezone.",
            )

        # Same timezone
        tz = utils.tz_parse(tz)
        if my_tz is tz:
            return self

        # Convert: aware => aware
        #: To prevent 'ns' overflow issue, we manually check if
        #: the values are in safe 'ns' range before conversion.
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)
        try:
            if my_reso == utils.DT_NPY_UNIT_NS and not utils.is_dt64arr_ns_safe(
                self.values_naive, utils.DT_NPY_UNIT_NS
            ):
                # Cast to 'us' to prevent overflow
                return DatetimeIndex.tz_convert(self.as_unit("us"), tz)
            else:
                # Convert in original resolution
                return DatetimeIndex.tz_convert(self, tz)
        # fmt: off
        except errors.PdOutOfBoundsDatetime as err:
            errors.raise_error(errors.OutOfBoundsError, self.__class__, "tz_convert(...)", None, err)
            return  # unreachable: suppress compiler warning
        except (errors.PytzAmbiguousTimeError, errors.PytzNonExistentTimeError) as err:
            errors.raise_error(errors.AmbiguousTimeError, self.__class__, "tz_convert(...)", None, err)
            return  # unreachable: suppress compiler warning
        except Exception as err:
            errors.raise_argument_error(self.__class__, "tz_convert(...)", None, err)
            return  # unreachable: suppress compiler warning
        # fmt: on

    def tz_switch(
        self,
        targ_tz: datetime.tzinfo | str | None,
        base_tz: datetime.tzinfo | str | None = None,
        naive: cython.bint = False,
        ambiguous: object = "raise",
        nonexistent: object = "raise",
    ) -> Self:
        """Switch (convert) the datetime index from base timezone to the target timezone `<'Pddt'>`.

        This method extends the functionality of `astimezone()` by allowing
        user to specify a base timezone for timezone-naive index before
        converting to the target timezone.

        - If the datetime index is timezone-aware, the 'base_tz' argument is `ignored`,
          and this method behaves identical to `astimezone()`: converting the index
          to the target timezone.
        - If the datetime index is timezone-naive, it first localizes the index
          to the `base_tz` (required), and then converts to the target timezone.

        :param targ_tz `<'tzinfo/str/None'>`: The target timezone.

        :param base_tz `<'tzinfo/str/None'>`: The base timezone for timezone-naive index. Defaults to `None`.

        :param naive `<'bool'>`: If 'True', returns timezone-naive datetime index after conversion. Defaults to `False`.

        :param ambiguous `<'str/ndarray'>`: How to handle ambiguous times. Defaults to `'raise'`.

            - `<'str'>` Accepts: `'infer'`, `'NaT'` or `'raise'` for ambiguous times handling.
            - `<'ndarray'>` A boolean array that specifies ambiguous times (True for DST time).

        :param nonexistent `<'str/timedelta'>`: How to handle nonexistent times. Defaults to `'raise'`.

            - `<'str'>` Accepts `'shift_forward'`, `'shift_backward'`, `'NaT'` or `'raise'`
                for nonexistent times handling.
            - `<'timedelta'>` An instance of timedelta to shift the nonexistent times.

        :returns `<'Pddt'>`: The resulting datetime index representing the
            `same` datetimes expressed in the target timezone; optionally timezone-naive.
        """
        # Timezone-aware
        to_tz = utils.tz_parse(targ_tz)
        my_tz = self.tzinfo
        if my_tz is not None:
            # . target timezone is None
            if to_tz is None:
                return self.tz_localize(None)
            # . target timezone is mytz
            elif to_tz is utils.tz_parse(my_tz):
                return self.tz_localize(None) if naive else self
            # . mytz => target timezone
            else:
                pt = self.tz_convert(to_tz)
                return pt.tz_localize(None) if naive else pt

        # Timezone-naive
        # . target timezone is None
        if to_tz is None:
            return self  # exit
        # . base timezone is None
        base_tz = utils.tz_parse(base_tz)
        if base_tz is None:
            errors.raise_argument_error(
                self.__class__,
                "tz_switch(...)",
                "Datetime index is timezone-naive.\n"
                "Cannot convert timezone-naive datetime to the "
                "target timezone without a base timezone (base_tz).",
            )
        # . base timezone is target timezone
        if base_tz is to_tz:
            return self if naive else self.tz_localize(to_tz, ambiguous, nonexistent)
        # . localize to base, then convert to target timezone
        else:
            pt = self.tz_localize(base_tz, ambiguous, nonexistent).tz_convert(to_tz)
            return pt.tz_localize(None) if naive else pt

    # Values -------------------------------------------------------------------------------
    @property
    def values_naive(self) -> np.ndarray[np.datetime64]:
        """Returns an array of the `timezone-naive` datetimes
        (underlying data) in the index `<'ndarray[datetime64]'>`.

        ## Behavior
        - If index is timezone-naive or `UTC`, equivalent to `pt.values`.
        - If index is timezone-aware, equivalent to `pt.tz_localize(None).values`.
        """
        tz: object = self.tzinfo
        if tz is None or tz is utils.UTC:
            return self.values
        else:
            return DatetimeIndex.tz_localize(self, None).values

    def as_unit(self, as_unit: str) -> Self:
        """Convert index to the given unit resolution `<'Pddt'>`.

        :param as_unit `<'str'>`: The target datetime unit resolution.
            Supports: `'s', 'ms', 'us', 'ns'`.

        :returns `<'Pddt'>`: Index with the specified datetime unit.
        """
        # Validate units
        try:
            as_reso: cython.int = utils.nptime_unit_str2int(as_unit)
        except Exception as err:
            raise errors.InvalidArgumentError(
                "<'%s'> Invalid 'as_unit' input.\n"
                "Supports: 's', 'ms', 'us' and 'ns'; got %r."
                % (self.__class__.__name__, as_unit)
            ) from err
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)

        # Fast-path: same unit
        if my_reso == as_reso:
            return self  # exit

        # Convert unit
        arr: np.ndarray = self.values_naive
        try:
            out: np.ndarray = utils.dt64arr_as_unit(arr, as_unit, my_reso, True, True)
        except Exception as err:
            errors.raise_argument_error(self.__class__, "as_unit", None, err)
            return  # unreachable: suppress compiler warning
        if arr is out:
            return self  # exit

        # New instance
        return self._new(out, tz=self.tzinfo, name=self.name)

    # Arithmetic ---------------------------------------------------------------------------
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
        nanoseconds: cython.int = 0,
    ) -> Self:
        """Add relative delta to the datetime index `<'Pddt'>`.

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
        :param nanoseconds `<'int'>`: Relative nanoseconds. Defaults to `0`.
        :returns `<'Pddt'>`: The resulting datetime index after adding the relative delta.
        """
        # Fast-path: no change
        if (
            years == 0
            and quarters == 0
            and months == 0
            and weeks == 0
            and days == 0
            and hours == 0
            and minutes == 0
            and seconds == 0
            and milliseconds == 0
            and microseconds == 0
            and nanoseconds == 0
        ):
            return self  # exit

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)

        # Add delta
        # fmt: off
        out = utils.dt64arr_add_delta(arr,
            years, quarters, months, weeks, days, hours, minutes, 
            seconds, milliseconds, microseconds, nanoseconds,
            my_reso
        )
        # fmt: on

        # New instance
        return self._new(out, tz=self.tzinfo, name=self.name)

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
        nanoseconds: cython.int = 0,
    ) -> Self:
        """Subtract relative delta from the datetime index `<'Pddt'>`.

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
        :param nanoseconds `<'int'>`: Relative nanoseconds. Defaults to `0`.
        :returns `<'Pddt'>`: The resulting datetime index after subtracting the relative delta.
        """
        # Fast-path: no change
        if (
            years == 0
            and quarters == 0
            and months == 0
            and weeks == 0
            and days == 0
            and hours == 0
            and minutes == 0
            and seconds == 0
            and milliseconds == 0
            and microseconds == 0
            and nanoseconds == 0
        ):
            return self  # exit

        # Access datetime array & info
        arr: np.ndarray = self.values_naive
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)

        # Sub delta
        # fmt: off
        out = utils.dt64arr_add_delta(arr,
            -years, -quarters, -months, -weeks, -days, -hours, -minutes, 
            -seconds, -milliseconds, -microseconds, -nanoseconds,
            my_reso
        )
        # fmt: on

        # New instance
        return self._new(out, tz=self.tzinfo, name=self.name)

    def diff(
        self,
        data: object,
        unit: str,
        absolute: cython.bint = False,
        inclusive: str = "one",
    ) -> np.ndarray[np.int64]:
        """Compute the delta difference between the instance and another datetime-like data `<'int'>`.

        The delta are computed in the specified datetime 'unit' and
        adjusted based on the 'inclusive' argument to determine the
        inclusivity of the start and end times.

        :param data `<'object'>`: Datetime-like data.

            - `<'Array-Like'>`          → An array-like (1-dimensional) data containing datetime information.
                                          such as: `list`, `np.ndarray`, `DatetimeIndex`, `Pddt`, etc.
                                          Must contains the exact number of elements as the instance.
            - `<'str'>`                 → A datetime string.
            - `<'datetime.datetime'>`   → An instance or subclass of `datetime.datetime`.
            - `<'datetime.date'>`       → An instance or subclass of `datetime.date` (time fields set to 0).
            - `<'np.datetime64'>`       → An instance of `np.datetime64`.

        :param unit `<'str'>`: The unit to compute the delta difference.
            Supports: `'Y', 'Q', 'M', 'W', 'D', 'h', 'm', 's', 'ms', 'us', 'ns'`.

        :param absolute `<'bool'>`: If 'True', compute the absolute difference. Defaults to `False`.

        :param inclusive `<'str'>`: Specifies the inclusivity of the start and end times. Defaults to `'one'`.

            - `'one'`     → Include either the start or end time → `(a - b)`
            - `'both'`:   → Include both the start and end times → `(a - b) + 1 (offset)`
            - `'neither'` → Exclude both the start and end times → `(a - b) - 1 (offset)`

        :returns `<'np.ndarray[int64]'>`: The delta difference between the instance
            and `data` in the specified `unit`, adjusted for inclusivity.
        """
        # Parse 'data' into datetime index
        my_arr: np.ndarray = self.values
        my_size: cython.Py_ssize_t = my_arr.shape[0]
        if isinstance(data, Pddt):
            pt = data
        elif isinstance(data, (str, datetime.date, np.datetime64)):
            pt = Pddt.fromdatetime(data, size=my_size)
        elif isinstance(data, (int, float)):
            pt = Pddt.fromseconds(data, size=my_size)
        else:
            try:
                pt = Pddt(data)
            except Exception as err:
                errors.raise_argument_error(
                    self.__class__,
                    "diff(data, ...)",
                    "Cannot parse 'data' into datetime index.",
                    err,
                )
                return  # unreachable: suppress compiler warning

        # Check array size
        pt_arr: np.ndarray = pt.values
        if my_size != pt_arr.shape[0]:
            errors.raise_argument_error(
                self.__class__,
                "diff(data, ...)",
                "Cannot compare datetime indexes with different length: '%d' vs '%d'."
                % (my_size, pt_arr.shape[0]),
            )

        # Check timezone parity
        my_tz = self.tzinfo
        pt_tz = pt.tzinfo
        if (my_tz is not None) != (pt_tz is not None):
            errors.raise_error(
                errors.MixedTimezoneError,
                self.__class__,
                "diff(data, ...)",
                "Cannot compare naive and aware datetime indexes",
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
                self.__class__,
                "diff(..., inclusive)",
                "Supports: 'one', 'both' or 'neither'; got '%s'." % inclusive,
            )
            return  # unreachable: suppress compiler warning

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

        # Calculate delta -> int64
        try:
            # . convert to int64[W] on monday
            if unit_len == 1 and str_read(unit, 0) == "W":
                my_arr = utils.dt64arr_as_W_iso(my_arr, 1, -1, 0, True)
                pt_arr = utils.dt64arr_as_W_iso(pt_arr, 1, -1, 0, True)
            # . convert to int64[unit]
            else:
                my_arr = utils.dt64arr_as_int64(my_arr, unit, -1, 0, True)
                pt_arr = utils.dt64arr_as_int64(pt_arr, unit, -1, 0, True)
        except Exception as err:
            errors.raise_argument_error(self.__class__, "diff(..., unit)", None, err)
            return  # unreachable: suppress compiler warning
        # . compute relative delta
        delta = utils.arr_sub_arr(my_arr, pt_arr, 0, False)

        # Adjust for inclusivity
        # . absolute = True
        if absolute:
            delta = utils.arr_abs(delta, incl_off, False)
        # . absolute = False & inclusive offset
        elif incl_off != 0:
            delta_p = cython.cast(cython.pointer(np.npy_int64), np.PyArray_DATA(delta))
            i: cython.Py_ssize_t
            for i in range(my_size):
                # Preserve NaT
                v: np.npy_int64 = delta_p[i]
                if v == utils.LLONG_MIN:
                    continue
                # Adjust offset
                delta_p[i] = v - incl_off if v < 0 else v + incl_off

        # Finished
        return pd.Index(delta, name="diff")

    # Comparison ---------------------------------------------------------------------------
    def is_past(self) -> pd.Index[bool]:
        """Element-wise check whether datetimes are in the past `<'Index[bool]'>`.

        ## Equivalent
        >>> self < datetime.datetime.now(self.tzinfo)
        """
        # Get current datetime in the same timezone
        dt: datetime.datetime = utils.dt_now(self.tzinfo, None)

        # Convert to the same resolution
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)
        tic: cython.longlong = utils.dt_to_us(dt, True)
        if my_reso == utils.DT_NPY_UNIT_NS:
            tic *= utils.NS_MICROSECOND
        elif my_reso == utils.DT_NPY_UNIT_MS:
            tic = utils.math_div_even(tic, utils.US_MILLISECOND)
        elif my_reso == utils.DT_NPY_UNIT_SS:
            tic = utils.math_div_even(tic, utils.US_SECOND)
        #: else 'us' -> as-is

        # Compare
        return pd.Index(utils.arr_lt(self.values, tic), name="is_past")

    def is_future(self) -> pd.Index[bool]:
        """Element-wise check whether datetimes are in the future `<'Index[bool]'>`.

        ## Equivalent
        >>> self > datetime.datetime.now(self.tzinfo)
        """
        # Get current datetime in the same timezone
        dt: datetime.datetime = utils.dt_now(self.tzinfo, None)

        # Convert to the same resolution
        my_reso: cython.int = utils.nptime_unit_str2int(self.unit)
        tic: cython.longlong = utils.dt_to_us(dt, True)
        if my_reso == utils.DT_NPY_UNIT_NS:
            tic *= utils.NS_MICROSECOND
        elif my_reso == utils.DT_NPY_UNIT_MS:
            tic = utils.math_div_even(tic, utils.US_MILLISECOND)
        elif my_reso == utils.DT_NPY_UNIT_SS:
            tic = utils.math_div_even(tic, utils.US_SECOND)
        #: else 'us' -> as-is

        # Compare
        return pd.Index(utils.arr_gt(self.values, tic), name="is_future")
