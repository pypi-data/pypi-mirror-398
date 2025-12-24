# cython: language_level=3
# cython: wraparound=False
# cython: boundscheck=False

# Cython imports
import cython

# Python imports
from pytz.exceptions import (
    AmbiguousTimeError as PytzAmbiguousTimeError,
    NonExistentTimeError as PytzNonExistentTimeError,
)
from pandas.errors import OutOfBoundsDatetime as PdOutOfBoundsDatetime
from pandas._libs.tslibs.parsing import DateParseError as PdDateParseError


# Base Exceptions ---------------------------------------------------------------------------------
class cyTimesError(Exception):
    """The base error for the cyTimes package."""


class cyTimesTypeError(cyTimesError, TypeError):
    """The base TypeError for the cyTimes package."""


class cyTimesValueError(cyTimesError, ValueError):
    """The base ValueError for the cyTimes package."""


# Delta Exceptions --------------------------------------------------------------------------------
class DeltaError(cyTimesError):
    """The base error for the Delta module."""


class InvalidRelativeDelta(DeltaError, cyTimesTypeError):
    """Error for invalid RelativeDelta value."""


# Parser Exceptions -------------------------------------------------------------------------------
class ParserError(cyTimesError):
    """The base error for the Parser module."""


class ParserFailedError(ParserError, cyTimesValueError):
    """Error for failed parsing"""


# . configs
class ConfigsError(ParserError):
    """Error for the 'parser.Configs' when the settings are invalid."""


class InvalidConfigsToken(ConfigsError, cyTimesValueError):
    """Error for the 'parser.Configs' when the token is invalid."""


class InvalidConfigsValue(ConfigsError, cyTimesValueError):
    """Error for the 'parser.Configs' when the value is invalid."""


class InvalidParserInfo(ConfigsError, cyTimesTypeError):
    """Error for Configs importing invalid 'dateutil.parser.parserinfo'."""


# Pydt/Pddt Exceptions ----------------------------------------------------------------------------
class DatetimeError(cyTimesError):
    """The base error for the datetime module."""


class PydtError(DatetimeError):
    """The base error for the pydt module."""


class PddtError(DatetimeError):
    """The base error for the pddt module."""


class InvalidArgumentError(PydtError, PddtError, cyTimesValueError):
    """Error for invalid arguments."""


class InvalidTypeError(InvalidArgumentError, cyTimesTypeError):
    """Error for invalid type."""


class InvalidTimezoneError(InvalidArgumentError):
    """Error for invalid timezone value."""


class InvalidMonthError(InvalidArgumentError, ParserError):
    """Error for invalid month value."""


class InvalidWeekdayError(InvalidArgumentError, ParserError):
    """Error for invalid weekday value."""


class OutOfBoundsError(InvalidArgumentError, PdOutOfBoundsDatetime):
    """Error for 'dtsobj' that has datetimes out of bounds."""


class AmbiguousTimeError(
    InvalidArgumentError,
    PytzAmbiguousTimeError,
    PytzNonExistentTimeError,
):
    """Error for ambiguous time."""


class MixedTimezoneError(InvalidTypeError):
    """Error for mixing tz-aware and tz-naive datetime objects."""


# Raise error helpers -----------------------------------------------------------------------------
@cython.ccall
@cython.exceptval(-1, check=False)
def raise_error(
    exc: object,
    cls: object = None,
    input_msg: str = None,
    error_msg: str = None,
    tb_exc: Exception = None,
) -> cython.bint:
    """Raise error.

    :param exc `<'type[Exception]'>`: The error Exception type to raise.
    :param cls `<'type/None'>`: Optional object class raises the error. Defaults to `None`.
    :param input_msg `<'str/None'>`: Optional `'Invalid 'X' input'` message. Defaults to `None`.
    :param error_msg `<'str/None'>`: Optional error message. Defaults to `None`.
    :param tb_exc `<'Exception/None'>`: Optional traceback exception. Defaults to `None`.
    """
    l: list = []
    if input_msg is not None:
        l.append("Invalid '%s' input." % (input_msg))
    if error_msg is not None:
        l.append(error_msg)
    if tb_exc is not None:
        l.append(str(tb_exc))

    if cls is not None:
        msg = "<'%s'> %s" % (cls.__name__, "\n".join(l))
    else:
        msg = "\n".join(l)

    if tb_exc is None:
        raise exc(msg)
    else:
        raise exc(msg) from tb_exc


