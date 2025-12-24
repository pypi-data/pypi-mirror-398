from typing import Any, Literal, Hashable
from typing_extensions import Self, TypeVar
import datetime
import numpy as np
import pandas as pd
from pandas._typing import Scalar
from pandas._libs import lib
from cytimes.pydt import Pydt
from cytimes.parser import Configs
from cytimes.utils import SENTINEL

# Types
DatetimeLike = TypeVar("DatetimeLike", bound=str | datetime.date | np.datetime64)
ArrayLike = TypeVar("ArrayLike", bound=list | tuple | np.ndarray | pd.Series | pd.Index)

# Pddt
class Pddt(pd.DatetimeIndex):
    def __new__(
        cls,
        data: ArrayLike,
        freq: str | datetime.timedelta | pd.offsets.BaseOffset | None = None,
        tz: datetime.tzinfo | str | None = None,
        ambiguous: np.ndarray[bool] | Literal["infer", "NaT", "raise"] = "raise",
        yearfirst: bool = True,
        dayfirst: bool = False,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        copy: bool = False,
        name: Hashable | None = None,
        cfg: Configs | None = None,
    ) -> Self: ...
    # Constructor ------------------------------------------------------
    @classmethod
    def date_range(
        cls,
        start: DatetimeLike | None = None,
        end: DatetimeLike | None = None,
        periods: int | None = None,
        freq: str | datetime.timedelta | pd.offsets.BaseOffset | None = "D",
        tz: datetime.tzinfo | str | None = None,
        normalize: bool = False,
        inclusive: Literal["left", "right", "both", "neither"] = "both",
        unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def parse(
        cls,
        data: ArrayLike,
        freq: str | datetime.timedelta | pd.offsets.BaseOffset | None = None,
        tz: datetime.tzinfo | str | None = None,
        ambiguous: np.ndarray[bool] | Literal["infer", "NaT", "raise"] = "raise",
        yearfirst: bool = True,
        dayfirst: bool = False,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        copy: bool = False,
        name: Hashable | None = None,
        cfg: Configs | None = None,
    ) -> Self: ...
    @classmethod
    def now(
        cls,
        size: int | Any,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def utcnow(
        cls,
        size: int | Any,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def today(
        cls,
        size: int | Any,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def combine(
        cls,
        size: int | Any,
        date: datetime.date | str | None = None,
        time: datetime.time | str | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromordinal(
        cls,
        ordinal: int | ArrayLike,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromseconds(
        cls,
        seconds: int | float | ArrayLike,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def frommicroseconds(
        cls,
        us: int | ArrayLike,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromtimestamp(
        cls,
        ts: int | float | ArrayLike,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def utcfromtimestamp(
        cls,
        ts: int | float | ArrayLike,
        size: int | Any | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromisoformat(
        cls,
        dtstr: str | ArrayLike,
        size: int | Any | None = None,
        unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromisocalendar(
        cls,
        iso: dict | list | tuple | pd.DataFrame,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromdayofyear(
        cls,
        iso: dict | list | tuple | pd.DataFrame,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromdate(
        cls,
        date: datetime.date | ArrayLike,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromdatetime(
        cls,
        dt: DatetimeLike | ArrayLike,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def fromdatetime64(
        cls,
        dt64: DatetimeLike | ArrayLike,
        size: int | Any | None = None,
        tz: datetime.tzinfo | str | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    @classmethod
    def strptime(
        cls,
        dtstr: str | ArrayLike,
        fmt: str,
        size: int | Any | None = None,
        as_unit: Literal["s", "ms", "us", "ns"] | None = None,
        name: Hashable | None = None,
    ) -> Self: ...
    # Convertor --------------------------------------------------------
    def ctime(self) -> pd.Index[str]: ...
    def strftime(self, fmt: str) -> pd.Index[str]: ...
    def isoformat(self, sep: str = "T") -> pd.Index[str]: ...
    def timedf(self) -> pd.DataFrame: ...
    def utctimedf(self) -> pd.DataFrame: ...
    def toordinal(self) -> pd.Index[np.int64]: ...
    def toseconds(self, utc: bool = False) -> pd.Index[np.float64]: ...
    def tomicroseconds(self, utc: bool = False) -> pd.Index[np.int64]: ...
    def timestamp(self) -> pd.Index[np.float64]: ...
    def datetime(self) -> np.ndarray[Pydt]: ...
    def date(self) -> np.ndarray[datetime.date]: ...
    def time(self) -> np.ndarray[datetime.time]: ...
    def timetz(self) -> np.ndarray[datetime.time]: ...
    def to_period(self, freq: str | pd.offsets.BaseOffset | None) -> pd.PeriodIndex: ...
    def to_list(self) -> list[pd.Timestamp]: ...
    def to_numpy(
        dtype: None = None,
        copy: bool = False,
        na_value: Scalar = ...,
        **kwargs,
    ) -> np.ndarray: ...
    def to_series(
        self,
        index: pd.Index | None = None,
        name: Hashable | None = None,
    ) -> pd.Series: ...
    def to_frame(
        self,
        index: bool = True,
        name: Hashable = lib.no_default,
    ) -> pd.DataFrame: ...
    # Manipulator ------------------------------------------------------
    def replace(
        self,
        year: int = SENTINEL,
        month: int = SENTINEL,
        day: int = SENTINEL,
        hour: int = SENTINEL,
        minute: int = SENTINEL,
        second: int = SENTINEL,
        microsecond: int = SENTINEL,
        nanosecond: int = SENTINEL,
        tzinfo: datetime.tzinfo | str | None = SENTINEL,
    ) -> Self: ...
    # . year
    def to_curr_year(
        self,
        month: int | str | None = None,
        day: int = SENTINEL,
    ) -> Self: ...
    def to_prev_year(
        self,
        month: int | str | None = None,
        day: int = SENTINEL,
    ) -> Self: ...
    def to_next_year(
        self,
        month: int | str | None = None,
        day: int = SENTINEL,
    ) -> Self: ...
    def to_year(
        self,
        offset: int,
        month: int | str | None = None,
        day: int = SENTINEL,
    ) -> Self: ...
    # . quarter
    def to_curr_quarter(self, month: int = SENTINEL, day: int = SENTINEL) -> Self: ...
    def to_prev_quarter(self, month: int = SENTINEL, day: int = SENTINEL) -> Self: ...
    def to_next_quarter(self, month: int = SENTINEL, day: int = SENTINEL) -> Self: ...
    def to_quarter(
        self,
        offset: int,
        month: int = SENTINEL,
        day: int = SENTINEL,
    ) -> Self: ...
    # . month
    def to_curr_month(self, day: int = SENTINEL) -> Self: ...
    def to_prev_month(self, day: int = SENTINEL) -> Self: ...
    def to_next_month(self, day: int = SENTINEL) -> Self: ...
    def to_month(self, offset: int, day: int = SENTINEL) -> Self: ...
    # . weekday
    def to_monday(self) -> Self: ...
    def to_tuesday(self) -> Self: ...
    def to_wednesday(self) -> Self: ...
    def to_thursday(self) -> Self: ...
    def to_friday(self) -> Self: ...
    def to_saturday(self) -> Self: ...
    def to_sunday(self) -> Self: ...
    def to_curr_weekday(self, weekday: int | str | None = None) -> Self: ...
    def to_prev_weekday(self, weekday: int | str | None = None) -> Self: ...
    def to_next_weekday(self, weekday: int | str | None = None) -> Self: ...
    def to_weekday(self, offset: int, weekday: int | str | None = None) -> Self: ...
    # . day
    def to_yesterday(self) -> Self: ...
    def to_tomorrow(self) -> Self: ...
    def to_day(self, offset: int) -> Self: ...
    # . date&time
    def normalize(self) -> Self: ...
    def snap(self, freq: str | pd.offsets.BaseOffset) -> Self: ...
    def to_datetime(
        self,
        year: int = SENTINEL,
        month: int = SENTINEL,
        day: int = SENTINEL,
        hour: int = SENTINEL,
        minute: int = SENTINEL,
        second: int = SENTINEL,
        microsecond: int = SENTINEL,
        nanosecond: int = SENTINEL,
    ) -> Self: ...
    def to_date(
        self,
        year: int = SENTINEL,
        month: int = SENTINEL,
        day: int = SENTINEL,
    ) -> Self: ...
    def to_time(
        self,
        hour: int = SENTINEL,
        minute: int = SENTINEL,
        second: int = SENTINEL,
        microsecond: int = SENTINEL,
        nanosecond: int = SENTINEL,
    ) -> Self: ...
    def to_first_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W"],
    ) -> Self: ...
    def to_last_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W"],
    ) -> Self: ...
    def to_start_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W", "D", "h", "m", "s", "ms", "us", "ns"],
    ) -> Self: ...
    def to_end_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W", "D", "h", "m", "s", "ms", "us", "ns"],
    ) -> Self: ...
    def is_first_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W"],
    ) -> pd.Index[bool]: ...
    def is_last_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W"],
    ) -> pd.Index[bool]: ...
    def is_start_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W", "D", "h", "m", "s", "ms", "us", "ns"],
    ) -> pd.Index[bool]: ...
    def is_end_of(
        self,
        unit: str | Literal["Y", "Q", "M", "W", "D", "h", "m", "s", "ms", "us", "ns"],
    ) -> pd.Index[bool]: ...
    # . round / ceil / floor
    def round(self, unit: Literal["D", "h", "m", "s", "ms", "us", "ns"]) -> Self: ...
    def ceil(self, unit: Literal["D", "h", "m", "s", "ms", "us", "ns"]) -> Self: ...
    def floor(self, unit: Literal["D", "h", "m", "s", "ms", "us", "ns"]) -> Self: ...
    # . fsp (fractional seconds precision)
    def fsp(self, precision: int) -> Self: ...
    # Calendar ---------------------------------------------------------
    # . iso
    def isocalendar(self) -> pd.DataFrame: ...
    def isoyear(self) -> pd.Index[np.int64]: ...
    def isoweek(self) -> pd.Index[np.int64]: ...
    def isoweekday(self) -> pd.Index[np.int64]: ...
    # . year
    @property
    def year(self) -> pd.Index[np.int64]: ...
    def is_year(self, year: int) -> pd.Index[bool]: ...
    def is_leap_year(self) -> pd.Index[bool]: ...
    def is_long_year(self) -> pd.Index[bool]: ...
    def leap_bt_year(self, year: int) -> pd.Index[np.int64]: ...
    def days_in_year(self) -> pd.Index[np.int64]: ...
    def days_bf_year(self) -> pd.Index[np.int64]: ...
    def day_of_year(self) -> pd.Index[np.int64]: ...
    # . quarter
    @property
    def quarter(self) -> pd.Index[np.int64]: ...
    def is_quarter(self, quarter: int) -> pd.Index[bool]: ...
    def days_in_quarter(self) -> pd.Index[np.int64]: ...
    def days_bf_quarter(self) -> pd.Index[np.int64]: ...
    def day_of_quarter(self) -> pd.Index[np.int64]: ...
    # . month
    @property
    def month(self) -> pd.Index[np.int64]: ...
    def is_month(self, month: str | int) -> pd.Index[bool]: ...
    def days_in_month(self) -> pd.Index[np.int64]: ...
    def days_bf_month(self) -> pd.Index[np.int64]: ...
    def day_of_month(self) -> pd.Index[np.int64]: ...
    def month_name(self, locale: str | None = None) -> pd.Index[str]: ...
    # . weekday
    @property
    def weekday(self) -> pd.Index[np.int64]: ...
    def is_weekday(self, weekday: int | str) -> pd.Index[bool]: ...
    def weekday_name(self, locale: str | None = None) -> pd.Index[str]: ...
    # . day
    @property
    def day(self) -> pd.Index[np.int64]: ...
    def is_day(self, day: int) -> pd.Index[bool]: ...
    # . time
    @property
    def hour(self) -> pd.Index[np.int64]: ...
    @property
    def minute(self) -> pd.Index[np.int64]: ...
    @property
    def second(self) -> pd.Index[np.int64]: ...
    @property
    def millisecond(self) -> pd.Index[np.int64]: ...
    @property
    def microsecond(self) -> pd.Index[np.int64]: ...
    @property
    def nanosecond(self) -> pd.Index[np.int64]: ...
    # Timezone -----------------------------------------------------------------------------
    @property
    def tz_available(self) -> set[str]: ...
    @property
    def tz(self) -> datetime.tzinfo | None:
        """The timezone information `<'tzinfo/None'>`."""

    @property
    def tzinfo(self) -> datetime.tzinfo | None:
        """The timezone information `<'tzinfo/None'>`."""

    def is_local(self) -> bool: ...
    def is_utc(self) -> bool: ...
    def tzname(self) -> str | None: ...
    def astimezone(
        self,
        tz: datetime.tzinfo | str | None = None,
        ambiguous: np.ndarray[bool] | Literal["infer", "NaT", "raise"] = "raise",
        nonexistent: (
            datetime.timedelta
            | Literal["shift_forward", "shift_backward", "NaT", "raise"]
        ) = "raise",
    ) -> Self: ...
    def tz_localize(
        self,
        tz: datetime.tzinfo | str | None,
        ambiguous: np.ndarray[bool] | Literal["infer", "NaT", "raise"] = "raise",
        nonexistent: (
            datetime.timedelta
            | Literal["shift_forward", "shift_backward", "NaT", "raise"]
        ) = "raise",
    ) -> Self: ...
    def tz_convert(self, tz: datetime.tzinfo | str | None) -> Self: ...
    def tz_switch(
        self,
        targ_tz: datetime.tzinfo | str | None,
        base_tz: datetime.tzinfo | str | None = None,
        naive: bool = False,
        ambiguous: np.ndarray[bool] | Literal["infer", "NaT", "raise"] = "raise",
        nonexistent: (
            datetime.timedelta
            | Literal["shift_forward", "shift_backward", "NaT", "raise"]
        ) = "raise",
    ) -> Self: ...
    # Values -------------------------------------------------------------------------------
    @property
    def freq(self) -> pd.offsets.BaseOffset | None:
        """Return the frequency object if it's set, otherwise None. `<'BaseOffset/None'>`."""

    @property
    def freqstr(self) -> str | None: ...
    @property
    def inferred_freq(self) -> str | None:
        """Tries to return a string representing a frequency.
        Return `None` if it can't autodetect the frequency.
        """

    @property
    def values_naive(self) -> np.ndarray[np.datetime64]: ...
    def as_unit(self, as_unit: Literal["s", "ms", "us", "ns"]) -> Self: ...
    # Arithmetic ---------------------------------------------------------------------------
    def add(
        self,
        years: int = 0,
        quarters: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        milliseconds: int = 0,
        microseconds: int = 0,
        nanoseconds: int = 0,
    ) -> Self: ...
    def sub(
        self,
        years: int = 0,
        quarters: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        milliseconds: int = 0,
        microseconds: int = 0,
        nanoseconds: int = 0,
    ) -> Self: ...
    def diff(
        self,
        data: DatetimeLike | ArrayLike,
        unit: Literal["Y", "Q", "M", "W", "D", "h", "m", "s", "ms", "us", "ns"],
        absolute: bool = False,
        inclusive: Literal["one", "both", "neither"] = "one",
    ) -> np.ndarray[np.int64]: ...
    # Comparison ---------------------------------------------------------------------------
    def is_past(self) -> pd.Index[bool]: ...
    def is_future(self) -> pd.Index[bool]: ...
