# cython: language_level=3

from cpython cimport datetime
from cpython.unicode cimport (
    PyUnicode_READ_CHAR as str_read,
    PyUnicode_GET_LENGTH as str_len,
    PyUnicode_FromOrdinal as str_chr,
    PyUnicode_Replace as str_replace,
)
from cytimes cimport utils

# Timelex
ctypedef enum State:
    START     = 0
    DIGIT     = 1
    DIGIT_DOT = 2
    ALPHA     = 3
    ALPHA_DOT = 4

cdef inline list _timelex(str data, Py_ssize_t pos, Py_ssize_t length=0):
    """Tokenize a datetime-like string into lexical units (tokens).

    This lexer performs a single left-to-right pass over `data` and emits tokens
    based on `maximal runs` of letters or digits, while preserving separators
    as individual one-character tokens. It is optimized for datetime strings
    (ISO/RFC-like), and implements special handling for dots and decimal commas.

    :param data `<'str'>`: The datetime string to be tokenized.
    :param pos `<'int'>`: Start position (0-based index) within *data*. 
        Negative values are clamped to 0.
    :param length `<'int'>`: Optional length of the input 'data' string. Defaults to `0`.
        If 'length <= 0', computes the length of the 'data' string internally.
    :returns `<'list[str]'>`: A list of tokens that are either:

        * Maximal runs of letters (Unicode-aware) or ASCII digits
        * Individual one-character separators (including spaces and punctuation),
        * A single normalized numeric token.
    """
    # Validate bounds
    if length <= 0:
        length = str_len(data)
    if pos < 0:
        pos = 0
    elif pos >= length:
        return []

    # Setup
    cdef:
        State state
        list tokens = []
        str  token, sub_token
        Py_UCS4 ch              # current character
        Py_UCS4 ch_cache = 0    # cache character for next token
        Py_ssize_t i            # index for 'token'
        Py_ssize_t dot_count    # total 'dot' count in 'token'
        Py_ssize_t com_count    # total 'comma' count in 'token'
        bint is_dot_end         # is 'token' ends with a 'dot'
        bint is_com_end         # is 'token' ends with a 'comma'

    # Skip leading control & space characters
    while pos < length and utils.is_ascii_ctl_or_space(str_read(data, pos)):
        pos += 1

    # Main loop: begin -------------------------------------------------------
    while pos < length:
        # Reset
        state = State.START
        token = None
        dot_count = com_count = 0
        is_dot_end = is_com_end = False

        # Nested loop: begin - - - - - - - - - - - - - - - - - - - - - - - - -
        while pos < length:
            # Read new character
            if ch_cache == 0:
                ch = str_read(data, pos)
                # . normalize space
                if utils.is_ascii_ctl_or_space(ch):
                    ch = 32  # 'space'
                    # remove adjacent spaces*
                    while utils.is_ascii_ctl_or_space(str_read(data, pos + 1)):
                        pos += 1
            # Comsume cache
            else:
                ch = ch_cache
                ch_cache = 0

            # State: START
            if state == State.START:
                # . digit (e.g: 1)
                if utils.is_ascii_digit(ch):
                    token = str_chr(ch)             # collect digit
                    state = State.DIGIT             # set state: DIGIT
                    is_dot_end = is_com_end = False
                # . alpha (e.g: a)
                elif utils.is_alpha(ch):
                    token = str_chr(ch)             # collect alpha
                    state = State.ALPHA             # set state: ALPHA
                    is_dot_end = is_com_end = False
                # . emit single character token
                else:
                    tokens.append(str_chr(ch))
                    pos += 1
                    break   # end token; start a new one

            # State: DIGIT
            elif state == State.DIGIT:
                # . digit (e.g: [X]12)
                if utils.is_ascii_digit(ch):
                    token += str_chr(ch)            # collect digit
                    is_dot_end = is_com_end = False
                # . dot   (e.g: [X]1.)
                elif ch == '.':
                    token += "."                    # collect dot
                    dot_count += 1                  # increase dot count
                    state = State.DIGIT_DOT         # set state: DIGIT_DOT
                    is_dot_end, is_com_end = True, False
                # . comma (e.g: [X]1,)
                elif ch == ',' and dot_count == 0 and com_count == 0:
                    token += ","                    # collect comma
                    com_count += 1                  # increase comma count
                    state = State.DIGIT_DOT         # set state: DIGIT_DOT
                    is_dot_end, is_com_end = False, True
                # . cache for next token & stop
                else:
                    ch_cache = ch
                    break

            # State: DIGIT_DOT
            elif state == State.DIGIT_DOT:
                # . digit (e.g: [X]1.2)
                if utils.is_ascii_digit(ch):
                    token += str_chr(ch)            # collect digit
                    is_dot_end = is_com_end = False
                # . alpha (e.g: [X]1.a)
                elif is_dot_end and utils.is_alpha(ch):
                    token += str_chr(ch)            # collect alpha
                    state = State.ALPHA_DOT  # set state: ALPHA_DOT
                    is_dot_end = is_com_end = False
                # . dot   (e.g: [X]1.2.)
                elif ch == '.':
                    token += "."                    # collect dot
                    dot_count += 1                  # increase dot count
                    is_dot_end, is_com_end = True, False
                # . cache for next token & stop
                else:
                    ch_cache = ch
                    break

            # State: ALPHA
            elif state == State.ALPHA:
                # . alpha (e.g: [X]ab)
                if utils.is_alpha(ch):
                    token += str_chr(ch)            # collect alpha
                    is_dot_end = is_com_end = False
                # . dot   (e.g: [X]a.)
                elif ch == ".":
                    token += "."                    # collect dot
                    dot_count += 1                  # increase dot count
                    state = State.ALPHA_DOT         # set state: ALPHA_DOT
                    is_dot_end, is_com_end = True, False
                # . cache for next token & stop
                else:
                    ch_cache = ch
                    break

            # State: ALPHA_DOT
            else:
                # . alpha (e.g: [X]a.b)
                if utils.is_alpha(ch):
                    token += str_chr(ch)            # collect alpha
                    is_dot_end = is_com_end = False
                # . digit (e.g: [X]a.1)
                elif is_dot_end and utils.is_ascii_digit(ch):
                    token += str_chr(ch)            # collect digit
                    state = State.DIGIT_DOT         # set state: DIGIT_DOT
                    is_dot_end = is_com_end = False
                # . dot   (e.g: [X]a.b.)
                elif ch == '.':
                    token += "."                    # collect dot
                    dot_count += 1                  # increase dot count
                    is_dot_end, is_com_end = True, False
                # . cache for next token & stop
                else:
                    ch_cache = ch
                    break

            # Next character
            pos += 1
                    
        # Add token
        if token is not None:
            # Pure alpha or digit token
            if state in (State.ALPHA, State.DIGIT):
                tokens.append(token)

            # Mixed token with dots/commas => split into sub-tokens
            elif state == State.ALPHA_DOT or is_dot_end or is_com_end or dot_count > 1 or com_count > 1:
                sub_token = None
                for i in range(str_len(token)):
                    ch = str_read(token, i)
                    if ch == '.':
                        if sub_token is not None:
                            tokens.append(sub_token)
                            sub_token = None
                        tokens.append(".")
                    elif ch == ',':
                        if sub_token is not None:
                            tokens.append(sub_token)
                            sub_token = None
                        tokens.append(",")
                    else:
                        if sub_token is None:
                            sub_token = str_chr(ch)
                        else:
                            sub_token += str_chr(ch)
                if sub_token is not None:
                    tokens.append(sub_token)

            # Decimal comma normalization (e.g., '1,234' -> '1.234')
            elif state == State.DIGIT_DOT and com_count == 1 and dot_count == 0:
                tokens.append(str_replace(token, ",", ".", -1))

            # Other cases
            else:
                tokens.append(token)

        # Nested loop: break - - - - - - - - - - - - - - - - - - - - - - - - -

    # Main loop: break -------------------------------------------------------
    return tokens