@cython.ccall
@cython.exceptval(-1, check=False)
def raise_configs_token_error(
    cls: object = None,
    error_msg: str = None,
    tb_exc: Exception = None,
) -> cython.bint:
    """Raise `<'InvalidConfigsToken'>` error.

    :param cls `<'type/None'>`: Optional object class raises the error. Defaults to `None`.
    :param error_msg `<'str/None'>`: Optional error message. Defaults to `None`.
    :param tb_exc `<'Exception/None'>`: Optional traceback exception. Defaults to `None`.
    :raises `<'InvalidConfigsToken'>`:
    """
    raise_error(InvalidConfigsToken, cls, None, error_msg, tb_exc)


@cython.ccall
@cython.exceptval(-1, check=False)
def raise_configs_value_error(
    cls: object = None,
    error_msg: str = None,
    tb_exc: Exception = None,
) -> cython.bint:
    """Raise `<'InvalidConfigsValue'>` error.

    :param cls `<'type/None'>`: Optional object class raises the error. Defaults to `None`.
    :param error_msg `<'str/None'>`: Optional error message. Defaults to `None`.
    :param tb_exc `<'Exception/None'>`: Optional traceback exception. Defaults to `None`.
    :raises `<'InvalidConfigsValue'>`:
    """
    raise_error(InvalidConfigsValue, cls, None, error_msg, tb_exc)


@cython.ccall
@cython.exceptval(-1, check=False)
def raise_parser_failed_error(
    cls: object = None,
    error_msg: str = None,
    tb_exc: Exception = None,
) -> cython.bint:
    """Raise `<'ParserFailedError'>` error.

    :param cls `<'type/None'>`: Optional object class raises the error. Defaults to `None`.
    :param error_msg `<'str/None'>`: Optional error message. Defaults to `None`.
    :param tb_exc `<'Exception/None'>`: Optional traceback exception. Defaults to `None`.
    :raises `<'ParserFailedError'>`:
    """
    raise_error(ParserFailedError, cls, None, error_msg, tb_exc)


@cython.ccall
@cython.exceptval(-1, check=False)
def raise_argument_error(
    cls: object = None,
    input_msg: str = None,
    error_msg: str = None,
    tb_exc: Exception = None,
) -> cython.bint:
    """Raise `<'InvalidArgumentError'>` error.

    :param cls `<'type/None'>`: Optional object class raises the error. Defaults to `None`.
    :param input_msg `<'str/None'>`: Optional `'Invalid 'X' input'` message. Defaults to `None`.
    :param error_msg `<'str/None'>`: Optional error message. Defaults to `None`.
    :param tb_exc `<'Exception/None'>`: Optional traceback exception. Defaults to `None`.
    :raises `<'InvalidArgumentError'>`:
    """
    raise_error(InvalidArgumentError, cls, input_msg, error_msg, tb_exc)


@cython.ccall
@cython.exceptval(-1, check=False)
def raise_type_error(
    cls: object = None,
    input_msg: str = None,
    error_msg: str = None,
    tb_exc: Exception = None,
) -> cython.bint:
    """Raise `<'InvalidTypeError'>` error.

    :param cls `<'type/None'>`: Optional object class raises the error. Defaults to `None`.
    :param input_msg `<'str/None'>`: Optional `'Invalid 'X' input'` message. Defaults to `None`.
    :param error_msg `<'str/None'>`: Optional error message. Defaults to `None`.
    :param tb_exc `<'Exception/None'>`: Optional traceback exception. Defaults to `None`.
    :raises `<'InvalidTypeError'>`:
    """
    raise_error(InvalidTypeError, cls, input_msg, error_msg, tb_exc)
