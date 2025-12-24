# cython: language_level=3

from cpython cimport datetime

# Constants
cdef tuple _WEEKDAY_REPRS

# Delta
cdef class Delta:
    cdef:
        int _years
        int _months
        long long _days
        int _hours
        int _minutes
        int _seconds
        int _microseconds
        int _year
        int _month
        int _day
        int _weekday
        int _hour
        int _minute
        int _second
        int _microsecond
        long long _hashcode
    # Arithmetic: addition
    cdef inline datetime.date _add_date(self, datetime.date o)
    cdef inline datetime.datetime _add_datetime(self, datetime.datetime o)
    cdef inline Delta _add_timedelta(self, datetime.timedelta o)
    cdef inline Delta _add_delta(self, Delta o)
    # Arithmetic: subtraction
    cdef inline Delta _sub_timedelta(self, datetime.timedelta o)
    cdef inline Delta _sub_delta(self, Delta o)
    # Arithmetic: right subtraction
    cdef inline datetime.date _rsub_date(self, datetime.date o)
    cdef inline datetime.datetime _rsub_datetime(self, datetime.datetime o)
    cdef inline Delta _rsub_timedelta(self, datetime.timedelta o)
    # Comparison
    cdef inline bint _eq_timedelta(self, datetime.timedelta o) noexcept
    cdef inline bint _eq_delta(self, Delta o) noexcept