cpdef list timelex(str dtstr)

# Configs
cdef:
    set _DEFAULT_PERTAIN 
    set _DEFAULT_JUMP
    set _DEFAULT_UTC
    dict _DEFAULT_TZ
    dict _DEFAULT_MONTH
    dict _DEFAULT_WEEKDAY
    dict _DEFAULT_HMS
    dict _DEFAULT_AMPM

cdef class Configs:
    cdef:
        # . settings
        bint _yearfirst
        bint _dayfirst
        set _jump, _jump_ext
        set _pertain, _pertain_ext
        set _utc, _utc_ext
        dict _tz, _tz_ext
        dict _month, _month_ext
        dict _weekday, _weekday_ext
        dict _hms, _hms_ext
        dict _ampm, _ampm_ext
        # . internal
        object __cls
    # Y/M/D
    cpdef str order_hint(self)
    #  Jump
    cpdef bint add_jump(self, str token) except -1
    cpdef bint remove_jump(self, str token) except -1
    cpdef bint replace_jump(self, set tokens=?) except -1
    cpdef bint is_jump(self, str token) except -1
    # Pertain
    cpdef bint add_pertain(self, str token) except -1
    cpdef bint remove_pertain(self, str token) except -1
    cpdef bint replace_pertain(self, set tokens=?) except -1
    cpdef bint is_pertain(self, str token) except -1
    # UTC
    cpdef bint add_utc(self, str token) except -1
    cpdef bint remove_utc(self, str token) except -1
    cpdef bint replace_utc(self, set tokens=?) except -1
    cpdef bint is_utc(self, str token) except -1
    # Timezone
    cpdef bint add_tz(self, str token, int hours=?, int minutes=?, int seconds=?) except -1
    cpdef bint remove_tz(self, str token) except -1
    cpdef bint replace_tz(self, dict mapping=?) except -1
    cpdef bint is_tz(self, str token) except -1
    cpdef int get_tz_offset(self, str token) except -200_000
    # Month
    cpdef bint add_month(self, str token, int month) except -1
    cpdef bint remove_month(self, str token) except -1
    cpdef bint replace_month(self, dict mapping=?) except -1
    cpdef bint is_month(self, str token) except -1
    cpdef int get_month(self, str token) except -2
    # Weekday
    cpdef bint add_weekday(self, str token, int weekday) except -1
    cpdef bint remove_weekday(self, str token) except -1
    cpdef bint replace_weekday(self, dict mapping=?) except -1
    cpdef bint is_weekday(self, str token) except -1
    cpdef int get_weekday(self, str token) except -2
    # HMS
    cpdef bint add_hms(self, str token, int flag) except -1
    cpdef bint remove_hms(self, str token) except -1
    cpdef bint replace_hms(self, dict mapping=?) except -1
    cpdef bint is_hms(self, str token) except -1
    cpdef int get_hms(self, str token) except -2
    # AM/PM
    cpdef bint add_ampm(self, str token, int flag) except -1
    cpdef bint remove_ampm(self, str token) except -1
    cpdef bint replace_ampm(self, dict mapping=?) except -1
    cpdef bint is_ampm(self, str token) except -1
    cpdef int get_ampm(self, str token) except -2
    # Clear & Reset
    cpdef bint clear_settings(self) except -1
    cpdef bint reset_settings(self) except -1
    # Internal
    # . token
    cdef inline str _ensure_str_token(self, str namespace, object token)
    cdef inline str _validate_token(self, str namespace, str token)
    cdef inline str _lowercase_token(self, str namespace, str token)
    cdef inline tuple _gen_token_case_variants(self, str token)
    # . value
    cdef inline int _ensure_int_value(self, str namespace, object value)
    cdef inline int _validate_value(self, str namespace, int value, int minimum, int maximum)
    # . class
    cdef inline object _cls(self)

