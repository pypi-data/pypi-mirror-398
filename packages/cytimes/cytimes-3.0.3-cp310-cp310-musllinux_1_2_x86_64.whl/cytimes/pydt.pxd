# cython: language_level=3

from cpython cimport datetime

# Pydt (Python Datetime)
cdef class _Pydt(datetime.datetime):
    cdef: 
        object __cls
    # Convertor
    cpdef str ctime(self)
    cpdef str strftime(self, str format)
    cpdef str isoformat(self, str sep=?)
    cpdef dict timedict(self)
    cpdef dict utctimedict(self)
    cpdef object timetuple(self)
    cpdef object utctimetuple(self)
    cpdef int toordinal(self) except -1
    cpdef double toseconds(self, bint utc=?)
    cpdef long long tomicroseconds(self, bint utc=?)
    cpdef double timestamp(self)
    cpdef datetime.date date(self)
    cpdef datetime.time time(self)
    cpdef datetime.time timetz(self)
    # Internal
    cdef inline object _cls(self)
    # Manipulator
    cpdef _Pydt replace(
        self, int year=?, int month=?, int day=?,
        int hour=?, int minute=?, int second=?,
        int microsecond=?, object tzinfo=?, int fold=?,
    )
    # . year
    cpdef _Pydt to_curr_year(self, object month=?, int day=?)
    cpdef _Pydt to_prev_year(self, object month=?, int day=?)
    cpdef _Pydt to_next_year(self, object month=?, int day=?)
    cpdef _Pydt to_year(self, int offset, object month=?, int day=?)
    # . quarter
    cpdef _Pydt to_curr_quarter(self, int month=?, int day=?)
    cpdef _Pydt to_prev_quarter(self, int month=?, int day=?)
    cpdef _Pydt to_next_quarter(self, int month=?, int day=?)
    cpdef _Pydt to_quarter(self, int offset, int month=?, int day=?)
    # . month
    cpdef _Pydt to_curr_month(self, int day=?)
    cpdef _Pydt to_prev_month(self, int day=?)
    cpdef _Pydt to_next_month(self, int day=?)
    cpdef _Pydt to_month(self, int offset, int day=?)
    # . weekday
    cpdef _Pydt to_monday(self)
    cpdef _Pydt to_tuesday(self)
    cpdef _Pydt to_wednesday(self)
    cpdef _Pydt to_thursday(self)
    cpdef _Pydt to_friday(self)
    cpdef _Pydt to_saturday(self)
    cpdef _Pydt to_sunday(self)
    cpdef _Pydt to_curr_weekday(self, object weekday=?)
    cpdef _Pydt to_prev_weekday(self, object weekday=?)
    cpdef _Pydt to_next_weekday(self, object weekday=?)
    cpdef _Pydt to_weekday(self, int offset, object weekday=?)
    cdef inline _Pydt _to_curr_weekday(self, int weekday)
    # . day
    cpdef _Pydt to_yesterday(self)
    cpdef _Pydt to_tomorrow(self)
    cpdef _Pydt to_day(self, int offset)
    # . date&time
    cpdef _Pydt normalize(self)
    cpdef _Pydt to_datetime(
        self, int year=?, int month=?, int day=?,
        int hour=?, int minute=?, int second=?, int microsecond=?,
    )
    cpdef _Pydt to_date(self, int year=?, int month=?, int day=?)
    cpdef _Pydt to_time(self, int hour=?, int minute=?, int second=?, int microsecond=?)
    cpdef _Pydt to_first_of(self, str unit)
    cpdef _Pydt to_last_of(self, str unit)
    cpdef _Pydt to_start_of(self, str unit)
    cpdef _Pydt to_end_of(self, str unit)
    cpdef bint is_first_of(self, str unit) except -1
    cpdef bint is_last_of(self, str unit) except -1
    cpdef bint is_start_of(self, str unit) except -1
    cpdef bint is_end_of(self, str unit) except -1
    # . round / ceil / floor
    cpdef _Pydt round(self, str unit)
    cpdef _Pydt ceil(self, str unit)
    cpdef _Pydt floor(self, str unit)
    # . fsp (fractional seconds precision)
    cpdef _Pydt fsp(self, int precision)
    # Calendar
    # . iso
    cpdef dict isocalendar(self)
    cpdef int isoyear(self) noexcept
    cpdef int isoweek(self) noexcept
    cpdef int isoweekday(self) noexcept
    # . year
    cpdef int access_year(self) noexcept
    cpdef bint is_year(self, int year) noexcept
    cpdef bint is_leap_year(self) noexcept
    cpdef bint is_long_year(self) noexcept
    cpdef int leap_bt_year(self, int year) noexcept
    cpdef int days_in_year(self) noexcept
    cpdef int days_bf_year(self) noexcept
    cpdef int day_of_year(self) noexcept
    # . quarter
    cpdef int access_quarter(self) noexcept
    cpdef bint is_quarter(self, int quarter) noexcept
    cpdef int days_in_quarter(self) noexcept
    cpdef int days_bf_quarter(self) noexcept
    cpdef int day_of_quarter(self) noexcept
    # . month
    cpdef int access_month(self) noexcept
    cpdef bint is_month(self, object month) noexcept
    cpdef int days_in_month(self) noexcept
    cpdef int days_bf_month(self) noexcept
    cpdef int day_of_month(self) noexcept
    cpdef str month_name(self, object locale=?)
    # . weekday
    cpdef int access_weekday(self) noexcept
    cpdef bint is_weekday(self, object weekday) noexcept
    cpdef str weekday_name(self, object locale=?)
    # . day
    cpdef int access_day(self) noexcept
    cpdef bint is_day(self, int day) noexcept
    # . time
    cpdef int access_hour(self) noexcept
    cpdef int access_minute(self) noexcept
    cpdef int access_second(self) noexcept
    cpdef int access_millisecond(self) noexcept
    cpdef int access_microsecond(self) noexcept
    # Timezone
    cpdef object access_tzinfo(self)
    cpdef int access_fold(self) noexcept
    cpdef bint is_local(self) except -1
    cpdef bint is_utc(self) except -1
    cpdef bint is_dst(self) except -1
    cpdef str tzname(self)
    cpdef datetime.timedelta utcoffset(self)
    cpdef object utcoffset_seconds(self)
    cpdef datetime.timedelta dst(self)
    cpdef _Pydt astimezone(self, object tz=?)
    cpdef _Pydt tz_localize(self, object tz)
    cpdef _Pydt tz_convert(self, object tz)
    cpdef _Pydt tz_switch(self, object targ_tz, object base_tz=?, bint naive=?)
    # Arithmetic
    cpdef _Pydt add(
        self, int years=?, int quarters=?, int months=?, 
        int weeks=?, int days=?, int hours=?, int minutes=?, 
        int seconds=?, int milliseconds=?, int microseconds=?
    )
    cpdef _Pydt sub(
        self, int years=?, int quarters=?, int months=?, 
        int weeks=?, int days=?, int hours=?, int minutes=?, 
        int seconds=?, int milliseconds=?, int microseconds=?
    )
    cpdef long long diff(self, object dtobj, str unit, bint absolute=?, str inclusive=?)
    # Comparison
    cpdef bint is_past(self) except -1
    cpdef bint is_future(self) except -1