cdef Configs _DEFAULT_CONFIGS

# Parser
cdef class Result:
    cdef:
        # . Y/M/D
        int _ymd[3]
        int _idx
        int _yidx
        int _midx
        int _didx
        bint _resolved
        # . values
        int year
        int month
        int day
        int hour
        int minute
        int second
        int microsecond
        int weekday
        int doy
        int ampm
        int tzoffset
        bint tzoffset_finalized
        bint century_specified
    # Y/M/D
    cdef inline bint set_ymd_int(self, int flag, long long value) except -1
    cdef inline bint set_ymd_str(self, int flag, str token, Py_ssize_t token_len=?) except -1
    cdef inline int ymd_slots_filled(self) noexcept
    cdef inline int ymd_roles_resolved(self) noexcept
    cdef inline bint could_be_day(self, long long value) noexcept
    cdef inline bint could_be_doy(self, long long value) noexcept
    # Resolve
    cdef inline bint resolve(self, bint yearfirst, bint dayfirst) noexcept
    cdef inline bint valid(self) noexcept
    cdef inline bint is_year_set(self) noexcept
    cdef inline bint is_month_set(self) noexcept
    cdef inline bint is_day_set(self) noexcept
    cdef inline bint is_hour_set(self) noexcept
    cdef inline bint is_minute_set(self) noexcept
    cdef inline bint is_second_set(self) noexcept
    cdef inline bint is_microsecond_set(self) noexcept
    cdef inline bint is_weekday_set(self) noexcept
    cdef inline bint is_doy_set(self) noexcept
    cdef inline bint is_ampm_set(self) noexcept
    cdef inline bint is_tzoffset_set(self) noexcept
    # Internal
    cdef inline bint _record_ymd(self, int flag, int value) noexcept
    cdef inline bint _reset(self) noexcept

cdef class Parser:
    cdef:
        bint _ignoretz
        Configs _cfg
        Result _res
        Py_ssize_t _pos
        Py_ssize_t _length
        list _tokens
        str _token1
        object __cls
    # Parse
    cpdef datetime.datetime parse(self, str dtstr, object default=?, object yearfirst=?, object dayfirst=?, bint ignoretz=?, bint isoformat=?, object dtclass=?)
    cdef inline bint _process(self, str dtstr, bint isoformat) except -1
    # Build
    cdef inline datetime.datetime _build(self, str dtstr, object default, object dtclass)
    cdef inline datetime.datetime _gen_dt(self, object default, object tzinfo, object dtclass)
    # ISO format - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    cdef inline bint _process_iso_format(self, str dtstr) except -1
    # . parser
    cdef inline bint _parse_iso_date(self, str dtstr) except -1
    cdef inline bint _parse_iso_time(self, str dtstr) except -1
    cdef inline bint _parse_iso_extra(self, str dtstr) except -1
    # Timelex tokens - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    cdef inline bint _process_timelex_tokens(self, str dtstr) except -1
    # . parser
    cdef inline bint _parse_token_numeric(self, str token) except -1
    cdef inline bint _parse_token_month(self, str token) except -1
    cdef inline bint _parse_iso_week(self, str token) except -1
    cdef inline bint _parse_token_weekday(self, str token) except -1
    cdef inline bint _parse_token_ampm(self, str token) except -1
    cdef inline bint _parse_token_tzname(self, str token) except -1
    cdef inline bint _parse_token_tzoffset(self, str token) except -1
    # . tokens
    cdef inline bint _has_token(self, Py_ssize_t offset) noexcept
    cdef inline str _get_token(self, Py_ssize_t offset)
    cdef inline str _get_token1(self)
    cdef inline str _get_next_token(self)
    cdef inline bint _reset_token_peeks(self) noexcept
    # . setters
    cdef inline bint _set_ymd_by_token(self, int flag, str token=?, Py_ssize_t token_len=?, int token_kind=?) except -1
    cdef inline bint _set_hms_by_token(self, int flag, str token=?, Py_ssize_t token_len=?, int token_kind=?) except -1
    cdef inline bint _set_hour_by_token(self, str token=?, Py_ssize_t token_len=?, int token_kind=?) except -1
    cdef inline bint _set_minute_by_token(self, str token=?, Py_ssize_t token_len=?, int token_kind=?) except -1
    cdef inline bint _set_second_by_token(self, str token=?, Py_ssize_t token_len=?, int token_kind=?) except -1
    cdef inline int _adjust_hour_by_ampm(self, int hour, int flag) except -1
    # Internal
    cdef inline object _cls(self)

cdef Parser _DEFAULT_PARSER

# Parse
cpdef datetime.datetime parse(str dtstr, object default=?, object yearfirst=?, object dayfirst=?, bint ignoretz=?, bint isoformat=?, Configs cfg=?, object dtclass=?)
cpdef datetime.datetime parse_obj(object dtobj, object default=?, object yearfirst=?, object dayfirst=?, bint ignoretz=?, bint isoformat=?, Configs cfg=?, object dtclass=?)
cpdef int parse_month(object token, Configs cfg=?, bint raise_error=?) except -2
cpdef int parse_weekday(object token, Configs cfg=?, bint raise_error=?) except -2