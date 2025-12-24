# cython: language_level=3
# cython: wraparound=False
# cython: boundscheck=False

from __future__ import annotations

# Cython imports
import cython
from cython.cimports.libc import math  # type: ignore
from cython.cimports import numpy as np  # type: ignore
from cython.cimports.cpython import datetime  # type: ignore
from cython.cimports.cpython.time import localtime  # type: ignore
from cython.cimports.cpython.unicode import PyUnicode_CheckExact as is_str_exact  # type: ignore
from cython.cimports.cpython.unicode import PyUnicode_READ_CHAR as str_read  # type: ignore
from cython.cimports.cpython.unicode import PyUnicode_GET_LENGTH as str_len  # type: ignore
from cython.cimports.cpython.set import PySet_Add as set_add  # type: ignore
from cython.cimports.cpython.set import PySet_Size as set_len  # type: ignore
from cython.cimports.cpython.set import PySet_Discard as set_discard  # type: ignore
from cython.cimports.cpython.set import PySet_Contains as set_contains  # type: ignore
from cython.cimports.cpython.dict import PyDict_Size as dict_len  # type: ignore
from cython.cimports.cpython.dict import PyDict_SetItem as dict_setitem  # type: ignore
from cython.cimports.cpython.dict import PyDict_GetItem as dict_getitem  # type: ignore
from cython.cimports.cpython.dict import PyDict_DelItem as dict_delitem  # type: ignore
from cython.cimports.cpython.dict import PyDict_Contains as dict_contains  # type: ignore
from cython.cimports.cpython.list import PyList_GET_SIZE as list_len  # type: ignore
from cython.cimports.cpython.list import PyList_GET_ITEM as list_getitem  # type: ignore
from cython.cimports.cpython.list import PyList_SET_ITEM as list_setitem  # type: ignore
from cython.cimports.cytimes import errors, utils  # type: ignore

np.import_array()
np.import_umath()
datetime.import_datetime()

# Python imports
import datetime
from dateutil.parser._parser import parserinfo
from cytimes import errors, utils

__all__ = [
    "timelex",
    "Configs",
    "Parser",
    "parse",
    "parse_obj",
    "parse_month",
    "parse_weekday",
]


# Timelex -------------------------------------------------------------------------------------
@cython.ccall
def timelex(data: str) -> list[str]:
    """Tokenize a datetime-like string into lexical units (tokens).

    This lexer performs a single left-to-right pass over `data` and emits tokens
    based on `maximal runs` of letters or digits, while preserving separators
    as individual one-character tokens. It is optimized for datetime strings
    (ISO/RFC-like), and implements special handling for dots and decimal commas.

    :param data `<'str'>`: The datetime string to be tokenized.
    :returns `<'list[str]'>`: A list of tokens that are either:

        * Maximal runs of letters (Unicode-aware) or ASCII digits
        * Individual one-character separators (including spaces and punctuation),
        * A single normalized numeric token.
    """
    return _timelex(data, 0, 0)  # type: ignore


# Configs -------------------------------------------------------------------------------------
# . default configs
# fmt: off
_DEFAULT_PERTAIN: set[str] = {"of"}
_DEFAULT_JUMP: set[str] = {
    " ", ".", ",", ";", "-", "/", "'",
    "at", "on", "and", "ad", "m", "t", "of",
    "st", "nd", "rd", "th", "年" ,"月", "日"
}
_DEFAULT_UTC: set[str] = {"utc", "gmt", "z"}
_DEFAULT_TZ: dict[str, int] = {}
_DEFAULT_MONTH: dict[str, int] = {
    # EN(a)    # EN            # DE            # FR            # IT            # ES             # PT            # NL            # SE            #PL                 # TR          # CN         # Special
    "jan": 1,  "january": 1,   "januar": 1,    "janvier": 1,   "gennaio": 1,   "enero": 1,      "janeiro": 1,   "januari": 1,   "januari": 1,   "stycznia": 1,      "ocak": 1,    "一月": 1,
    "feb": 2,  "february": 2,  "februar": 2,   "février": 2,   "febbraio": 2,  "febrero": 2,    "fevereiro": 2, "februari": 2,  "februari": 2,  "lutego": 2,        "şubat": 2,   "二月": 2,    "febr": 2,
    "mar": 3,  "march": 3,     "märz": 3,      "mars": 3,      "marzo": 3,     "marzo": 3,      "março": 3,     "maart": 3,     "mars": 3,      "marca": 3,         "mart": 3,    "三月": 3,
    "apr": 4,  "april": 4,     "april": 4,     "avril": 4,     "aprile": 4,    "abril": 4,      "abril": 4,     "april": 4,     "april": 4,     "kwietnia": 4,      "nisan": 4,   "四月": 4,
    "may": 5,  "may": 5,       "mai": 5,       "mai": 5,       "maggio": 5,    "mayo": 5,       "maio": 5,      "mei": 5,       "maj": 5,       "maja": 5,          "mayıs": 5,   "五月": 5,
    "jun": 6,  "june": 6,      "juni": 6,      "juin": 6,      "giugno": 6,    "junio": 6,      "junho": 6,     "juni": 6,      "juni": 6,      "czerwca": 6,       "haziran": 5, "六月": 6,
    "jul": 7,  "july": 7,      "juli": 7,      "juillet": 7,   "luglio": 7,    "julio": 7,      "julho": 7,     "juli": 7,      "juli": 7,      "lipca": 7,         "temmuz": 7,  "七月": 7,
    "aug": 8,  "august": 8,    "august": 8,    "août": 8,      "agosto": 8,    "agosto": 8,     "agosto": 8,    "augustus": 8,  "augusti": 8,   "sierpnia": 8,      "ağustos": 8, "八月": 8,
    "sep": 9,  "september": 9, "september": 9, "septembre": 9, "settembre": 9, "septiembre": 9, "setembro": 9,  "september": 9, "september": 9, "września": 9,      "eylül": 9,   "九月": 9,    "sept": 9,
    "oct": 10, "october": 10,  "oktober": 10,  "octobre": 10,  "ottobre": 10,  "octubre": 10,   "outubro": 10,  "oktober": 10,  "oktober": 10,  "października": 10, "ekim": 10,   "十月": 10,
    "nov": 11, "november": 11, "november": 11, "novembre": 11, "novembre": 11, "noviembre": 11, "novembro": 11, "november": 11, "november": 11, "listopada": 11,    "kasım": 11,  "十一月": 11,
    "dec": 12, "december": 12, "dezember": 12, "décembre": 12, "dicembre": 12, "diciembre": 12, "dezembro": 12, "december": 12, "december": 12, "grudnia": 12,      "aralık": 12, "十二月": 12
}
_DEFAULT_WEEKDAY: dict[str, int] = {
    # EN(a)   # EN            # DE             # FR           # IT            # ES            # NL            # SE          # PL               # TR            # CN        # CN(a)
    "mon": 0, "monday": 0,    "montag": 0,     "lundi": 0,    "lunedì": 0,    "lunes": 0,     "maandag": 0,   "måndag": 0,  "poniedziałek": 0, "pazartesi": 0, "星期一": 0, "周一": 0,
    "tue": 1, "tuesday": 1,   "dienstag": 1,   "mardi": 1,    "martedì": 1,   "martes": 1,    "dinsdag": 1,   "tisdag": 1,  "wtorek": 1,       "salı": 1,      "星期二": 1, "周二": 1,
    "wed": 2, "wednesday": 2, "mittwoch": 2,   "mercredi": 2, "mercoledì": 2, "miércoles": 2, "woensdag": 2,  "onsdag": 2,  "środa": 2,        "çarşamba": 2,  "星期三": 2, "周三": 2,
    "thu": 3, "thursday": 3,  "donnerstag": 3, "jeudi": 3,    "giovedì": 3,   "jueves": 3,    "donderdag": 3, "torsdag": 3, "czwartek": 3,     "perşembe": 3,  "星期四": 3, "周四": 3,
    "fri": 4, "friday": 4,    "freitag": 4,    "vendredi": 4, "venerdì": 4,   "viernes": 4,   "vrijdag": 4,   "fredag": 4,  "piątek": 4,       "cuma": 4,      "星期五": 4, "周五": 4,
    "sat": 5, "saturday": 5,  "samstag": 5,    "samedi": 5,   "sabato": 5,    "sábado": 5,    "zaterdag": 5,  "lördag": 5,  "sobota": 5,       "cumartesi": 5, "星期六": 5, "周六": 5,
    "sun": 6, "sunday": 6,    "sonntag": 6,    "dimanche": 6, "domenica": 6,  "domingo": 6,   "zondag": 6,    "söndag": 6,  "niedziela": 6,    "pazar": 6,     "星期日": 6, "周日": 6
}
_DEFAULT_HMS: dict[str, int] = {
    # EN(a)   # EN          # DE           # FR           IT            # ES           # PT           # NL           # SE           # PL          # TR            # CN
    "h": 0,   "hour": 0,    "stunde": 0,   "heure": 0,    "ora": 0,     "hora": 0,     "hora": 0,     "uur": 0,      "timme": 0,    "godzina": 0, "saat": 0,      "时": 0,
    "hr": 0,  "hours": 0,   "stunden": 0,  "heures": 0,   "ore": 0,     "horas": 0,    "horas": 0,    "uren": 0,     "timmar": 0,   "godziny": 0, "saatler": 0,   "小时": 0,
    "m": 1,   "minute": 1,  "minute": 1,   "minute": 1,   "minuto": 1,  "minuto": 1,   "minuto": 1,   "minuut": 1,   "minut": 1,    "minuta": 1,  "dakika": 1,    "分": 1,
    "min": 1, "minutes": 1, "minuten": 1,  "minutes": 1,  "minuti": 1,  "minutos": 1,  "minutos": 1,  "minuten": 1,  "minuter": 1,  "minuty": 1,  "dakikalar": 1, "分钟": 1,
    "s": 2,   "second": 2,  "sekunde": 2,  "seconde": 2,  "secondo": 2, "segundo": 2,  "segundo": 2,  "seconde": 2,  "sekund": 2,   "sekunda": 2, "saniye": 2,    "秒": 2,
    "sec": 2, "seconds": 2, "sekunden": 2, "secondes": 2, "secondi": 2, "segundos": 2, "segundos": 2, "seconden": 2, "sekunder": 2, "sekundy": 2, "saniyeler": 2,
                                                                                                                                    "godzin": 0,                                           
}
_DEFAULT_AMPM: dict[str, int] = {
    # EN(a)  # EN(b)  #EN             # DE             # IT             # ES         # PT        # NL          # SE              # PL             # TR          # CN
    "a": 0,  "am": 0, "morning": 0,   "morgen": 0,     "mattina": 0,    "mañana": 0, "manhã": 0, "ochtend": 0, "morgon": 0,      "rano": 0,       "sabah": 0,   "上午": 0,
    "p": 1,  "pm": 1, "afternoon": 1, "nachmittag": 1, "pomeriggio": 1, "tarde": 1,  "tarde": 1, "middag": 1,  "eftermiddag": 1, "popołudnie": 1, "öğleden": 1, "下午": 1
}
# fmt: on


@cython.cclass
class Configs:
    """Configuration for the `<'Parser'>`.

    A `Configs` instance controls how tokens are recognized and how ambiguous
    year/month/day triples are interpreted. It maintains several token namespaces
    (e.g., month, weekday, AM/PM, timezone names) and enforces cross-namespace
    uniqueness rules so a token cannot silently change meaning.
    """

    # Settings
    _yearfirst: cython.bint
    _dayfirst: cython.bint
    # . jump
    _jump: set[str]
    _jump_ext: set[str]
    # . pertain
    _pertain: set[str]
    _pertain_ext: set[str]
    # . utc
    _utc: set[str]
    _utc_ext: set[str]
    # . tz
    _tz: dict[str, int]
    _tz_ext: dict[str, int]
    # . month
    _month: dict[str, int]
    _month_ext: dict[str, int]
    # . weekday
    _weekday: dict[str, int]
    _weekday_ext: dict[str, int]
    # . hms
    _hms: dict[str, int]
    _hms_ext: dict[str, int]
    # . ampm
    _ampm: dict[str, int]
    _ampm_ext: dict[str, int]
    # . internal
    __cls: object

    def __init__(
        self,
        yearfirst: cython.bint = True,
        dayfirst: cython.bint = False,
    ) -> None:
        """Configuration for `<'Parser'>`.

        A `Configs` instance controls how tokens are recognized and how ambiguous
        year/month/day triples are interpreted. It maintains several token namespaces
        (e.g., month, weekday, AM/PM, timezone names) and enforces cross-namespace
        uniqueness rules so a token cannot silently change meaning.

        :param yearfirst `<'bool'>`: Interpret the first ambiguous Y/M/D value as year. Defaults to `True`.
        :param dayfirst `<'bool'>`: Interpret the first ambiguous Y/M/D values as day. Defaults to `False`.

        Ambiguous Y/M/D
        ---------------
        Two booleans control ambiguous triplets (e.g. "01/05/09"):

        - `yearfirst` has precedence over `dayfirst` when both are True.
        - If all three positions are ambiguous, these apply:
            * yearfirst=False, dayfirst=False -> M/D/Y
            * yearfirst=False, dayfirst=True  -> D/M/Y
            * yearfirst=True,  dayfirst=False -> Y/M/D
            * yearfirst=True,  dayfirst=True  -> Y/D/M
        - If exactly one component is unambiguous (e.g. a number > 12), the parser
        should infer the order regardless of these flags.

        Namespaces
        ----------
        pertain : set[str]
            Tokenss like "of" that indicate a possessive/pertain relationship.
        jump : set[str]
            Low-priority stopwords that may safely be skipped (e.g. "and", "at", "on").
        utc : set[str]
            Tokens that explicitly denote UTC (e.g. "utc", "gmt", "z").
        tz : dict[str, int]
            Timezone aliases mapped to UTC offset in seconds (e.g. {"est": -18000}).
        month : dict[str, int]
            Month names/aliases to month number (1..12).
        weekday : dict[str, int]
            Weekday names/aliases to weekday number (0=Mon..6=Sun).
        hms : dict[str, int]
            Time unit flags: 0 = hour, 1 = minute, 2 = second.
        ampm : dict[str, int]
            AM/PM flags: 0 = AM, 1 = PM.

        Normalization & Validation
        --------------------------
        - All tokens are normalized to lowercase for conflict checking.
        - Then each token will generate three case variants for recognition:
            * lowercase
            * uppercase
            * titlecase
        - Integer values are range-checked:
            * tz offset:  -86,400 .. 86,400  (seconds)
            * month:       1 .. 12 (January .. December)
            * weekday:     0 .. 6  (Monday .. Sunday)
            * hms:         0 .. 2  (hour/minute/second)
            * ampm:        0 .. 1  (AM/PM)

        Conflict Policy
        ---------------
        - Overlap token is rejected unless explicitly allowed:
            * `jump` is lowest priority and may overlap with any namespace.
            * Re-adding a token to the same namespace is allowed.
        """
        self._yearfirst = yearfirst
        self._dayfirst = dayfirst
        #: The following order matters for conflict checking
        self.reset_settings()

    @classmethod
    def from_parserinfo(cls, info: parserinfo) -> Configs:
        """Build `Configs` from an existing `dateutil.parser.parserinfo` <'Configs'>`.

        :param info `<'dateutil.parser.parserinfo'>`: An existing parserinfo instance.
        :returns `<'Configs'>`: A Configs instance constructed from `info`,
            with equivalent settings.

        ## Example
        ```python
        from cytimes import Configs
        from dateutil.parser import parserinfo
        info = parserinfo()
        cfg = Configs.from_parserinfo(info)
        ```
        """
        if not isinstance(info, parserinfo):
            errors.raise_error(
                errors.InvalidParserInfo,
                cls,
                "from_parserinfo(info)",
                "Expects an instance of 'dateutil.parser.parserinfo', "
                "instead got %s." % (type(info)),
            )
        # Construct Configs
        cfg: Configs = cls(yearfirst=bool(info.yearfirst), dayfirst=bool(info.dayfirst))
        #: The following order matters for conflict checking
        cfg.clear_settings()
        if isinstance(info.JUMP, (list, tuple, set)):
            cfg.replace_jump(set(info.JUMP))
        if isinstance(info.PERTAIN, (list, tuple, set)):
            cfg.replace_pertain(set(info.PERTAIN))
        if isinstance(info.UTCZONE, (list, tuple, set)):
            cfg.replace_utc(set(info.UTCZONE))
        if isinstance(info.TZOFFSET, dict):
            cfg.replace_tz(dict(info.TZOFFSET))
        if isinstance(info.MONTHS, (list, tuple)):
            cfg.replace_month(
                {t: i + 1 for i, row in enumerate(info.MONTHS) for t in row}
            )
        if isinstance(info.WEEKDAYS, (list, tuple)):
            cfg.replace_weekday(
                {t: i for i, row in enumerate(info.WEEKDAYS) for t in row}
            )
        if isinstance(info.HMS, (list, tuple)):
            cfg.replace_hms({t: i for i, row in enumerate(info.HMS) for t in row})
        if isinstance(info.AMPM, (list, tuple)):
            cfg.replace_ampm({t: i for i, row in enumerate(info.AMPM) for t in row})
        return cfg

    # Y/M/D -----------------------------------------------------------
    @property
    def yearfirst(self) -> bool:
        """Whether to interpret ambiguous Y/M/D with the first position as `year` `<'bool'>`.

        ## Notice
        - `yearfirst` has higher priority than `dayfirst` when both are set to `True`.
        """
        return self._yearfirst

    @property
    def dayfirst(self) -> bool:
        """Whether to interpret ambiguous Y/M/D with the first position as `day` `<'bool'>`.

        ## Notice
        - `yearfirst` has higher priority than `dayfirst` when both are set to `True`.
        """
        return self._dayfirst

    @cython.ccall
    def order_hint(self) -> str:
        """Give a hint of the ambiguous Y/M/D order based
        on `yearfirst` and `dayfirst` settings `<'str'>`.
        """
        if self._yearfirst and self._dayfirst:
            return "Y/D/M"
        elif self._yearfirst and not self._dayfirst:
            return "Y/M/D"
        elif not self._yearfirst and self._dayfirst:
            return "D/M/Y"
        else:
            return "M/D/Y"

    # Jump ------------------------------------------------------------
    @property
    def jump(self) -> set[str]:
        """Set of tokens that should be skipped `<'set[str]'>`."""
        return set(self._jump)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_jump(self, token: str) -> cython.bint:
        """Add token that should be skipped `<'bool'>`.

        :param token `<'str'>`: The `jump` token to added (case-insensitive).
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If `token` is invalid or conflicts with other namespaces.

        ## Example
        >>> cfg.add_jump("at")
        """
        # Validate token
        token = self._validate_token("jump", token)
        # Add to base namespace
        set_add(self._jump, token)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            set_add(self._jump_ext, tok)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_jump(self, token: str) -> cython.bint:
        """Remove `jump` token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `jump` token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_jump("at")
        """
        # Lowercase token
        token = self._lowercase_token("jump", token)
        # Remove from base namespace
        removed = set_discard(self._jump, token)
        # Remove from extend namespace
        if removed:
            for tok in self._gen_token_case_variants(token):
                set_discard(self._jump_ext, tok)
        return removed

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_jump(self, tokens: set[str] = None) -> cython.bint:
        """Replace the set of `jump` tokens `<'bool'>`.

        :param tokens `<'set[str]/None'>`: The new set of `jump` tokens. Defaults to `None`.
            If `None`, resets to the default `jump` set.
        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `token` is invalid or conflicts with other namespaces.

        ## Example
        >>> cfg.replace_jump({"at", "on", ...})
        """
        # Reset to default
        if tokens is None:
            tokens = _DEFAULT_JUMP

        # Cache tokens
        old: set = self._jump
        old_ext: set = self._jump_ext

        # Add tokens
        self._jump = set()
        self._jump_ext = set()
        try:
            for t in tokens:
                self.add_jump(self._ensure_str_token("jump", t))
        except Exception:
            # Rollback
            self._jump = old
            self._jump_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_jump(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `jump` `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return set_contains(self._jump_ext, token)

    # Pertain ---------------------------------------------------------
    @property
    def pertain(self) -> set[str]:
        """Set of tokens to recognize as `pertain` `<'set[str]'>`."""
        return set(self._pertain)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_pertain(self, token: str) -> cython.bint:
        """Add token that should be recognized as `pertain` `<'bool'>`.

        :param token `<'str'>`: The `pertain` token to added (case-insensitive).
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If `token` is invalid or conflicts with other namespaces.

        ## Example
        >>> cfg.add_pertain("of")
        """
        # Validate token
        token = self._validate_token("pertain", token)
        # Add to base namespace
        set_add(self._pertain, token)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            set_add(self._pertain_ext, tok)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_pertain(self, token: str) -> cython.bint:
        """Remove `pertain` token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `pertain` token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_pertain("of")
        """
        # Lowercase token
        token = self._lowercase_token("pertain", token)
        # Remove from base namespace
        removed = set_discard(self._pertain, token)
        # Remove from extend namespace
        if removed:
            for tok in self._gen_token_case_variants(token):
                set_discard(self._pertain_ext, tok)
        return removed

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_pertain(self, tokens: set[str] = None) -> cython.bint:
        """Replace the set of `pertain` tokens `<'bool'>`.

        :param tokens `<'set[str]/None'>`: The new set of `pertain` tokens. Defaults to `None`.
            If `None`, resets to the default `pertain` set.
        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `token` is invalid or conflicts with other namespaces.

        ## Example
        >>> cfg.replace_pertain({"of", "for", ...})
        """
        # Reset to default
        if tokens is None:
            tokens = _DEFAULT_PERTAIN

        # Cache tokens
        old: set = self._pertain
        old_ext: set = self._pertain_ext

        # Add tokens
        self._pertain = set()
        self._pertain_ext = set()
        try:
            for t in tokens:
                self.add_pertain(self._ensure_str_token("pertain", t))
        except Exception:
            # Rollback
            self._pertain = old
            self._pertain_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_pertain(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `pertain` `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return set_contains(self._pertain_ext, token)

    # UTC -------------------------------------------------------------
    @property
    def utc(self) -> set[str]:
        """Set of tokens to recognize as `UTC` timezone `<'set[str]'>`."""
        return set(self._utc)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_utc(self, token: str) -> cython.bint:
        """Add token that should be recognized as UTC timezone `<'bool'>`.

        :param token `<'str'>`: The `UTC` timezone token to added (case-insensitive).
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If `token` is invalid or conflicts with other namespaces.

        ## Example
        >>> cfg.add_utc("gmt")
        """
        # Validate token
        token = self._validate_token("utc", token)
        # Add to base namespace
        set_add(self._utc, token)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            set_add(self._utc_ext, tok)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_utc(self, token: str) -> cython.bint:
        """Remove `UTC` timezone token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `UTC` timezone token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_utc("gmt")
        """
        # Lowercase token
        token = self._lowercase_token("utc", token)
        # Remove from base namespace
        removed = set_discard(self._utc, token)
        # Remove from extend namespace
        if removed:
            for tok in self._gen_token_case_variants(token):
                set_discard(self._utc_ext, tok)
        return removed

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_utc(self, tokens: set[str] = None) -> cython.bint:
        """Replace the set of `UTC` timezone tokens `<'bool'>`.

        :param tokens `<'set[str]/None'>`: The new set of `UTC` timezone tokens. Defaults to `None`.
            If `None`, resets to the default `UTC` timezone set.
        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `token` is invalid or conflicts with other namespaces.

        ## Example
        >>> cfg.replace_utc({"utc", "gmt", ...})
        """
        # Reset to default
        if tokens is None:
            tokens = _DEFAULT_UTC

        # Cache tokens
        old: set = self._utc
        old_ext: set = self._utc_ext

        # Add tokens
        self._utc = set()
        self._utc_ext = set()
        try:
            for t in tokens:
                self.add_utc(self._ensure_str_token("utc", t))
        except Exception:
            # Rollback
            self._utc = old
            self._utc_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_utc(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `UTC` timezone `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return set_contains(self._utc_ext, token)

    # Timezone --------------------------------------------------------
    @property
    def tz(self) -> dict[str, int]:
        """Map of tokens to recognize as a `timezone` `<'dict[str, int]'>`

        - Keys are timezone names and values are UTC offsets in seconds.
        """
        return dict(self._tz)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_tz(
        self,
        token: str,
        hours: cython.int = 0,
        minutes: cython.int = 0,
        seconds: cython.int = 0,
    ) -> cython.bint:
        """Add token that should be recognized as `timezone`
        with the corresponding UTC offset.

        :param token `<'str'>`: The `timezone` token to add (case-insensitive).
        :param hours `<'int'>`: UTC offset in hours. Defaults to `0`.
        :param minutes `<'int'>`: UTC offset in minutes. Defaults to `0`.
        :param seconds `<'int'>`: UTC offset in seconds. Defaults to `0`.
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If token conflicts with other namespaces,
            or the UTC offset (hours & minutes & seconds) is invalid.

        ## UTC Offset
        - offset = hours * 3600 + minutes * 60 + seconds

        ## Example
        >>> cfg.add_tz("est", hours=-5)
        """
        # Validate token
        token = self._validate_token("tz", token)
        # Validate value
        value: object = self._validate_value(
            "tz", hours * 3_600 + minutes * 60 + seconds, -86_400, 86_400
        )
        # Add to base namespace
        dict_setitem(self._tz, token, value)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            dict_setitem(self._tz_ext, tok, value)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_tz(self, token: str) -> cython.bint:
        """Remove `timezone` token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `timezone` token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_tz("est")
        """
        # Lowercase token
        token = self._lowercase_token("tz", token)
        # Remove from base namespace
        try:
            dict_delitem(self._tz, token)
        except KeyError:
            return False
        # Remove from extend namespace
        for tok in self._gen_token_case_variants(token):
            try:
                dict_delitem(self._tz_ext, tok)
            except KeyError:
                pass
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_tz(self, mapping: dict[str, int] = None) -> cython.bint:
        """Replace the `timezone` mapping `<'bool'>`.

        :param mapping `<'dict[str,int]/None'>`: The new mapping of `timezone` tokens. Defaults to `None`.

            - Accepts dictionary where keys are `timezone` tokens
              and values are UTC offsets in seconds.
            - If `None`, resets to the default `timezone` mapping.

        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `timezone` token conflicts with
            other namespaces or the UTC offset value is invalid.

        ## Example
        >>> cfg.replace_tz({"est": -18000, "edt": -14400, ... })
        """
        # Reset to default
        if mapping is None:
            mapping = _DEFAULT_TZ

        # Cache mappings
        old: dict = self._tz
        old_ext: dict = self._tz_ext

        # Set tokens & values
        self._tz = dict()
        self._tz_ext = dict()
        try:
            for t, v in mapping.items():
                self.add_tz(
                    self._ensure_str_token("tz", t),
                    0,
                    0,
                    self._ensure_int_value("tz", v),
                )
        except Exception:
            # Rollback
            self._tz = old
            self._tz_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_tz(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `timezone` `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return dict_contains(self._tz_ext, token)

    @cython.ccall
    @cython.exceptval(-200_000, check=False)
    def get_tz_offset(self, token: str) -> cython.int:
        """Get the corresponding UTC offset if `token`
        can be recognized as `timezone` `<'int'>`

        :param token `<'str'>`: Candidate for `timezone` token.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'int'>`: UTC offset in seconds, or `-100_000` if the `token`
            is not recognizible (-100_000 is the sentinel value for None).
        """
        if token is None:
            return utils.NULL_TZOFFSET
        value = dict_getitem(self._tz_ext, token)
        if value == cython.NULL:
            return utils.NULL_TZOFFSET
        return cython.cast(object, value)

    # Month -----------------------------------------------------------
    @property
    def month(self) -> dict[str, int]:
        """Map of tokens to recognize as `month` `<'dict[str, int]'>`.

        - Keys are month names and values are month numbers: 1(Jan)...12(Dec).
        """
        return dict(self._month)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_month(self, token: str, month: cython.int) -> cython.bint:
        """Add token that should be recognized as `month`
        with the corresponding month number.

        :param token `<'str'>`: The `month` token to add (case-insensitive).
        :param month `<'int'>`: The month number (1=Jan...12=Dec).
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If token conflicts with other namespaces,
            or the month number is invalid.

        ## Month Number
        - month: 1=Jan...12=Dec

        ## Example
        >>> cfg.add_month("jan", 1)
        """
        # Validate token
        token = self._validate_token("month", token)
        # Validate value
        value: object = self._validate_value("month", month, 1, 12)
        # Add to base namespace
        dict_setitem(self._month, token, value)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            dict_setitem(self._month_ext, tok, value)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_month(self, token: str) -> cython.bint:
        """Remove `month` token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `month` token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_month("jan")
        """
        # Lowercase token
        token = self._lowercase_token("month", token)
        # Remove from base namespace
        try:
            dict_delitem(self._month, token)
        except KeyError:
            return False
        # Remove from extend namespace
        for tok in self._gen_token_case_variants(token):
            try:
                dict_delitem(self._month_ext, tok)
            except KeyError:
                pass
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_month(self, mapping: dict[str, int] = None) -> cython.bint:
        """Replace the `month` mapping `<'bool'>`.

        :param mapping `<'dict[str,int]/None'>`: The new mapping of `month` tokens. Defaults to `None`.

            - Accepts dictionary where keys are `month` tokens
              and values are month numbers (1=Jan...12=Dec).
            - If `None`, resets to the default `month` mapping.

        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `month` token conflicts with
            other namespaces or the month number is invalid.

        ## Example
        >>> cfg.replace_month({"jan": 1, "feb": 2, ... })
        """
        # Reset to default
        if mapping is None:
            mapping = _DEFAULT_MONTH

        # Cache mappings
        old: dict = self._month
        old_ext: dict = self._month_ext

        # Set tokens & values
        self._month = dict()
        self._month_ext = dict()
        try:
            for t, v in mapping.items():
                self.add_month(
                    self._ensure_str_token("month", t),
                    self._ensure_int_value("month", v),
                )
        except Exception:
            # Rollback
            self._month = old
            self._month_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_month(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `month` `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return dict_contains(self._month_ext, token)

    @cython.ccall
    @cython.exceptval(-2, check=False)
    def get_month(self, token: str) -> cython.int:
        """Get the corresponding month number if `token`
        can be recognized as `month` `<'int'>`

        :param token `<'str'>`: Candidate for `month` token.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'int'>`: Month number (1=Jan...12=Dec), or `-1` if the
            token is not recognizable (-1 is the sentinel value for None).
        """
        if token is None:
            return -1
        value = dict_getitem(self._month_ext, token)
        if value == cython.NULL:
            return -1
        return cython.cast(object, value)

    # Weekday ---------------------------------------------------------
    @property
    def weekday(self) -> dict[str, int]:
        """Map of tokens to recognize as `weekday` `<'dict[str, int]'>`.

        - Keys are weekday names and values are weekday numbers: 0=Mon...6=Sun.
        """
        return dict(self._weekday)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_weekday(self, token: str, weekday: cython.int) -> cython.bint:
        """Add token that should be recognized as `weekday`
        with the corresponding weekday number.

        :param token `<'str'>`: The `weekday` token to add (case-insensitive).
        :param weekday `<'int'>`: The weekday number (0=Mon...6=Sun).
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If token conflicts with other namespaces,
            or the weekday number is invalid.

        ## Weekday Number
        - weekday: 0=Mon...6=Sun

        ## Example
        >>> cfg.add_weekday("mon", 0)
        """
        # Validate token
        token = self._validate_token("weekday", token)
        # Validate value
        value: object = self._validate_value("weekday", weekday, 0, 6)
        # Add to base namespace
        dict_setitem(self._weekday, token, value)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            dict_setitem(self._weekday_ext, tok, value)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_weekday(self, token: str) -> cython.bint:
        """Remove `weekday` token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `weekday` token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_weekday("mon")
        """
        # Lowercase token
        token = self._lowercase_token("weekday", token)
        # Remove from base namespace
        try:
            dict_delitem(self._weekday, token)
        except KeyError:
            return False
        # Remove from extend namespace
        for tok in self._gen_token_case_variants(token):
            try:
                dict_delitem(self._weekday_ext, tok)
            except KeyError:
                pass
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_weekday(self, mapping: dict[str, int] = None) -> cython.bint:
        """Replace the `weekday` mapping `<'bool'>`.

        :param mapping `<'dict[str,int]/None'>`: The new mapping of `weekday` tokens. Defaults to `None`.

            - Accepts dictionary where keys are `weekday` tokens
              and values are weekday numbers (0=Mon...6=Sun).
            - If `None`, resets to the default `weekday` mapping.

        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `weekday` token conflicts with
            other namespaces or the weekday number is invalid.

        ## Example
        >>> cfg.replace_weekday({"mon": 0, "tue": 1, ... })
        """
        # Reset to default
        if mapping is None:
            mapping = _DEFAULT_WEEKDAY

        # Cache mappings
        old: dict = self._weekday
        old_ext: dict = self._weekday_ext

        # Set tokens & values
        self._weekday = dict()
        self._weekday_ext = dict()
        try:
            for t, v in mapping.items():
                self.add_weekday(
                    self._ensure_str_token("weekday", t),
                    self._ensure_int_value("weekday", v),
                )
        except Exception:
            # Rollback
            self._weekday = old
            self._weekday_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_weekday(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `weekday` `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return dict_contains(self._weekday_ext, token)

    @cython.ccall
    @cython.exceptval(-2, check=False)
    def get_weekday(self, token: str) -> cython.int:
        """Get the corresponding weekday number if `token`
        can be recognized as `weekday` `<'int'>`

        :param token `<'str'>`: Candidate for `weekday` token.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'int'>`: Weekday number (0=Mon...6=Sun), or `-1` if the
            token is not recognizable (-1 is the sentinel value for None).
        """
        if token is None:
            return -1
        value = dict_getitem(self._weekday_ext, token)
        if value == cython.NULL:
            return -1
        return cython.cast(object, value)

    # HMS ------------------------------------------------------------
    @property
    def hms(self) -> dict[str, int]:
        """Map of tokens to recognize as H/M/S flag `<'dict[str, int]'>`.

        - Keys are H/M/S tokens and values are the corresponding
        flag numbers: 0=hour; 1=minute; 2=second.
        """
        return dict(self._hms)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_hms(self, token: str, flag: cython.int) -> cython.bint:
        """Add token that should be recognized as `H/M/S` flag
        with the corresponding flag number.

        :param token `<'str'>`: The `H/M/S` token to add (case-insensitive).
        :param month `<'int'>`: The H/M/S flag number (0=hour; 1=minute; 2=second).
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If token conflicts with other namespaces,
            or the H/M/S flag number is invalid.

        ## H/M/S Flag Number
        - flag: 0=hour; 1=minute; 2=second

        ## Example
        >>> cfg.add_hms("hour", 0)
        """
        # Validate token
        token = self._validate_token("hms", token)
        # Validate value
        value: object = self._validate_value("hms", flag, 0, 2)
        # Add to base namespace
        dict_setitem(self._hms, token, value)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            dict_setitem(self._hms_ext, tok, value)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_hms(self, token: str) -> cython.bint:
        """Remove `H/M/S` token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `H/M/S` token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_hms("hour")
        """
        # Lowercase token
        token = self._lowercase_token("hms", token)
        # Remove from base namespace
        try:
            dict_delitem(self._hms, token)
        except KeyError:
            return False
        # Remove from extend namespace
        for tok in self._gen_token_case_variants(token):
            try:
                dict_delitem(self._hms_ext, tok)
            except KeyError:
                pass
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_hms(self, mapping: dict[str, int] = None) -> cython.bint:
        """Replace the `H/M/S` mapping `<'bool'>`.

        :param mapping `<'dict[str,int]/None'>`: The new mapping of `H/M/S` tokens. Defaults to `None`.

            - Accepts dictionary where keys are `H/M/S` tokens
              and values are H/M/S flag numbers (0=hour; 1=minute; 2=second).
            - If `None`, resets to the default `H/M/S` mapping.

        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `H/M/S` token conflicts with
            other namespaces or the H/M/S flag number is invalid.

        ## Example
        >>> cfg.replace_hms({"hour": 0, "minute": 1, "second": 2, ...})
        """
        # Reset to default
        if mapping is None:
            mapping = _DEFAULT_HMS

        # Cache mappings
        old: dict = self._hms
        old_ext: dict = self._hms_ext

        # Set tokens & values
        self._hms = dict()
        self._hms_ext = dict()
        try:
            for t, v in mapping.items():
                self.add_hms(
                    self._ensure_str_token("hms", t),
                    self._ensure_int_value("hms", v),
                )
        except Exception:
            # Rollback
            self._hms = old
            self._hms_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_hms(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `H/M/S` flag `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return dict_contains(self._hms_ext, token)

    @cython.ccall
    @cython.exceptval(-2, check=False)
    def get_hms(self, token: str) -> cython.int:
        """Get the corresponding H/M/S flag number if `token`
        can be recognized as `H/M/S` `<'int'>`

        :param token `<'str'>`: Candidate for `H/M/S` token.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'int'>`: H/M/S flag number (0=hour; 1=minute; 2=second), or `-1` if the
            token is not recognizable (-1 is the sentinel value for None).
        """
        if token is None:
            return -1
        value = dict_getitem(self._hms_ext, token)
        if value == cython.NULL:
            return -1
        return cython.cast(object, value)

    # AM/PM ----------------------------------------------------------
    @property
    def ampm(self) -> dict[str, int]:
        """Map of tokens to recognize as AM/PM flag `<'dict[str, int]'>`.

        - Keys are the AM/PM tokens and values are the corresponding
          flag numbers: 0=AM; 1=PM.
        """
        return dict(self._ampm)

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def add_ampm(self, token: str, flag: cython.int) -> cython.bint:
        """Add token that should be recognized as `AM/PM` flag
        with the corresponding flag number.

        :param token `<'str'>`: The `AM/PM` token to add (case-insensitive).
        :param month `<'int'>`: The AM/PM flag number (0=AM; 1=PM).
        :returns `<'bool'>`: True if added successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If token conflicts with other namespaces,
            or the AM/PM flag number is invalid.

        ## AM/PM Flag Number
        - flag: 0=AM; 1=PM

        ## Example
        >>> cfg.add_ampm("am", 0)
        """
        # Validate token
        token = self._validate_token("ampm", token)
        # Validate value
        value: object = self._validate_value("ampm", flag, 0, 1)
        # Add to base namespace
        dict_setitem(self._ampm, token, value)
        # Add to extend namespace
        for tok in self._gen_token_case_variants(token):
            dict_setitem(self._ampm_ext, tok, value)
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def remove_ampm(self, token: str) -> cython.bint:
        """Remove `AM/PM` token from the configuration `<'bool'>`.

        :param token `<'str'>`: The `AM/PM` token to remove (case-insensitive).
        :returns `<'bool'>`: True if removed successfully, otherwise False (not exists).
        :raises `<'InvalidConfigsValue'>`: If the `token` is invalid.

        ##  Example
        >>> cfg.remove_ampm("am")
        """
        # Lowercase token
        token = self._lowercase_token("ampm", token)
        # Remove from base namespace
        try:
            dict_delitem(self._ampm, token)
        except KeyError:
            return False
        # Remove from extend namespace
        for tok in self._gen_token_case_variants(token):
            try:
                dict_delitem(self._ampm_ext, tok)
            except KeyError:
                pass
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def replace_ampm(self, mapping: dict[str, int] = None) -> cython.bint:
        """Replace the `AM/PM` mapping `<'bool'>`.

        :param mapping `<'dict[str,int]/None'>`: The new mapping of `AM/PM` tokens. Defaults to `None`.

            - Accepts dictionary where keys are `AM/PM` tokens
              and values are AM/PM flag numbers (0=AM; 1=PM).
            - If `None`, resets to the default `AM/PM` mapping.

        :returns `<'bool'>`: True if replaced successfully, otherwise False.
        :raises `<'InvalidConfigsValue'>`: If any `AM/PM` token conflicts with
            other namespaces or the AM/PM flag number is invalid.

        ## Example
        >>> cfg.replace_ampm({"am": 0, "pm": 1, ... })
        """
        # Reset to default
        if mapping is None:
            mapping = _DEFAULT_AMPM

        # Cache mappings
        old: dict = self._ampm
        old_ext: dict = self._ampm_ext

        # Set tokens & values
        self._ampm = dict()
        self._ampm_ext = dict()
        try:
            for t, v in mapping.items():
                self.add_ampm(
                    self._ensure_str_token("ampm", t),
                    self._ensure_int_value("ampm", v),
                )
        except Exception:
            # Rollback
            self._ampm = old
            self._ampm_ext = old_ext
            raise
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def is_ampm(self, token: str) -> cython.bint:
        """Check if the `token` can be recognized as `AM/PM` flag `<'bool'>`.

        :param token `<'str'>`: The token to check against.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'bool'>`: True if the token can be recognized, otherwise False.
        """
        if token is None:
            return False
        return dict_contains(self._ampm_ext, token)

    @cython.ccall
    @cython.exceptval(-2, check=False)
    def get_ampm(self, token: str) -> cython.int:
        """Get the corresponding AM/PM flag number if `token`
        can be recognized as `AM/PM` `<'int'>`

        :param token `<'str'>`: Candidate for `AM/PM` token.
            Only recognize in `lowercase`, `uppercase` and `titlecase`.
        :return `<'int'>`: AM/PM flag number (0=AM; 1=PM), or `-1` if the
            token is not recognizable (-1 is the sentinel value for None).
        """
        if token is None:
            return -1
        value = dict_getitem(self._ampm_ext, token)
        if value == cython.NULL:
            return -1
        return cython.cast(object, value)

    # Clear & Reset ------------------------------------------------
    @cython.ccall
    @cython.exceptval(-1, check=False)
    def clear_settings(self) -> cython.bint:
        """Clear all token settings.

        - Remove all tokens in namespaces:
            `jump`, `pertain`, `utc`.
        - Remove all tokens and corresponding values in namespaces:
            `tz`, `month`, `weekday`, `hms`, `ampm`.
        """
        # . jump
        self._jump = set()
        self._jump_ext = set()
        # . pertain
        self._pertain = set()
        self._pertain_ext = set()
        # . utc
        self._utc = set()
        self._utc_ext = set()
        # . tz
        self._tz = dict()
        self._tz_ext = dict()
        # . month
        self._month = dict()
        self._month_ext = dict()
        # . weekday
        self._weekday = dict()
        self._weekday_ext = dict()
        # . hms
        self._hms = dict()
        self._hms_ext = dict()
        # . ampm
        self._ampm = dict()
        self._ampm_ext = dict()
        return True

    @cython.ccall
    @cython.exceptval(-1, check=False)
    def reset_settings(self) -> cython.bint:
        """Reset all token settings to `default`.

        - Reset all tokens to default in namespaces:
            `jump`, `pertain`, `utc`.
        - Reset all tokens and corresponding values to default in namespaces:
            `tz`, `month`, `weekday`, `hms`, `ampm`.
        """
        self.clear_settings()
        self.replace_jump(None)
        self.replace_pertain(None)
        self.replace_utc(None)
        self.replace_tz(None)
        self.replace_month(None)
        self.replace_weekday(None)
        self.replace_hms(None)
        self.replace_ampm(None)
        return True

    # Internal --------------------------------------------------------
    # . token
    @cython.cfunc
    @cython.inline(True)
    def _ensure_str_token(self, namespace: str, token: object) -> str:
        """(internal) Ensure the `token` is a literal string `<'str'>`.

        :param namespace `<'str'>`: The destination namespace of the token:
            'jump', 'pertain', 'utc', 'tz', 'month', 'weekday', 'hms', 'ampm'.
        :param token `<'object'>`: The token to ensure is literal string.
        :returns `<'str'>`: The validated string value.
        :raises `<'InvalidConfigsValue'>`: If the token is not a string.
        """
        if not isinstance(token, str):
            errors.raise_configs_token_error(
                self._cls(),
                "Token for 'Configs.%s' must be a string, instead got %s."
                % (namespace, type(token)),
            )
        return token

    @cython.cfunc
    @cython.inline(True)
    def _validate_token(self, namespace: str, token: str) -> str:
        """(internal) Validate and normalize a token for a given namespace `<'str'>`.

        :param namespace `<'str'>`: The destination namespace of the token:
            'jump', 'pertain', 'utc', 'tz', 'month', 'weekday', 'hms', 'ampm'.
        :param token `<'str'>`: The user-provided token to register.
        :returns `<'str'>`: The validated and normalized (lowercased) token.
        :raises `<'InvalidConfigsValue'>`: If the token is invalid or conflicts per the policy.

        ## Conflict Policy
        - Namespace `jump` has the lowest priority and can overlap with any other namespace.
        - Other cross-namespace overlaps are rejected.
        """
        # Validate token
        if token is None:
            errors.raise_configs_token_error(
                self._cls(),
                "Token for 'Configs.%s' must be a string, instead got None."
                % namespace,
            )
        token: str = self._lowercase_token(namespace, token)

        # Cross-namespace check
        # . jump: lowest priority → accept overlap
        if namespace == "jump":
            return token
        overlap: str = None
        # . pertain
        if set_contains(self._pertain, token):
            if namespace != "pertain":
                overlap = "pertain"
        # . utc
        elif set_contains(self._utc, token):
            if namespace != "utc":
                overlap = "utc"
        # . tz
        elif dict_contains(self._tz, token):
            if namespace != "tz":
                overlap = "tz"
        # . month
        elif dict_contains(self._month, token):
            if namespace != "month":
                overlap = "month"
        # . weekday
        elif dict_contains(self._weekday, token):
            if namespace != "weekday":
                overlap = "weekday"
        # . hms flag
        elif dict_contains(self._hms, token):
            if namespace != "hms":
                overlap = "hms"
        # . ampm flag
        elif dict_contains(self._ampm, token):
            if namespace != "ampm":
                overlap = "ampm"

        # Raise error
        if overlap:
            errors.raise_configs_token_error(
                self._cls(),
                "Token '%s' for 'Configs.%s' conflicts with existing tokens in 'Configs.%s'."
                % (token, namespace, overlap),
            )

        # Return the token in lowercase
        return token

    @cython.cfunc
    @cython.inline(True)
    def _lowercase_token(self, namespace: str, token: str) -> str:
        """(internal) Normalize a token to lowercase `<'str'>`.

        :param namespace `<'str'>`: The destination namespace of the token:
            'jump', 'pertain', 'utc', 'tz', 'month', 'weekday', 'hms', 'ampm'.
        :param token `<'str'>`: The input token.
        :returns `<'str'>`: The lowercase variant of the token.
        """
        if token is None:
            errors.raise_configs_token_error(
                self._cls(),
                "Token for 'Configs.%s' must be a string, instead got None."
                % namespace,
            )
        if str_len(token) == 0:
            errors.raise_configs_token_error(
                self._cls(),
                "Token for 'Configs.%s' cannot be an empty string." % namespace,
            )
        return token.lower()

    @cython.cfunc
    @cython.inline(True)
    def _gen_token_case_variants(self, token: str) -> tuple[str, str, str]:
        """(internal) Generate case variants of a token `<'tuple'>`.

        :param token `<'str'>`: The input token.
        :returns `<'tuple[str, str, str]'>`: A tuple containing
            the lowercase, uppercase, and titlecase variants of the token.
        """
        if token is None:
            errors.raise_configs_token_error(
                self._cls(), "Namespace `token` cannot be None."
            )
        return (token.lower(), token.upper(), token.title())

    # . value
    @cython.cfunc
    @cython.inline(True)
    def _ensure_int_value(self, namespace: str, value: object) -> cython.int:
        """(internal) Ensure the `value` is an integer `<'int'>`.

        :param namespace `<'str'>`: The destination namespace of the value:
            'jump', 'pertain', 'utc', 'tz', 'month', 'weekday', 'hms', 'ampm'.
        :param value `<'object'>`: The value to ensure is an integer.
        :returns `<'int'>`: The validated integer value.
        :raises `<'InvalidConfigsValue'>`: If the value is not an integer.
        """
        if not isinstance(value, int):
            errors.raise_configs_value_error(
                self._cls(),
                "Value for 'Configs.%s' must be an integer, instead got %s."
                % (namespace, type(value)),
            )
        return value

    @cython.cfunc
    @cython.inline(True)
    def _validate_value(
        self,
        namespace: str,
        value: cython.int,
        minimum: cython.int,
        maximum: cython.int,
    ) -> cython.int:
        """(internal) Validate an integer value for a given namespace `<'int'>`.

        :param namespace `<'str'>`: The destination namespace of the value:
            'jump', 'pertain', 'utc', 'tz', 'month', 'weekday', 'hms', 'ampm'.
        :param value `<'int'>`: The user-provided value to register.
        :param minimum `<'int'>`: The minimum allowed value (inclusive).
        :param maximum `<'int'>`: The maximum allowed value (inclusive).
        :returns `<'int'>`: The validated integer value.
        :raises `<'InvalidConfigsValue'>`: If the value is out of range.
        """
        if not minimum <= value <= maximum:
            errors.raise_configs_value_error(
                self._cls(),
                "Value for 'Configs.%s' must be an integer between %d..%d, instead got %d."
                % (namespace, minimum, maximum, value),
            )
        return value

    # . class
    @cython.cfunc
    @cython.inline(True)
    def _cls(self) -> object:
        """(internal) Access the class object of the current instance `<'type[Configs]'>`."""
        if self.__cls is None:
            self.__cls = self.__class__
        return self.__cls

    # Special methods -------------------------------------------------
    def __repr__(self) -> str:
        return (
            "<'%s' (%s: yearfirst=%s dayfirst=%s | "
            "sizes: jump=%d pertain=%d utc=%d tz=%d month=%d weekday=%d hms=%d ampm=%d)>"
            % (
                self._cls().__name__,
                self.order_hint(),
                self._yearfirst,
                self._dayfirst,
                set_len(self._jump),
                set_len(self._pertain),
                set_len(self._utc),
                dict_len(self._tz),
                dict_len(self._month),
                dict_len(self._weekday),
                dict_len(self._hms),
                dict_len(self._ampm),
            )
        )


_DEFAULT_CONFIGS: Configs = Configs()


# Parser --------------------------------------------------------------------------------------
@cython.cclass
class Result:
    """Parsed datetime result container for the Parser.

    This class stores raw date tokens as they are encountered (up to three
    positional Y/M/D `values`) and, separately, which positions are known to be
    year/month/day (`role indices`). It then resolves ambiguities to concrete
    `year`, `month`, and `day`, and also carries time/weekday/tzoffset
    information when available.

    ## Sentinels
    - Unset date/time component: `-1`
    - Unset tzoffset: `-100_000`

    ## Notice
    This class is designed to be used internally by the Parser
    only, and all attributes/methods are only available in Cython
    (`NOT` exposed to Python).
    """

    # Y/M/D
    _ymd: cython.int[3]
    _idx: cython.int
    _yidx: cython.int
    _midx: cython.int
    _didx: cython.int
    _resolved: cython.bint
    # Values
    year: cython.int
    month: cython.int
    day: cython.int
    hour: cython.int
    minute: cython.int
    second: cython.int
    microsecond: cython.int
    weekday: cython.int
    doy: cython.int
    ampm: cython.int
    tzoffset: cython.int
    tzoffset_finalized: cython.bint
    century_specified: cython.bint

    def __cinit__(self) -> None:
        """The datetime result from the Parser."""
        self._reset()

    # Y/M/D -----------------------------------------------------------
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def set_ymd_int(self, flag: cython.int, value: cython.longlong) -> cython.bint:
        """(cfunc) Set one Y/M/D candidate value from an integer `<'bool'>`.

        :param flag `<'int'>`: The Y/M/D flag (0=UNKNOWN, 1=YEAR, 2=MONTH, 3=DAY).
        :param value `<'int'>`: An integer value, candidate for Y/M/D.
        :returns `<'bool'>`: True if value is recorded.
            False if the corresponding field is set or all slots were full.
        :raises `<'ValueError'>`: If the value is out of range or violates the basic domain of a labeled token.

        ## Rules
        - The `value` must be in 0..9999, else raise error.
        - When flag is `0` (UNKNOWN):
            * `value > 31` ⇒ treat as year (century is specified if `value > 99`).
            * `value == 0` ⇒ treat as year (century not specified).
            * `1..31` remains unknown, to be disambiguated later.
        - When flag is `1` (YEAR):
            * century is specified if `value > 99`.
        - When flag is `2` (MONTH):
            * `value` must be in 1..12, else raise error.
        - When flag is `3` (DAY):
            * `value` must be in 1..31, else raise error.
        """
        # Full: 3 slots already set (idx is 0-based)
        if self._idx >= 2:
            return False

        # Range check
        if not 0 <= value <= 9_999:
            raise ValueError("Invalid Y/M/D value '%d', must be in 0..9999." % value)

        # Unknown flag
        if flag == 0:
            # . definitely a year
            if value > 31:
                if value > 99 and not self.is_year_set():
                    self.century_specified = True
                flag = 1  # set to YEAR
            # . definitely a year (0)
            elif value == 0:
                flag = 1  # set to YEAR

        # YEAR flag
        elif flag == 1:
            if value > 99 and not self.is_year_set():
                self.century_specified = True

        # MONTH flag
        elif flag == 2:
            if not 1 <= value <= 12:
                raise ValueError("Invalid month value '%d', must be in 1..12." % value)

        # DAY flag
        elif flag == 3:
            if not 1 <= value <= 31:
                raise ValueError("Invalid day value '%d', must be in 1..31." % value)

        # Invalid flag
        else:
            raise AssertionError(
                "Invalid Y/M/D flag value '%d', must be in 0..2" % flag
            )

        # Record Y/M/D value
        return self._record_ymd(flag, value)

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def set_ymd_str(
        self,
        flag: cython.int,
        token: str,
        token_len: cython.Py_ssize_t = -1,
    ) -> cython.bint:
        """(cfunc) Set one Y/M/D candidate value from a string `<'bool'>`.

        :param flag `<'int'>`: The Y/M/D flag (0=UNKNOWN, 1=YEAR, 2=MONTH, 3=DAY).
        :param token `<'str'>`: A string token, candidate for Y/M/D.
        :param token_len `<'int'>`: Optional precomputed length of `token`. Defaults to `-1`.
            If `token_len <= 0`, the function computes the length.
            Otherwise, `token_len` is treated as the token length.
        :returns `<'bool'>`: True if token `value` is recorded.
            False if the corresponding field is set or all slots were full.
        :raises `<'ValueError'>`: If the token is non-numeric or,
            the integer value is out of range or violates the basic
            domain of a labeled token.

        ## Rules
        - The `token` must only contain ACSII dights, else raise error.
        - The `int(token)` must be in 0..9999, else raise error.
        - When flag is `0` (UNKNOWN):
            * `len(token) > 2`  ⇒ treat as year and century specified.
            * `int(token) > 31` ⇒ treat as year.
            * `int(token) == 0` ⇒ treat as year.
            * `1..31` remains unknown, to be disambiguated later.
        - When flag is `1` (YEAR):
            * century is specified if `len(token) > 2`.
        - When flag is `2` (MONTH):
            * `int(token)` must be in 1..12, else raise error.
        - When flag is `3` (DAY):
            * `int(token)` must be in 1..31, else raise error.
        """
        # Full: 3 slots already set (idx is 0-based)
        if self._idx >= 2:
            return False

        # Parse to value integer
        if token_len <= 0:
            token_len = str_len(token)
        if not utils.is_str_ascii_digits(token, token_len):
            raise ValueError(
                "Invalid Y/M/D value '%s', cannot be converted to an integer" % token
            )
        value: cython.ulonglong = utils.slice_to_uint(token, 0, token_len, token_len)

        # Range check
        if value > 9_999:
            raise ValueError("Invalid Y/M/D value '%d', must be in 0..9999." % value)

        # Unknown flag
        if flag == 0:
            # . definitely a year (length > 2: '0001')
            if token_len > 2:
                if not self.is_year_set():
                    self.century_specified = True
                flag = 1  # set to YEAR
            # . definitely a year (100..9999)
            elif value > 31:
                flag = 1  # set to YEAR
            # . definitely a year (0)
            elif value == 0:
                flag = 1  # set to YEAR

        # YEAR flag
        elif flag == 1:
            if token_len > 2 and not self.is_year_set():  # e.g '0001'
                self.century_specified = True

        # MONTH flag
        elif flag == 2:
            if not 1 <= value <= 12:
                raise ValueError("Invalid month value '%d', must be in 1..12." % value)

        # DAY flag
        elif flag == 3:
            if not 1 <= value <= 31:
                raise ValueError("Invalid day value '%d', must be in 1..31." % value)

        # Invalid flag
        else:
            raise AssertionError(
                "Invalid Y/M/D flag value '%d', must be in 0..2" % flag
            )

        # Record Y/M/D value
        return self._record_ymd(flag, value)

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def ymd_slots_filled(self) -> cython.int:
        """(cfunc) Return the number of Y/M/D slots are recorded so far (0..3) `<'int'>`."""
        return self._idx + 1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def ymd_roles_resolved(self) -> cython.int:
        """(cfunc) Return how many Y/M/D roles are known so far (0..3) `<'int'>`."""
        return (self._yidx != -1) + (self._midx != -1) + (self._didx != -1)

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def could_be_day(self, value: cython.longlong) -> cython.bint:
        """(cfunc) Determines whether the `value` could be a day-of-month
        given current Y/M/D labels `<'bool'>`.

        :param value `<'int'>`: Candidate for day-of-month.
        :returns `<'bool'>`: True if `value` could represent a valid
            day-of-month under the current Y/M/D constraints; False otherwise.
        """
        # Day slot already assigned
        if self._didx != -1:
            return False

        # Day is 1-based
        if value < 1:
            return False

        # Month unknown ⇒ any 1..31 could be a day
        if self._midx == -1:
            return value <= 31
        month: cython.int = self._ymd[self._midx]

        # Month known but year unknown -> check with a leap year (2000)
        if self._yidx == -1:
            return value <= utils.days_in_month(2000, month)
        year: cython.int = self._ymd[self._yidx]

        # Both month and year are known
        return value <= utils.days_in_month(year, month)

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def could_be_doy(self, value: cython.longlong) -> cython.bint:
        """(cfunc) Determines whether the `value` could be a day-of-year
        given current Y/M/D labels `<'bool'>`.

        :param value `<'int'>`: Candidate for day-of-year.
        :returns `<'bool'>`: True if `value` could represent a valid
            day-of-year under the current Y/M/D constraints; False otherwise.
        """
        # Day of year already assigned
        if self.doy != -1:
            return False

        # Day of year is 1-based
        if value < 1:
            return False

        # Either month or day is known
        if self._midx != -1 or self._didx != -1:
            return False

        # Year unknown
        if self._yidx == -1:
            return False
        year: cython.int = self._ymd[self._yidx]

        # Check Range
        return value <= utils.days_in_year(year)

    # Resolve ---------------------------------------------------------
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def resolve(self, yearfirst: cython.bint, dayfirst: cython.bint) -> cython.bint:
        """(cfunc) Resolve unlabeled/ambiguous Y/M/D tokens into concrete year/month/day
        values in-place, using the supplied disambiguation preferences.

        This method inspects the three positional Y/M/D slots together with their
        known-role indices. It chooses the most plausible assignment according to
        simple domain rules and the `yearfirst` / `dayfirst` preferences, then writes
        the results to `self.year`, `self.month`, and `self.day`. Components that
        cannot be inferred remain `-1`.

        After resolving Y/M/D, if `century_specified` is False and `0 <= year < 100`,
        the year is adjusted to the current century using a ±50-year sliding window
        relative to today's year.

        :param yearfirst `<'bool'>`: If True, break remaining ties in favor of
            interpreting an unlabeled ambiguous token as the year.
        :param dayfirst `<bool'>`: If True, break remaining ties in favor of
            interpreting an unlabeled ambiguous token as the day (when
            compatible with basic month/day ranges).
        :returns `<'bool'>`: True if the result contains any datetime information
            at all (date, time, weekday, or tzoffset) after resolution; False otherwise.
            Note this is a `presence` check, not a full calendar validity check.

        ## Notes
        - With one token present, values > 31 are taken as year; otherwise preference
          is applied (month if labeled, else day).
        - With two tokens present, obvious year/month ordering is chosen first
          (e.g., 99-Feb vs Feb-99), else `dayfirst` influences the decision.
        - With three tokens present:
            * If two roles are already labeled, the remaining role is deduced.
            * If roles are largely unlabeled, heuristics prefer placements that
              satisfy basic ranges (e.g., day ≤ 31, month ≤ 12) and `yearfirst`.
        - This method does not normalize impossible combinations beyond the above
          rules; unsupported values may remain `-1` for later handling by the parser.
        - This method must be called before accessing the resolved year/month/day values.
        """
        # Already resolved
        if self._resolved:
            return self.valid()

        # Resolve Y/M/D
        slots_filled: cython.int = self.ymd_slots_filled()
        roles_labeled: cython.int = self.ymd_roles_resolved()
        yidx: cython.int = self._yidx
        midx: cython.int = self._midx
        didx: cython.int = self._didx
        v0: cython.int = self._ymd[0]
        v1: cython.int = self._ymd[1]
        v2: cython.int = self._ymd[2]

        # Branch: at least two Y/M/D are filled with labels (no infer)
        if slots_filled == roles_labeled > 1:
            self.year = self._ymd[yidx] if yidx != -1 else -1
            self.month = self._ymd[midx] if midx != -1 else -1
            self.day = self._ymd[didx] if didx != -1 else -1

        # Branch: one Y/M/D value
        elif slots_filled == 1:
            if yidx != -1:
                self.year = v0  # labeled as year
                # . day-of-year conversion
                if self.doy != -1:
                    _ymd = utils.ymd_fr_doy(v0, self.doy)
                    self.month, self.day = _ymd.month, _ymd.day
            elif midx != -1:
                self.month = v0  # labeled as month
            elif didx != -1:
                self.day = v0  # labeled as day
            elif v0 > 31:
                self.year = v0  # must be year (> 31)
            else:
                self.day = v0  # probably day

        # Branch: two Y/M/D values
        elif slots_filled == 2:
            # . month labeled
            if midx != -1:
                if midx == 0:
                    if v1 > 31 or (v0 == 2 and v1 > 29):
                        self.month, self.year = v0, v1  # Jan-99
                    else:
                        self.month, self.day = v0, v1  # Jan-01 (probably)
                else:
                    if v0 > 31 or (v1 == 2 and v0 > 29):
                        self.year, self.month = v0, v1  # 99-Jan
                    else:
                        self.day, self.month = v0, v1  # 01-Jan (probably)
            # . month not labeled (infer)
            elif v0 > 31 or (v1 == 2 and v0 > 29):
                self.year, self.month = v0, v1  # 99-Feb
            elif v1 > 31 or (v0 == 2 and v1 > 29):
                self.month, self.year = v0, v1  # Feb-99
            elif dayfirst and 1 <= v1 <= 12:
                self.day, self.month = v0, v1  # 01-Jan
            else:
                self.month, self.day = v0, v1  # Jan-01

        # Branch: three Y/M/D values
        elif slots_filled == 3:
            # Case: two labels
            if roles_labeled == 2:
                # . month labeled
                if midx != -1:
                    self.month = self._ymd[midx]
                    #: the other flag is year
                    if yidx != -1:
                        self.year = self._ymd[yidx]
                        self.day = self._ymd[3 - yidx - midx]
                    #: the other flag is day
                    else:
                        self.day = self._ymd[didx]
                        self.year = self._ymd[3 - midx - didx]
                # . year labeled
                elif yidx != -1:
                    self.year = self._ymd[yidx]
                    #: the other flag is month
                    if midx != -1:
                        self.month = self._ymd[midx]
                        self.day = self._ymd[3 - yidx - midx]
                    #: the other flag is day
                    else:
                        self.day = self._ymd[didx]
                        self.month = self._ymd[3 - yidx - didx]
                # . day labeled
                else:
                    self.day = self._ymd[didx]
                    #: the other flag is year
                    if yidx != -1:
                        self.year = self._ymd[yidx]
                        self.month = self._ymd[3 - yidx - didx]
                    #: the other flag is month
                    else:
                        self.month = self._ymd[midx]
                        self.year = self._ymd[3 - midx - didx]

            # Case: month labeled (infer)
            elif midx == 0:
                if v1 > 31:
                    self.month, self.year, self.day = v0, v1, v2  # Apr-2003-25
                else:
                    self.month, self.day, self.year = v0, v1, v2  # Apr-25-2003
            elif midx == 1:
                if v0 > 31 or (yearfirst and 0 < v2 <= 31):
                    self.year, self.month, self.day = v0, v1, v2  # 99-Jan-01
                else:
                    self.day, self.month, self.year = v0, v1, v2  # 01-Jan-99
            elif midx == 2:
                if v1 > 31:
                    self.day, self.year, self.month = v0, v1, v2  # 01-99-Jan
                else:
                    self.year, self.day, self.month = v0, v1, v2  # 99-01-Jan

            # Case: month not labeled (infer)
            else:
                if (
                    v0 > 31
                    or yidx == 0
                    or (yearfirst and 0 < v1 <= 12 and 0 < v2 <= 31)
                ):
                    if dayfirst and 0 < v2 <= 12:
                        self.year, self.day, self.month = (v0, v1, v2)  # 99-01-Jan
                    else:
                        self.year, self.month, self.day = (v0, v1, v2)  # 99-Jan-01
                elif v0 > 12 or (dayfirst and 0 < v1 <= 12):
                    self.day, self.month, self.year = (v0, v1, v2)  # 01-Jan-99
                else:
                    self.month, self.day, self.year = (v0, v1, v2)  # Jan-01-99

        # Century adjustment (if necessary)
        if not self.century_specified and 0 <= self.year < 100:
            year_now: cython.int = localtime().tm_year
            year: cython.int = self.year + (year_now // 100) * 100
            # . too far into the future
            if year >= year_now + 50:
                year -= 100
            # . too distance from the now
            elif year < year_now - 50:
                year += 100
            self.year = year

        # Check validity
        self._resolved = True
        return self.valid()

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def valid(self) -> cython.bint:
        """(cfunc) Return whether the parsed result currently contains `any`
        datetime information.

        A result is considered valid if at least one of the following fields
        has been set to a non-sentinel value: year, month, day, hour, minute,
        second, microsecond, weekday, or tzoffset (tzoffset != -100_000).

        :returns `<'bool'>`: True if any component is present;
            False if all components are unset.
        """
        return (
            self.is_year_set()
            or self.is_month_set()
            or self.is_day_set()
            or self.is_hour_set()
            or self.is_minute_set()
            or self.is_second_set()
            or self.is_microsecond_set()
            or self.is_weekday_set()
            or self.is_tzoffset_set()
        )

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_year_set(self) -> cython.bint:
        """(cfunc) Return whether the `year` value is set `<'bool'>`."""
        return self._yidx != -1 or self.year != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_month_set(self) -> cython.bint:
        """(cfunc) Return whether the `month` value is set `<'bool'>`."""
        return self._midx != -1 or self.month != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_day_set(self) -> cython.bint:
        """(cfunc) Return whether the `day` value is set `<'bool'>`."""
        return self._didx != -1 or self.day != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_hour_set(self) -> cython.bint:
        """(cfunc) Return whether the `hour` value is set `<'bool'>`."""
        return self.hour != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_minute_set(self) -> cython.bint:
        """(cfunc) Return whether the `minute` value is set `<'bool'>`."""
        return self.minute != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_second_set(self) -> cython.bint:
        """(cfunc) Return whether the `second` value is set `<'bool'>`."""
        return self.second != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_microsecond_set(self) -> cython.bint:
        """(cfunc) Return whether the `microsecond` value is set `<'bool'>`."""
        return self.microsecond != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_weekday_set(self) -> cython.bint:
        """(cfunc) Return whether the `weekday` value is set `<'bool'>`."""
        return self.weekday != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_doy_set(self) -> cython.bint:
        """(cfunc) Return whether the `doy` (day-of-year) value is set `<'bool'>`."""
        return self.doy != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_ampm_set(self) -> cython.bint:
        """(cfunc) Return whether the `ampm` value is set `<'bool'>`."""
        return self.ampm != -1

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def is_tzoffset_set(self) -> cython.bint:
        """(cfunc) Return whether the `tzoffset` value is set `<'bool'>`."""
        return self.tzoffset != utils.NULL_TZOFFSET

    # Internal --------------------------------------------------------
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def _record_ymd(self, flag: cython.int, value: cython.int) -> cython.bint:
        """(internal) Record a Y/M/D value and (optionally) its role index `<'bool'>`.

        :param flag `<'int'>`: The Y/M/D flag (0=UNKNOWN, 1=YEAR, 2=MONTH, 3=DAY).
        :param value `<'int'>`: Validated Y/M/D integer value.
        :returns `<'bool'>`: True if value is written.
            False if the corresponding field is set or all slots were full.

        ## Rules
        - Appends `value` into the next Y/M/D slot.
        - If `flag` is (1=YEAR, 2=MONTH, 3=DAY) and the corresponding
          index is not yet assigned, records the index of this value.
          Otherwise returns False.
        - If all 3 slots are already used, returns False and does not write.
        """
        # Full: 3 slots already set (idx is 0-based)
        idx: cython.int = self._idx
        if idx >= 2:
            return False
        idx += 1  # advance index

        # Unknown flag
        if flag == 0:
            self._ymd[idx] = value
            self._idx = idx
            return True

        # YEAR flag
        if flag == 1:
            # . year already set
            if self._yidx != -1:
                if self.could_be_doy(value):
                    # candidate for day-of-year
                    self.doy = value
                    return True
                return False
            # . set year & index
            self._ymd[idx] = value
            self._idx = self._yidx = idx
            return True

        # MONTH flag
        if flag == 2:
            # . month already set
            if self._midx != -1:
                return False
            # . set month & index
            self._ymd[idx] = value
            self._idx = self._midx = idx
            return True

        # DAY flag
        if flag == 3:
            # . day already set
            if self._didx != -1:
                return False
            # . set day & index
            self._ymd[idx] = value
            self._idx = self._didx = idx
            return True

        # Invalid flag
        return False

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def _reset(self) -> cython.bint:
        """(internal) Reset the result to inital state."""
        # Y/M/D
        self._ymd = [-1, -1, -1]
        self._idx = self._yidx = self._midx = self._didx = -1
        self._resolved = False
        # Result
        self.year = self.month = self.day = -1
        self.hour = self.minute = self.second = self.microsecond = -1
        self.weekday = self.doy = self.ampm = -1
        #: tzoffset must be between -86400...86400,
        #: -100_000 represents no tzoffset.
        self.tzoffset = utils.NULL_TZOFFSET
        self.tzoffset_finalized = False
        self.century_specified = False
        return True

    # Special methods -------------------------------------------------
    def __repr__(self) -> str:
        reprs: list[str] = []

        # Datetime results
        # . year
        if self.is_year_set():
            reprs.append("year=%d" % self.year)
        elif self._yidx != -1:
            reprs.append("year=%d" % self._ymd[self._yidx])
        # . month
        if self.is_month_set():
            reprs.append("month=%d" % self.month)
        elif self._midx != -1:
            reprs.append("month=%d" % self._ymd[self._midx])
        # . day
        if self.is_day_set():
            reprs.append("day=%d" % self.day)
        elif self._didx != -1:
            reprs.append("day=%d" % self._ymd[self._didx])
        # . rest
        if self.is_hour_set():
            reprs.append("hour=%d" % self.hour)
        if self.is_minute_set():
            reprs.append("minute=%d" % self.minute)
        if self.is_second_set():
            reprs.append("second=%d" % self.second)
        if self.is_microsecond_set():
            reprs.append("microsecond=%d" % self.microsecond)
        if self.is_weekday_set():
            reprs.append("weekday=%d" % self.weekday)
        if self.is_doy_set():
            reprs.append("doy(day-of-year)=%d" % self.doy)
        if self.is_ampm_set():
            reprs.append("ampm=%d" % self.ampm)
        if self.is_tzoffset_set():
            reprs.append("tzoffset=%d" % self.tzoffset)

        # Construct
        return "<'%s' (resolved=%s: %s)>" % (
            self.__class__.__name__,
            self._resolved,
            " ".join(reprs),
        )

    def __bool__(self) -> bool:
        return self.valid()


@cython.cclass
class Parser:
    """Flexible date/time parser with ISO fast-path and token heuristics.

    The `Parser` reads a free-form date/time string and populates an
    internal `Result` accumulator via two complementary strategies:

    1) `ISO fast-path`: a tuned parser for ISO-8601 calendar/ordinal/week dates
       with optional time, fractional seconds, and timezone. When the core ISO
       portion parses but an extra tail remains (e.g., AM/PM, weekday, timezone
       adornments), a lightweight “ISO-extra” pass consumes the tail.
    2) `Heuristic token path`: a tokenizer + left→right scan that recognizes
       numeric blocks, month/weekday names, AM/PM, timezone names, and timezone
       offsets. Ambiguous Y/M/D triples are resolved later according to the
       configuration (or explicit flags passed to `parse`).

    The parser defers construction of the final `datetime` object until all
    fields have been gathered and disambiguated.
    """

    _ignoretz: cython.bint
    _cfg: Configs
    _res: Result
    _pos: cython.Py_ssize_t
    _length: cython.Py_ssize_t
    _tokens: list[str]
    _token1: str
    __cls: object

    def __init__(self, cfg: Configs = None) -> None:
        """Flexible date/time parser with ISO fast-path and token heuristics.

        The `Parser` reads a free-form date/time string and populates an
        internal `Result` accumulator via two complementary strategies:

        1) `ISO fast-path`: a tuned parser for ISO-8601 calendar/ordinal/week dates
        with optional time, fractional seconds, and timezone. When the core ISO
        portion parses but an extra tail remains (e.g., AM/PM, weekday, timezone
        adornments), a lightweight “ISO-extra” pass consumes the tail.
        2) `Heuristic token path`: a tokenizer + left→right scan that recognizes
        numeric blocks, month/weekday names, AM/PM, timezone names, and timezone
        offsets. Ambiguous Y/M/D triples are resolved later according to the
        configuration (or explicit flags passed to `parse`).

        The parser defers construction of the final `datetime` object until all
        fields have been gathered and disambiguated.

        :param cfg `<'Configs/None'>`: The Parser configuration. Defaults to `None`.

            - If `None`, uses the module's default `Configs`.
            - For more details, see the `Configs` class documentation.
        """
        if cfg is None:
            cfg = _DEFAULT_CONFIGS
        self._cfg = cfg
        self._res = Result()

    # Parse --------------------------------------------------------------------------------
    @cython.ccall
    def parse(
        self,
        dtstr: str,
        default: object = None,
        yearfirst: object = None,
        dayfirst: object = None,
        ignoretz: cython.bint = True,
        isoformat: cython.bint = True,
        dtclass: object = None,
    ) -> datetime.datetime:
        """Parse a date/time string into a datetime `<'datetime.datetime'>`.

        ## Parsing Strategies
        1) `ISO fast-path` (when `isoformat=True`): attempts an ISO 8601 calendar/ordinal/week
          date plus optional time, fractional seconds, and timezone. If an extra tail remains
          (e.g., AM/PM, weekday, timezone tail), a lightweight ISO-extra pass handles it.
        2) `Heuristic token path` (fallback or when `isoformat=False`): tokenizes the string
          and scans left→right, using specialized handlers for numeric blocks, month/weekday
          names, AM/PM, timezone names, and timezone offsets.

        After parsing, ambiguous Y/M/D fields are resolved using `yearfirst`/`dayfirst` (or the
        configured defaults when they are `None`). Finally, a datetime is built using parsed
        fields plus `default` for any missing calendar components.

        :param dtstr `<'str'>`: The input date/time string.
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
        :param dtclass `<'type[datetime.datetime]/None'>`: Optional custom datetime class. Defaults to `None`.
            If `None` uses python's built-in `datetime.datetime` as the constructor.
        :returns `<'datetime.datetime'>`: The parsed datetime (or subclass if 'dtclass' is specified).
        :raises `<'ParserFailedError'>`: If nothing extractable is found (or ISO parsing
            fails and token scanning yields no fields).
        :raises `<'ParserBuildError'>`: If fields cannot be assembled into a datetime
            (e.g., invalid field combination, unsupported custom class).

        ## Field Construction
        - `Y/M/D`: use parsed values; if missing, copy from `default` (if provided), otherwise raise.
          If `day > 28`, it is clamped to the month's maximum.
        - `Weekday`: if a weekday was parsed and does not match `(Y, M, D)`, the date is shifted by
          the difference so the resulting weekday matches the requested one (within the same week as
          the parsed date).
        - `Time`: unset H/M/S/us default to `0`. AM/PM is applied when present.
        - `Timezone`:
            * If `ignoretz=True`, any parsed timezone info is ignored and a naive datetime
              (`tzinfo=None`) is returned.
            * Otherwise, a timezone-aware datetime is returned if a timezone name/offset was parsed:
              UTC for offset `0`, or a fixed-offset timezone for non-zero offsets.

        ## Ambiguous Y/M/D
        Both `yearfirst` and `dayfirst` control how ambiguous digit tokens are interpreted;
        `yearfirst` has higher priority. When all three are ambiguous (e.g., `01/05/09`):
        - `yearfirst=False & dayfirst=False` → `M/D/Y`  → `2009-01-05`
        - `yearfirst=False & dayfirst=True`  → `D/M/Y`  → `2009-05-01`
        - `yearfirst=True  & dayfirst=False` → `Y/M/D`  → `2001-05-09`
        - `yearfirst=True  & dayfirst=True`  → `Y/D/M`  → `2001-09-05`

        When the year is already known (e.g., `32/01/05`), `dayfirst` alone decides between `Y/M/D`
        vs `Y/D/M`. When only one value is ambiguous, the parser picks the only consistent
        interpretation and ignores the flags.
        """
        # Validate dtstr
        if dtstr is None:
            errors.raise_parser_failed_error(self._cls(), "Cannot parse None.")

        # Settings
        self._ignoretz = ignoretz

        # Process
        self._process(dtstr, isoformat)

        # Prepare
        if not self._res.resolve(
            self._cfg._yearfirst if yearfirst is None else bool(yearfirst),
            self._cfg._dayfirst if dayfirst is None else bool(dayfirst),
        ):
            errors.raise_parser_failed_error(
                self._cls(),
                "Failed to parse '%s' %s.\n"
                "Cannot extract any datetime components." % (dtstr, type(dtstr)),
            )

        # Build
        return self._build(dtstr, default, dtclass)

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _process(self, dtstr: str, isoformat: cython.bint) -> cython.bint:
        """(internal) Parse a datetime string, preferring ISO then falling back to tokens `<'bool'>`.

        This is the entrypoint for a single parse pass. It resets internal state, then
        chooses the parsing strategy:
        - If `isoformat=True`, try the ISO-8601 path via `_process_iso_format(dtstr)`.
          That routine `fallsback` automatically to the token (timelex) pipeline when
          the input is not a clean ISO date/time.
        - If `isoformat=False`, skip ISO pre-checks and go straight to the token pipeline
          via `_process_timelex_tokens(dtstr)`.

        Error handling
        - Format mismatches do `NOT` raise: the ISO path falls back to tokens.
        - Unexpected internal errors are wrapped and re-raised as `ParserFailedError`
        with the original exception chained.

        :param dtstr `<'str'>`: Input datetime string.
        :param isoformat `<'bool'>`: Prefer ISO-8601 parsing first if True;
            otherwise use the token pipeline directly. Notice even with
            `isoformat=True`, the parser may still fall back to token parsing
            if the input is not a valid ISO format. But this gives better
            performance for most common datetime strings.
        :returns `<'bool'>`: Always True on completion.
        :raises `<'ParserFailedError'>`: If an internal error occurs during processing.
        """
        # Reset result and (dtstr) position / length
        self._res._reset()
        self._pos = 0
        self._length = str_len(dtstr)

        # Process
        try:
            if isoformat:
                self._process_iso_format(dtstr)
            else:
                self._process_timelex_tokens(dtstr)
        except AssertionError:
            raise
        except Exception as err:
            errors.raise_parser_failed_error(
                self._cls(), "Failed to parse '%s' %s" % (dtstr, type(dtstr)), err
            )

        # Finished
        return True

    # Build --------------------------------------------------------------------------------
    @cython.cfunc
    @cython.inline(True)
    def _build(
        self,
        dtstr: str,
        default: object,
        dtclass: object,
    ) -> datetime.datetime:
        """(internal) Build a datetime from the parsed `Result`, honoring timezone settings `<'datetime.datetime'>`.

        Decides timezone strategy, then delegates to `_generate_dt` to materialize the object:
        - If `self._ignoretz` is True or `self._res.tzoffset` is unset (sentinel -100_000):
          build a `timezone-naive` datetime (no tzinfo), ignoring any parsed tzname/offset.
        - Else: build a `timezone-aware` datetime:
            * `UTC` when `tzoffset == 0`
            * A fixed-offset `timezone` via the parsed `tzoffset`.

        :param dtstr `<'str'>`: The original input string (used for error context).
        :param default `<'datetime/date/None'>`: Fallback date/time source for any
            missing `Y/M/D` components (see `_generate_dt` for rules). If None and
            a required component is missing, building fails.
        :param dtclass `<'type[datetime.datetime]'>`: Optional designated subclass
            of `datetime.datetime` for construction. If provided, it is called like
            `dtclass(year=..., tzinfo=...)`. If None, construct with python's built-in
            `datetime.datetime`.
        :returns `<'datetime.datetime'>`: The built datetime (naive or aware per above).
        :raises `<'ParserBuildError'>`: If an internal error occurs during building.
        """
        try:
            # Ignore timezone
            if self._ignoretz:
                return self._gen_dt(default, None, dtclass)

            # Timezone-naive
            offset: cython.int = self._res.tzoffset
            if (
                offset == utils.NULL_TZOFFSET
            ):  # -100_000 is the sentinel for 'no tzoffset'
                return self._gen_dt(default, None, dtclass)

            # Timezone-aware
            else:
                tzinfo = utils.UTC if offset == 0 else utils.tz_new(0, 0, offset)
                return self._gen_dt(default, tzinfo, dtclass)

        except Exception as err:
            errors.raise_parser_failed_error(
                self._cls(),
                "Failed to build datetime from '%s'.\n%s" % (dtstr, self._res),
                err,
            )

    @cython.cfunc
    @cython.inline(True)
    def _gen_dt(
        self,
        default: object,
        tzinfo: object,
        dtclass: object,
    ) -> datetime.datetime:
        """(internal) Generate a datetime from `Result` + `default` and optional tzinfo `<'datetime.datetime'>`.

        ## Field resolution order
        - Year / Month / Day:
            * If the field is set in `Result`, use it.
            * Else, if `default` is a date/datetime, copy the field from `default`.
            * Else, raise `ValueError` (missing required calendar component).
            * If `day > 28`, clamp to the month's maximum (e.g., “2023-02-30” → 2023-02-28).

        - Weekday:
            * If `Result.weekday` is set and does not match the computed weekday of (Y, M, D),
              shift the date by the difference so that the weekday matches. (Weekday thus
              takes precedence over an inconsistent calendar date and the resulting date
              is the requested weekday in the same week as the original Y/M/D.)

        - Time of day
            * unset components default to zero.
            * hour → 0, minute → 0, second → 0, microsecond → 0.

        :param default `<'datetime/date/None'>`: Fallback for missing Y/M/D.
        :param tzinfo `<'tzinfo/None'>`: Timezone info to attach (None yields a naive datetime).
        :param dtclass `<'type[datetime.datetime]/None'>`: Optional custom datetime class.
            If `None` uses python's built-in `datetime.datetime` as the constructor.
        :returns `<'datetime.datetime'>`: The constructed datetime.
        :raises `<'ValueError'>`: If a required Y/M/D component is missing and no `default`.
        :raises `<'TypeError'>`: If a provided `dtclass` cannot be constructed from the fields.
        """
        # Check default
        has_default: cython.bint = utils.is_date(default)

        # . year
        if self._res.is_year_set():
            yy = self._res.year
        elif has_default:
            yy = datetime.datetime_year(default)
        else:
            raise ValueError("Lack of 'year'.")
        # . month
        if self._res.is_month_set():
            mm = self._res.month
        elif has_default:
            mm = datetime.datetime_month(default)
        else:
            raise ValueError("Lack of 'month'.")
        # . day
        if self._res.is_day_set():
            dd = self._res.day
        elif has_default:
            dd = datetime.datetime_day(default)
        else:
            raise ValueError("Lack of 'day'.")
        if dd > 28:
            dd = min(dd, utils.days_in_month(yy, mm))
        # . weekday
        if self._res.is_weekday_set():
            wkd: cython.int = utils.ymd_weekday(yy, mm, dd)
            if wkd != self._res.weekday:
                _ymd = utils.ymd_fr_ord(
                    utils.ymd_to_ord(yy, mm, dd) + self._res.weekday - wkd
                )
                yy, mm, dd = _ymd.year, _ymd.month, _ymd.day
        # . hour
        hh = self._res.hour if self._res.is_hour_set() else 0
        # . minute
        mi = self._res.minute if self._res.is_minute_set() else 0
        # . second
        ss = self._res.second if self._res.is_second_set() else 0
        # . microsecond
        us = self._res.microsecond if self._res.is_microsecond_set() else 0

        # Generate datetime
        return utils.dt_new(yy, mm, dd, hh, mi, ss, us, tzinfo, 0, dtclass)

    # ISO format ---------------------------------------------------------------------------
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _process_iso_format(self, dtstr: str) -> cython.bint:
        """(internal) Parse `dtstr` using an ISO-8601-first strategy, with graceful fallback `<'bool'>`.

        ## Strategy
        1) `Date: _parse_iso_date(dtstr)` — parses an ISO calendar/ordinal/week date
        at the beginning of the string and writes Y/M/D. On failure, the method
        `fallback` to the token (timelex) pipeline.

        2) `Time: _parse_iso_time(dtstr)` — parses `T`/space-separated ISO time,
        fractional seconds, and (when present) trailing weekday/AM-PM/timezone via
        `_parse_iso_extra`. On failure, the method `fallback` to the token pipeline.

        ## Notes
        - This routine never raises on ISO mismatches; it delegates to the token
          pipeline for flexible, heuristic parsing of non-ISO inputs.
        - On ISO success, `self._pos` is advanced past the parsed segment(s) and
          `Result` fields (Y/M/D/H/M/S/us/tz) are updated as applicable.
        - On fallback, `_process_timelex_tokens(dtstr)` re-tokenizes from the current
          position and continues parsing with the general handlers.

        :param dtstr `<'str'>`: The original datetime string.
        :returns `<'bool'>`: Always `True` (either ISO handled it or fallback did).
        """
        # Parse date components
        if not self._parse_iso_date(dtstr):
            # ISO format date parser failed,
            # fallback to timelex tokens processor.
            return self._process_timelex_tokens(dtstr)

        # Parse time components
        if not self._parse_iso_time(dtstr):
            # ISO format time parser failed,
            # fallback to timelex tokens processor.
            return self._process_timelex_tokens(dtstr)

        # Success
        return True

    # . parser - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_iso_date(self, dtstr: str) -> cython.bint:
        """(internal) Parse an ISO-8601 date components and update the current result.

        Parses an ISO-8601 `date` at the beginning of `dtstr`. On success,
        writes Y/M/D into `self._res` (and sets `century_specified=True`),
        and advances `self._pos` to the first character after the date.
        On failure, returns False and does not modify `position self._pos` or
        the `Result self._res`.

        :param dtstr <'str'>: Full datetime input string.
        :return <'bool'>: True if a valid ISO date prefix is parsed; otherwise False.

        Accepted:
        - Calendar: `'YYYY-MM-DD'`   | `'YYYYMMDD'`
        - Ordinal : `'YYYY-DDD'`     | `'YYYYDDD'`
        - Week    : `'YYYY-Www[-D]'` | `'YYYYWww[D]'` | `'YYYYWww[-D]'`
                    (D=1..7, Monday=1; default D=1 when omitted)

        Not accepted:
        - Partial dates (e.g., YYYY, YYYY-MM)
        - Signed/expanded years (e.g., +012345)
        - Time parts (this function parses date only)
        """
        # ISO format length must be >= 7: YYYYWww or YYYYDDD
        length: cython.Py_ssize_t = self._length
        if length < 7:
            return False  # exit: invalid

        # ISO format always starts with year (YYYY)
        year: cython.int = utils.parse_isoyear(dtstr, 0, length)
        if year == -1:
            return False  # exit: invalid

        # Parse components
        # . YYYY[-]
        ch4: cython.Py_UCS4 = str_read(dtstr, 4)
        pos: cython.Py_ssize_t
        if utils.is_date_sep(ch4):
            if length < 8:
                #: For ISO format with "-" separator,
                #: the minimum length should be 8.
                return False  # exit: invalid

            # . YYYY-MM[-]
            ch7: cython.Py_UCS4 = str_read(dtstr, 7)
            if utils.is_date_sep(ch7):
                # . parse month: YYYY-[MM]
                month: cython.int = utils.parse_isomonth(dtstr, 5, length)
                if month == -1:
                    return False  # exit: invalid
                # . parse day: YYYY-MM-[DD]
                day: cython.int = utils.parse_isoday(dtstr, 8, length)
                if day == -1:
                    return False  # exit: invalid
                pos = 10  # after: YYYY-MM-DD

            # YYYY-[W]
            elif utils.is_isoweek_sep(str_read(dtstr, 5)):
                # . parse week: YYYY-W[ww]
                week: cython.int = utils.parse_isoweek(dtstr, 6, length)
                if week == -1:
                    return False  # exit: invalid
                # . parse weekday: YYYY-Www[-D]
                if length > 9 and utils.is_date_sep(str_read(dtstr, 8)):
                    wkd: cython.int = utils.parse_isoweekday(dtstr, 9, length)
                    if wkd == -1:
                        return False  # exit: invalid
                    pos = 10  # after: YYYY-Www-D
                else:
                    wkd = 1  # default to Monday
                    pos = 8  # after: YYYY-Www
                # . calculate MM/DD
                _ymd = utils.ymd_fr_iso(year, week, wkd)
                year, month, day = _ymd.year, _ymd.month, _ymd.day

            # . YYYY-DD[D]
            elif utils.is_ascii_digit(ch7):
                # . parse days of the year: YYYY-[DDD]
                days: cython.int = utils.parse_isodoy(dtstr, 5, length)
                if days == -1:
                    return False  # exit: invalid
                # Calculate MM/DD
                _ymd = utils.ymd_fr_doy(year, days)
                month, day = _ymd.month, _ymd.day
                pos = 8  # after: YYYY-DDD

            # . Invalid ISO format
            else:
                return False  # exit: invalid

        # . YYYY[W]
        elif utils.is_isoweek_sep(ch4):
            # . parse week: YYYYW[ww]
            week: cython.int = utils.parse_isoweek(dtstr, 5, length)
            if week == -1:
                return False  # exit: invalid
            # . parse weekday
            wkd: cython.int
            if length > 7:
                # . YYYYWww[-D]
                if length > 8 and utils.is_date_sep(str_read(dtstr, 7)):
                    wkd = utils.parse_isoweekday(dtstr, 8, length)
                    if wkd == -1:
                        wkd = 1  # default to Monday
                        pos = 7  # after: YYYYWww
                    else:
                        pos = 9  # after: YYYYWww-D
                # . YYYYWww[D]
                else:
                    wkd = utils.parse_isoweekday(dtstr, 7, length)
                    if wkd == -1:
                        wkd = 1  # default to Monday
                        pos = 7  # after: YYYYWww
                    else:
                        pos = 8  # after: YYYYWwwD
            else:
                wkd = 1  # default to Monday
                pos = 7  # after: YYYYWww
            # . calculate MM/DD
            _ymd = utils.ymd_fr_iso(year, week, wkd)
            year, month, day = _ymd.year, _ymd.month, _ymd.day

        # . YYYY[D]
        elif utils.is_ascii_digit(ch4):
            # . YYYYMMD[D]
            if length > 7 and utils.is_ascii_digit(str_read(dtstr, 7)):
                # . parse month: YYYY[MM]
                month: cython.int = utils.parse_isomonth(dtstr, 4, length)
                if month == -1:
                    return False  # exit: invalid
                # . parse day: YYYYMM[DD]
                day: cython.int = utils.parse_isoday(dtstr, 6, length)
                if day == -1:
                    return False  # exit: invalid
                pos = 8  # after: YYYYMMDD
            # . YYYYDDD
            else:
                # . YYYYDDD requires at least 7 characters (already guarded)
                # . parse days of the year: YYYY[DDD]
                days: cython.int = utils.parse_isodoy(dtstr, 4, length)
                if days == -1:
                    return False  # exit: invalid
                # Calculate MM/DD
                _ymd = utils.ymd_fr_doy(year, days)
                month, day = _ymd.month, _ymd.day
                pos = 7  # after: YYYYDDD

        # . Invalid ISO format
        else:
            return False

        # Update position & Set Y/M/D
        self._pos = pos  # update position
        self._res.century_specified = True
        self._res.set_ymd_int(1, year)
        self._res.set_ymd_int(2, month)
        self._res.set_ymd_int(3, day)
        return True  # exit: complete

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_iso_time(self, dtstr: str) -> cython.bint:
        """(internal) Parse ISO-8601 time components and update the current result.

        This method should be called only after `_parse_iso_date()` has successfully
        parsed the date portion at the start of `dtstr`. It attempts to parse a time
        directly following the date at `self._pos` in either extended or basic ISO form,
        optionally with fractional seconds and a UTC designator or numeric offset.

        On success, the method returns True. hour/minute/second/microsecond/tzoffset
        are set to the Result and `self._pos` is advanced to the first character after
        the time (typically end of string for strict ISO inputs). If there is no time
        part (EOF right after the date), this is treated as success and nothing is
        changed.

        On failure, the method returns False and leaves `self._pos` unchanged at the
        end of the date part. Callers should then fall back to tokenized (timelex)
        parsing for non-ISO time forms.

        :param dtstr <'str'>: Full datetime input string.
        :returns <'bool'>: True if a valid ISO time is parsed; otherwise False.

        ## Accepted:
        - Basic   : `'THHMMSS'`   | `' HHMMSS'`
        - Extended: `'THH:MM:SS'` | `' HH:MM:SS'`
        - Fraction: A fractional part right after seconds using '.' or ',' with 1..N digits;
                    only the first 6 digits are used (microseconds), excess are ignored.
        - UTC tz  : Trailing 'Z' or 'z' (recognized as UTC offset)
        - Numeric tz: "+HH:MM", "+HHMM", "-HH:MM", or "-HHMM"

        ## Behavioral notes
        - This routine requires seconds. Inputs like "THH:MM" are not accepted here and
        should be handled by the timelex fallback.
        - If a fractional separator is present with zero digits (e.g. ".") the routine
        treats the fraction as absent and continues per the implementation.
        - Microsecond rounding: the first up to 6 fractional digits are scaled to
        microseconds; additional digits are ignored.
        - When `self._ignoretz` is True, trailing 'Z' or numeric offsets are not parsed
        and will be left to the timelex fallback.
        """
        # Validate
        pos: cython.Py_ssize_t = self._pos
        length: cython.Py_ssize_t = self._length
        if pos == length:
            # eof: no time component
            return True  # exit: success
        if pos < 7 or length - pos < 7:
            #: The minimum time component is [HHMMSS],
            #: adding iso separator "T", the length
            #: of the 'dtstr' should have at least
            #: 7 or more characters.
            return False  # exit: invalid
        if not utils.is_iso_sep(str_read(dtstr, pos)):
            #: The charactor right after date components
            #: should be either "T" or " ".
            return False  # exit: invalid

        # Parse HH:MM:SS / HHMMSS
        # . hour: ...T[HH]
        hour: cython.int = utils.parse_isohour(dtstr, pos + 1, length)
        if hour == -1:
            return False  # exit: invalid
        # . with separator: ...THH[:]
        if utils.is_time_sep(str_read(dtstr, pos + 3)):
            # . THH:MM:SS requires at least 9 characters.
            if length - pos < 9:
                return False  # exit: invalid
            # . minute: ...THH:[MM]
            minute: cython.int = utils.parse_isominute(dtstr, pos + 4, length)
            if minute == -1:
                return False  # exit: invalid
            # . second: ...THH:MM:[SS]
            second: cython.int = utils.parse_isosecond(dtstr, pos + 7, length)
            if second == -1:
                return False  # exit: invalid
            # . Update position & Set H/M/S
            pos += 9  # after: ...THH:MM:SS
            self._res.hour = hour
            self._res.minute = minute
            self._res.second = second
            # . eof: ...THH:MM:SS
            if pos == length:
                self._pos = pos  # update position
                return True  # exit: success
        # . without separator: ...THH[]
        else:
            # . THHMMSS requires at least 7 characters (already guarded)
            # . minute: ...THH[MM]
            minute: cython.int = utils.parse_isominute(dtstr, pos + 3, length)
            if minute == -1:
                return False  # exit: invalid
            # . second: ...THHMM[SS]
            second: cython.int = utils.parse_isosecond(dtstr, pos + 5, length)
            if second == -1:
                return False  # exit: invalid
            # . Update position & Set H/M/S
            pos += 7  # after: ...THHMMSS
            self._res.hour = hour
            self._res.minute = minute
            self._res.second = second
            # . eof: ...THHMMSS
            if pos == length:
                self._pos = pos  # update position
                return True  # exit: success

        # Parse fraction: ...THH:MM:SS[.fff] / ...THH:MM:SS[,fff]
        if length - pos > 1 and str_read(dtstr, pos) in (46, 44):  # '.' or ','
            pos += 1  # skip: [./,]
            f_size: cython.int = 0
            us: cython.int = 0
            ch: cython.Py_UCS4
            while pos < length:
                ch = str_read(dtstr, pos)
                if not utils.is_ascii_digit(ch):
                    break  # non-digit: end of fraction
                if f_size < 6:
                    us = us * 10 + (ord(ch) - 48)
                    f_size += 1
                pos += 1  # digit beyond 6 are skipped
            # . set microsecond
            self._res.microsecond = utils.scale_fraction_to_us(us, f_size)
            # . eof: ...THH:MM:SS.ffffff[fff]
            if pos == length:
                self._pos = pos  # update position
                return True  # exit: success

        # Skip spaces
        while pos < length and str_read(dtstr, pos) == 32:  # ' '
            pos += 1
        if pos == length:
            self._pos = pos  # update position
            return True  # exit: success

        # Parse UTC offset
        if not self._ignoretz:
            ch: cython.Py_UCS4 = str_read(dtstr, pos)
            # Could be: ...THH:MM:SS[.ffffff][Z]
            if ch in (90, 122):  # 'Z' or 'z'
                extra: cython.Py_ssize_t = length - pos
                # . eof: ...THH:MM:SS[.ffffff]Z
                if extra == 1:
                    self._res.tzoffset = 0
                    self._res.tzoffset_finalized = True  # prevent further changes
                    self._pos = length  # update position
                    return True  # exit: success
                # . Z[space]: ...THH:MM:SS[.ffffff]Z[space]
                elif extra > 1 and str_read(dtstr, pos + 1) == 32:  # ' '
                    self._res.tzoffset = 0
                    self._res.tzoffset_finalized = True  # prevent further changes
                    pos += 2  # skip: [Z][space]
                    if pos == length:
                        self._pos = pos  # update position
                        return True  # exit: success

            # Could be: ...[+/-HHMM] / ...[+/-HH:MM]
            elif length - pos > 4 and utils.is_plus_or_minus_sign(ch):
                # . offset sign: ...[+/-]
                sign: cython.int = 1 if utils.is_plus_sign(ch) else -1
                # . offset hour: ...+[HH]
                hh: cython.int = utils.parse_isohour(dtstr, pos + 1, length)
                if hh == -1:
                    self._pos = pos  # update position
                    return self._parse_iso_extra(dtstr)  # exit: fallback
                # . offset minute: ...+HH[:]
                ch = str_read(dtstr, pos + 3)
                if utils.is_time_sep(ch):
                    # . +HH:[MM]
                    mi: cython.int = utils.parse_isominute(dtstr, pos + 4, length)
                    if mi == -1:
                        self._pos = pos  # update position
                        return self._parse_iso_extra(dtstr)  # exit: fallback
                    pos += 6  # after: +HH:MM
                else:
                    # . +HH[MM]
                    mi: cython.int = utils.parse_isominute(dtstr, pos + 3, length)
                    if mi == -1:
                        self._pos = pos  # update position
                        return self._parse_iso_extra(dtstr)  # exit: fallback
                    pos += 5  # after: +HHMM
                # . set UTC offset
                self._res.tzoffset = sign * (hh * 3_600 + mi * 60)
                self._res.tzoffset_finalized = True  # prevent further changes
                # . eof: ...THH:MM:SS[.ffffff]+HH:MM
                if pos == length:
                    self._pos = pos  # update position
                    return True  # exit: success

        # Still have extra characters
        self._pos = pos  # update position
        return self._parse_iso_extra(dtstr)  # exit: fallback

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_iso_extra(self, dtstr: str) -> cython.bint:
        """(internal) Parse trailing extra characters after a valid ISO time segment `<'bool'>`.

        This is a cut-down, resilient pass used when the ISO parser successfully extracted
        the time portion (`HH[:MM[:SS[.f]]]`) but stopped at additional trailing content.
        It tokenizes from the current `self._pos` and only handles the constructs that
        are valid after an ISO time by invoking specialized handlers for each token:
        1) Weekday names           → `_parse_token_weekday`
        2) AM/PM flags             → `_parse_token_ampm`
        3) Timezone names          → `_parse_token_tzname`
        4) Timezone offsets (+/-)  → `_parse_token_tzoffset`

        ## Notes
        - The `self._pos` is then updated to track the index within `self._tokens`
          (from `_timelex`), contrary to ISO parsers which track positions in the
          original `dtstr` string.
        - Handlers may consume additional lookahead tokens and advance `self._pos`
          accordingly (e.g., to skip separators and multi-part patterns). The main
          loop then continues from the updated position. Unrecognized non-space
          tokens are tolerated and skipped.
        - This routine is resilient by design: it never raises on unrecognized tokens
          and always completes the scan.

        :param dtstr `<'str'>`: The original datetime string (used by tokenizer).
        :returns `<'bool'>`: Always True.
        """
        # Reset tokens and (dtstr) position / length
        self._tokens = _timelex(dtstr, self._pos, self._length)  # type: ignore
        self._length = list_len(self._tokens)
        if self._length == 0:
            return True  # exit: no valid tokens

        # Position start at -1:
        # '_get_next_token' will advance position
        self._pos = -1

        # Parse tokens
        while True:
            # Get next token
            token: str = self._get_next_token()
            if token is None:
                break
            # . control or space character
            elif utils.is_str_ascii_ctl_or_space(token):
                pass
            # . weekday token
            elif self._parse_token_weekday(token):
                pass
            # . am/pm token
            elif self._parse_token_ampm(token):
                pass
            # . tzname token
            elif self._parse_token_tzname(token):
                pass
            # . tzoffset token
            elif self._parse_token_tzoffset(token):
                pass

        # Success
        self._tokens = None
        return True

    # Timelex tokens -----------------------------------------------------------------------
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _process_timelex_tokens(self, dtstr: str) -> cython.bint:
        """(internal) Tokenize the input `dtstr` and parse tokens with heuristic handlers `<'bool'>`.

        Tokenizes the substring of `dtstr` starting at the current parser
        position (`self._pos`) via `_timelex`, then scans left→right, invoking
        specialized handlers for each token:
        1) Numeric tokens          → `_parse_token_numeric`
        2) Month names             → `_parse_token_month`
        3) ISO week fragments      → `_parse_iso_week`
        4) Weekday names           → `_parse_token_weekday`
        5) AM/PM flags             → `_parse_token_ampm`
        6) Timezone names          → `_parse_token_tzname`
        7) Timezone offsets (+/-)  → `_parse_token_tzoffset`

        ## Notes
        - The `self._pos` is then updated to track the index within `self._tokens`
          (from `_timelex`), contrary to ISO parsers which track positions in the
          original `dtstr` string.
        - Handlers may consume additional lookahead tokens and advance `self._pos`
          accordingly (e.g., to skip separators and multi-part patterns). The main
          loop then continues from the updated position. Unrecognized non-space
          tokens are tolerated and skipped.
        - This routine is resilient by design: it never raises on unrecognized tokens
          and always completes the scan.

        :param dtstr `<'str'>`: The original datetime string (used by tokenizer).
        :returns `<'bool'>`: Always True on completion.
        """
        # Reset tokens and (dtstr) position / length
        self._tokens = _timelex(dtstr, self._pos, self._length)  # type: ignore
        self._length = list_len(self._tokens)
        if self._length == 0:
            return True  # exit: no valid tokens

        # Position start at -1:
        # '_get_next_token' will advance position
        self._pos = -1

        # Parse tokens
        while True:
            # Get next token
            token: str = self._get_next_token()
            if token is None:
                break
            # . control or space character
            elif utils.is_str_ascii_ctl_or_space(token):
                pass
            # . numeric token
            elif self._parse_token_numeric(token):
                pass
            # . month token
            elif self._parse_token_month(token):
                pass
            # . iso week
            elif self._parse_iso_week(token):
                pass
            # . weekday token
            elif self._parse_token_weekday(token):
                pass
            # . am/pm token
            elif self._parse_token_ampm(token):
                pass
            # . tzname token
            elif self._parse_token_tzname(token):
                pass
            # . tzoffset token
            elif self._parse_token_tzoffset(token):
                pass

        # Success
        self._tokens = None
        return True

    # . parser - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_token_numeric(self, token: str) -> cython.bint:
        """(internal) Parse a `numeric` token and update the parser `Result` `<'bool'>`.

        This method recognizes numeric tokens (integers or decimals) and tries to
        interpret them as compact date/time fields, or as fragments of a larger
        date/time expression when combined with neighboring tokens (e.g., separators,
        HMS/AMPM flags). It may set fields on `self._res` and may advance `self._pos`
        to consume additional look-ahead tokens when a complete pattern is matched.

        :param token `<'str'>`: The current token to parse.
        :returns `<'bool'>`: The process result.

            - `False` only if `token` is `NOT` numeric (integer or decimal only), signaling
              that other handlers should try this token.
            - `True` in all other cases, including when no fields were ultimately set and/or
              the token was effectively skipped (the numeric handler has decided there is
              nothing more to do for this token).

        ## Notes
        - This function is intentionally permissive: once a token is recognized as numeric,
          it returns `True` even if it ultimately doesn't assign any fields. This prevents
          re-processing by other handlers that do not accept numeric tokens.
        - Y/M/D pushed without roles are `unlabeled` on purpose; final disambiguation
          happens later in the resolver based on context/preferences.
        """
        # Validate if is a numeric token
        token_len: cython.Py_ssize_t = str_len(token)
        token_kind: cython.int = utils.parse_numeric_kind(token, token_len)
        if token_kind == 0:
            return False  # exit: not numeric token

        # Pure Integer - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        if token_kind == 1:
            # . (Y/M/D)HH[MM]
            if (
                token_len in (2, 4)  # HH or HHMM
                and not self._res.is_hour_set()  # hour not set
                and self._res.ymd_slots_filled() == 3  # Y/M/D recorded
                and (
                    not self._has_token(1)  # no more tokens
                    or (
                        # next token is not time-field separator
                        not utils.is_str_time_sep(self._get_token1())
                        # next token is not H/M/S flag
                        and not self._cfg.is_hms(self._get_token1())
                    )
                )
            ):
                # . (Y/M/D)[HH]
                self._res.hour = utils.parse_isohour(token, 0, token_len)
                if token_len == 4:
                    # . (Y/M/D)HH[MM]
                    self._res.minute = utils.parse_isominute(token, 2, token_len)
                return True  # exit

            # . YYMMDD / HHMMSS
            if token_len == 6:
                # . [YYMMDD] (ambiguous Y/M/D)
                if self._res.ymd_slots_filled() == 0:
                    self._res.set_ymd_int(
                        0, utils.slice_to_uint(token, 0, 2, token_len)
                    )
                    self._res.set_ymd_int(
                        0, utils.slice_to_uint(token, 2, 2, token_len)
                    )
                    self._res.set_ymd_int(
                        0, utils.slice_to_uint(token, 4, 2, token_len)
                    )
                # . [HHMMSS]
                else:
                    self._res.hour = utils.parse_isohour(token, 0, token_len)
                    self._res.minute = utils.parse_isominute(token, 2, token_len)
                    self._res.second = utils.parse_isosecond(token, 4, token_len)
                return True  # exit

            # . YYYYMMDD[HHMM[SS]]
            if token_len in (8, 10, 12, 14):
                # . [YYYYMMDD] (ambiguous M/D)
                self._res.set_ymd_int(1, utils.slice_to_uint(token, 0, 4, token_len))
                self._res.set_ymd_int(0, utils.slice_to_uint(token, 4, 2, token_len))
                self._res.set_ymd_int(0, utils.slice_to_uint(token, 6, 2, token_len))
                # . YYYYMMDD[HH]
                if token_len > 8:
                    self._res.hour = utils.parse_isohour(token, 8, token_len)
                    # . YYYYMMDDHH[MM]
                    if token_len > 10:
                        self._res.minute = utils.parse_isominute(token, 10, token_len)
                        # . YYYYMMDDHHMM[SS]
                        if token_len > 12:
                            self._res.second = utils.parse_isosecond(
                                token, 12, token_len
                            )
                return True  # exit

            # Next token exists
            if self._has_token(1):
                token1: str = self._get_token1()
                # . HH:[MM[:SS[.ss]]]]
                if (
                    # token(1) must be time separator
                    utils.is_str_time_sep(token1)
                    # try set hour: token(0)
                    and self._set_hour_by_token(token, token_len, token_kind)
                ):
                    # token(0) is hour
                    # try set minute: token(2)
                    if not self._set_minute_by_token(self._get_token(2)):
                        # token(2) is not minute
                        self._pos += 1  # skip token(1)
                        return True  # exit

                    # token(2) is minute / token(4) could be second
                    if not (
                        # token(3) must be time separator
                        utils.is_str_time_sep(self._get_token(3))
                        # try set second: token(4)
                        and self._set_second_by_token(self._get_token(4))
                    ):
                        # token(4) is not second
                        self._pos += 2  # skip token(1..2)
                        return True  # exit

                    # all H/M/S are set successfully
                    self._pos += 4  # skip token(1..4)
                    return True  # exit

                # . YY-[MM-DD] | YY/[MM/DD] | YY.[MM.DD] (ambiguous)
                if (
                    # token(1) must be date separator
                    utils.is_str_date_sep(token1)
                    # try set 1st Y/M/D: token(0)
                    and self._set_ymd_by_token(0, token, token_len, token_kind)
                ):
                    # token(0) is Y/M/D
                    # try set 2nd Y/M/D: token(2)
                    if not self._set_ymd_by_token(0, self._get_token(2)):
                        # token(2) is not Y/M/D
                        self._pos += 1  # skip token(1)
                        return True

                    # token(2) is Y/M/D / token(4) could be Y/M/D
                    if not (
                        # token(3) must be date separator
                        utils.is_str_date_sep(self._get_token(3))
                        # try set 3rd Y/M/D: token(4)
                        and self._set_ymd_by_token(0, self._get_token(4))
                    ):
                        # token(4) is not Y/M/D
                        self._pos += 2  # skip token(1..2)
                        return True  # exit

                    # all Y/M/D are set successfully
                    self._pos += 4  # skip token(1..4)
                    return True  # exit

        # Pure Decimal - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        else:
            # . HHMMSS.[fff]
            if token_len > 6 and utils.is_dot(str_read(token, 6)):
                # . [HHMMSS]
                self._res.hour = utils.parse_isohour(token, 0, token_len)
                self._res.minute = utils.parse_isominute(token, 2, token_len)
                self._res.second = utils.parse_isosecond(token, 4, token_len)
                # . [fff]
                if token_len > 7:
                    self._res.microsecond = utils.parse_isofraction(token, 7, token_len)
                return True  # exit

        # Integer or Decimal - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Next token exists
        if self._has_token(1):
            token1: str = self._get_token1()
            # . HMS with trailing H/M/S flag: [12]h
            flag: cython.int = self._cfg.get_hms(token1)
            if flag != -1:
                # There is a H/M/S flag (e.g: 'h', 'm', 's') trailing the token.
                # We assign the current token to the indicated H/M/S field.
                if self._set_hms_by_token(flag, token, token_len, token_kind):
                    self._pos += 1  # skip token(1)
                    return True

            # . HMS with trailing AM/PM flag: [12]am
            flag: cython.int = self._cfg.get_ampm(token1)
            if flag != -1:
                # There is an AM/PM flag (e.g: 'am', 'pm') trailing the token.
                # We assign the current token to hour and adjust by AM/PM flag.
                if self._set_hour_by_token(token, token_len, token_kind):
                    self._res.hour = self._adjust_hour_by_ampm(self._res.hour, flag)
                    self._pos += 1  # skip token(1)
                    return True  # exit

        # . HMS with preceding H/M/S flag: h[04]
        if self._has_token(-1):
            flag: cython.int = self._cfg.get_hms(self._get_token(-1))
            if flag in (0, 1):  # 'h' or 'm'
                # There is a H/M/S flag (e.g: 'h', 'm') preceding the token.
                # Since the forward case was not hit, there is no flag trailing
                # this token. We assign a lower resolution flag to the current
                # token, if the flag is not second: (h -> m) or (m -> s).
                if self._set_hms_by_token(flag + 1, token, token_len, token_kind):
                    return True

        # "hour AM" or YY|MM|DD (ambiguous)
        if not self._has_token(1) or self._cfg.is_jump(self._get_token1()):
            flag: cython.int = self._cfg.get_ampm(self._get_token(2))
            # . [12] AM
            if flag != -1:
                # There is an AM/PM flag (e.g: 'am', 'pm') after a jump token.
                # We assign the current token to hour and adjust by AM/PM flag.
                if self._set_hour_by_token(token, token_len, token_kind):
                    self._res.hour = self._adjust_hour_by_ampm(self._res.hour, flag)
                    self._pos += 2  # skip token(1..2)
                    return True  # exit
            # . YY|MM|DD (ambiguous)
            elif self._set_ymd_by_token(0, token, token_len, token_kind):
                self._pos += 1  # skip token(1)
                return True  # exit

        # Integer: last resort
        if token_kind == 1:
            # Could be day / day-of-year
            if token_len <= 3:
                value: cython.int = utils.slice_to_uint(token, 0, token_len, token_len)
                if self._res.could_be_day(value) or self._res.could_be_doy(value):
                    self._res.set_ymd_int(0, value)
                    return True  # exit

            # Could be year
            if token_len == 4 and not self._res.is_year_set():
                value: cython.int = utils.slice_to_uint(token, 0, token_len, token_len)
                self._res.set_ymd_int(1, value)
                return True  # exit

        # We reach the end and the numeric token is not processed.
        # But since the other handlers do not accept any numeric
        # tokens, we just return True to skip this token.
        return True

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_token_month(self, token: str) -> cython.bint:
        """(internal) Parse a `month` token and update the parser `Result` `<'bool'>`.

        Attempts to interpret `token` as a month name/abbreviation using the current
        `Configs`. On success, writes the month into the `Result` and (when the
        trailing tokens match supported patterns) also resolves adjacent Y/M/D
        components and advances the parser position.

        :param token `<'str'>`: The current token to parse.
        :returns `<'bool'>`: The process result.

            - `False` if the month is already set or `token` cannot be recognized as month.
            - `True` otherwise (including when the month was recognized but no further
               components could be resolved and the token is simply consumed).
        """
        # Month already set
        if self._res.is_month_set():
            return False  # exit: skip

        # Validate month token
        mm: cython.int = self._cfg.get_month(token)
        if mm == -1:
            return False  # exit: not month token
        if not self._res.set_ymd_int(2, mm):
            #: This token is a month token. Since the `Configs`
            #: guards against conflicting keywords in other
            #: namespaces, it cannot be `weekday` or `hms`, etc.
            return True  # exit: skip token

        # Not enough tokens for year & day
        token2: str = self._get_token(2)
        if token2 is None:
            return True  # exit: MM

        # Jan[-]01: token(1) is date separator
        token1: str = self._get_token1()
        if utils.is_str_date_sep(token1):
            # try set 2nd Y/M/D: token(2)
            if not self._set_ymd_by_token(0, token2):
                # token(2) is not Y/M/D
                return True  # exit: MM

            # token(2) is Y/M/D / token(4) could be Y/M/D
            if not (
                # token(3) must be date separator
                utils.is_str_date_sep(self._get_token(3))
                # try set 3rd Y/M/D: token(4)
                and self._set_ymd_by_token(0, self._get_token(4))
            ):
                # token(4) is not Y/M/D
                self._pos += 2  # skip token(1..2)
                return True  # exit: MM-DD / MM-YYYY

            # all Y/M/D are set successfully
            self._pos += 4  # skip token(1..4)
            return True  # exit: MM-DD-YYYY

        # Jan[, ]2000
        if (
            # token(1) is comma
            utils.is_str_comma(token1)
            # token(2) is space
            and utils.is_str_ascii_ctl_or_space(token2)
            # try set year: token(3)
            and self._set_ymd_by_token(1, self._get_token(3))
        ):
            # token(3) is year
            self._pos += 3  # skip token(1..3)
            return True  # exit: MM, YYYY

        # Jan[ of ]2000
        if (
            # token(1) is space
            utils.is_str_ascii_ctl_or_space(token1)
            # token(3) is space
            and utils.is_str_ascii_ctl_or_space(self._get_token(3))
            # token(2) is pertain
            and self._cfg.is_pertain(token2)
            # try set year: token(4)
            and self._set_ymd_by_token(1, self._get_token(4))
        ):
            # token(4) is year
            self._pos += 4  # skip token(1..4)
            return True  # exit: MM of YYYY

        # End of process
        return True  # exit: MM

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_iso_week(self, token: str) -> cython.bint:
        """(internal) Parse an ISO week-day fragment and update the parser `Result` `<'bool'>`.

        Attempts to interpret the current token and adjacents as an ISO week-date.
        On success, resolves the (month, day) from (year, week, weekday), writes
        into the Result and advances the parser position.

        ## Preconditions
        - Result has YEAR set, and MONTH/DAY are not yet set.
        - The current token is the ISO week marker ('W' / 'w').

        ## Patterns
        - 'W' + 'ww'        (e.g., W05)     → defaults weekday to 1 (Monday)
        - 'W' + 'ww' + '-D' (e.g., W05-3)   → explicit weekday 1..7

        :param token `<'str'>`: The current token to parse.
        :returns `<'bool'>`: The process result.

            - `False` if patterns are not matched, tokens are malformed,
              or values are out of range.
            - `True` otherwise (including when weekday is absent or invalid
              and Monday is assumed).
        """
        # Validate iso week
        if (
            # year not set
            not self._res.is_year_set()
            # month is set
            or self._res.is_month_set()
            # day is set
            or self._res.is_day_set()
            # token(0) is not 'W' or 'w'
            or not utils.is_str_isoweek_sep(token)
        ):
            return False  # exit: not matched

        # W[52]: token(1) must be week number
        token1: str = self._get_token1()
        if token1 is None:
            return False  # exit: invalid
        token1_len: cython.Py_ssize_t = str_len(token1)
        if token1_len != 2:
            return False  # exit: invalid
        week: cython.int = utils.parse_isoweek(token1, 0, 2)
        if week == -1:
            return False  # exit: invalid

        # W52[-7]: token(3) could be weekday
        wkd: cython.int = 1
        token3: str = self._get_token(3)
        if (
            # has token(3)
            token3 is not None
            # token(3) must be single digit
            and str_len(token3) == 1
            # token(2) must be date separator
            and utils.is_str_date_sep(self._get_token(2))
        ):
            num: cython.int = utils.parse_isoweekday(token3, 0, 1)
            if num != -1:
                wkd = num  # Www-D
                self._pos += 2  # skip token(2..3)
        # else: Www-1; defaults to 1 (Monday)

        # Set date by ISO week date
        year: cython.int = self._res._ymd[self._res._yidx]
        _ymd = utils.ymd_fr_iso(year, week, wkd)
        self._res.set_ymd_int(2, _ymd.month)
        self._res.set_ymd_int(3, _ymd.day)
        self._pos += 1  # skip token(1)
        return True  # exit: Www[-D]

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_token_weekday(self, token: str) -> cython.bint:
        """(internal) Parse a `weekday` token and update the parser `Result` `<'bool'>`.

        Attempts to interpret `token` as a weekday name/abbreviation using the
        current `Configs`. On success, writes the weekday into the `Result` and
        advances the parser position.

        :param token `<'str'>`: The current token to parse.
        :returns `<'bool'>`: The process result.

            - `False` if the weekday is already set or `token` cannot be recognized as weekday.
            - `True` otherwise (when the weekday was recognized and set to Result).
        """
        # Weekday already set
        if self._res.is_weekday_set():
            return False  # exit: skip

        # Validate weekday token
        wkd: cython.int = self._cfg.get_weekday(token)
        if wkd == -1:
            return False  # exit: not weekday token

        # Set weekday
        self._res.weekday = wkd
        return True

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_token_ampm(self, token: str) -> cython.bint:
        """(internal) Parse an `AM/PM` flag token and apply it to the current hour `<'bool'>`.

        Attempts to interpret `token` as an AM/PM designator using the current `Config`.
        On success, records the AM/PM flag on the result and adjusts the already-parsed
        hour in-place (e.g., `12 am → 0`, `1 pm → 13`).

        :param token `<'str'>`: The current token to parse.
        :returns `<'bool'>`: The process result.
            - `False` if AM/PM was already set, the hour is missing / not in 12-hour
              domain, or `token` is not an AM/PM designator.
            - `True` otherwise (token is recognized as AM/PM flag and the hour is
              adjusted accordingly).
        """
        # AM/PM flag already set
        if self._res.is_ampm_set():
            return False  # exit

        # Missing hour / Not a 12 hour clock
        hour: cython.int = self._res.hour
        if not 0 <= hour <= 12:
            return False  # exit

        # Validate AM/PM flag token
        flag: cython.int = self._cfg.get_ampm(token)
        if flag == -1:
            return False  # exit: not AM/PM flag token
        self._res.ampm = flag

        # Adjust hour according to AM/PM flag
        self._res.hour = self._adjust_hour_by_ampm(hour, flag)
        return True  # exit

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_token_tzname(self, token: str) -> cython.bint:
        """(internal) Parse a timezone *name/alias* token and update the Result `<'bool'>`.

        Attempts to interpret `token` as a timezone `name` (e.g., `UTC`, `GMT`,
        `CET`, `BRST`) using the current `Config`.. On success, sets `tzoffset`
        from the configuration mapping (or `0` for UTC aliases), optionally
        performs POSIX-style flip for UTC aliases.

        enables a subsequent numeric offset to be applied, and returns `True`. Otherwise returns `False`.

        :param token `<'str'>`: The current token to parse.
        :returns `<'bool'>`: The process result.
            - `True` if `token` is a recognized as timezone name/alias and
              `tzoffset` was updated.
            - `False` if timezone parsing is disabled, a tzoffset is already finalized,
              or `token` is not a valid/known timezone name.

        ## POSIX-style flip
        - If the pattern `UTC/GMT/Z` followed by `+/-` and a 1..4 digit token exists
          (e.g., `UTC + 3`, `GMT - 0230`), the sign token is `flipped` in the token
          list so that the subsequent tz-offset parser interprets it as a standard
          “UTC±HH[MM]” offset.
        - Non-UTC names do `not` flip the sign (e.g., `CET+03` means CET plus 3 hours
          relative to UTC; the numeric offset will be `added` to the base CET offset).
        - Unknown names are rejected via the sentinel `-100_000` returned by the mapping.
        """
        # Check if need to parse timezone name
        if (
            # ignore timezone
            self._ignoretz
            # tzoffset already set
            or self._res.is_tzoffset_set()
        ):
            return False  # exit: no need

        # Validate timezone token
        # . utc timezone alias
        is_utc: cython.bint = self._cfg.is_utc(token)
        if is_utc:
            self._res.tzoffset = 0
        # . timezone name must be ASCCI alpha
        elif not utils.is_str_ascii_letters(token):
            return False  # exit: invalid
        # . offset from timezone mapping
        else:
            offset: cython.int = self._cfg.get_tz_offset(token)
            if offset == utils.NULL_TZOFFSET:
                return False  # exit: not timezone name
            self._res.tzoffset = offset

        #: For UTC/GMT/Z followed by a numeric offset (e.g., 'UTC + 3' or 'GMT - 0230'):
        #: POSIX semantics say “my time ±X is UTC”, so flip the following sign token
        #: to make the numeric tzoffset parser compute the correct absolute offset.
        if is_utc and self._has_token(2):  # token(2) must exists
            token1: str = self._get_token1()
            token2: str = self._get_token(2)
            token2_len: cython.Py_ssize_t = str_len(token2)
            if (
                # . token(2) must be 1, 2 or 4 digits
                token2_len in (1, 2, 4)
                and utils.is_str_ascii_digits(token2, token2_len)
                # . token(1) must be a single char
                and str_len(token1) == 1
            ):
                ch: cython.Py_UCS4 = str_read(token1, 0)
                if utils.is_plus_sign(ch):
                    #: we advance position to token(1) and reset
                    #: peeks before calling tzoffset parser, then
                    #: flip token(1) from '+' to '-'
                    self._pos += 1
                    self._reset_token_peeks()
                    return self._parse_token_tzoffset("-")  # True
                if utils.is_minus_sign(ch):
                    #: we advance position to token(1) and reset
                    #: peeks before calling tzoffset parser, then
                    #: flip token(1) from '-' to '+'.
                    self._pos += 1
                    self._reset_token_peeks()
                    return self._parse_token_tzoffset("+")  # True

        #: For non-UTC names (e.g., 'CET + 02:00'): do not flip — numeric offset
        #: will be added to the base zone offset (additive semantics).
        self._res.tzoffset_finalized = False
        return True  # exit: success

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _parse_token_tzoffset(self, token: str) -> cython.bint:
        """(internal) Parse a timezone `numeric offset` fragment and update the Result `<'bool'>`.

        Interprets a sign token (`'+'`/`'-'`) followed by one or two numeric
        tokens as a UTC offset. Supports:
        - `±HHMM`     → sign + 4 digits in the `next` token (e.g. `+ 0530`)
        - `±HH[:MM]?` → sign + 1-2 digits hour, optional `:` and 1-2 digit minute
                        in subsequent tokens (e.g. `- 5 : 30`, `+ 02`)

        This method must run even when `ignoretz=True` so that time parsing can
        continue correctly (the tokens are still consumed/validated). When
        `ignoretz=True`, the computed offset is simply not written back.

        :param token `<'str'>`: The current token to parse.
        :returns `<'bool'>`: The process result.
            - `False` if the pattern does not match or a `tzoffset` is
              already set and finalized.
            - `True` otherwise (matched tokens are consumed as needed).

        ## Notes
        - Sign flipping for UTC-like names (e.g., `UTC + 3`) should be handled
          earlier in `_parse_token_tzname`; this method simply parses what it sees.
        - `ignoretz=True` only suppresses `writing` the offset; token advancement
          and validation still occur for downstream parsers.
        """

        # Check if need to parse timezone offset
        if self._res.is_tzoffset_set() and self._res.tzoffset_finalized:
            return False

        #: Cannot bypass the following process even if 'ignoretz=True'
        #: Timezone offset tokens (if exists) must be skipped to ensure
        #: H/M/S and AM/PM are parsed properly.

        # token(0): must be a single '+' or '-'
        if str_len(token) != 1:
            return False  # exit: invalid
        ch: cython.Py_UCS4 = str_read(token, 0)
        if utils.is_plus_sign(ch):
            sign: cython.int = 1
        elif utils.is_minus_sign(ch):
            sign: cython.int = -1
        else:
            return False  # exit: invalid

        # token(1): +[HH] / +[HHMM]
        token1: str = self._get_token1()
        if token1 is None:
            return False  # exit: not exists
        token1_len: cython.Py_ssize_t = str_len(token1)
        # token(1) must all digits
        if not utils.is_str_ascii_digits(token1, token1_len):
            return False  # exit: invalid

        # Case: +[HHMM] (exactly 4 digits)
        if token1_len == 4:
            hh: cython.int = utils.parse_isohour(token1, 0, token1_len)
            mi: cython.int = utils.parse_isominute(token1, 2, token1_len)
            self._pos += 1  # skip token(1)
        # Case: +[HH[:MM]] ((1–2 digit hour, optional ':' + MM)
        elif 1 <= token1_len <= 2:
            hh: cython.int = utils.slice_to_uint(token1, 0, token1_len, token1_len)
            mi: cython.int = 0
            # +HH[:MM]
            if self._has_token(3) and utils.is_str_time_sep(self._get_token(2)):
                token3: str = self._get_token(3)
                token3_len: cython.Py_ssize_t = str_len(token3)
                if (
                    # token(3) should be max 2 digits
                    token3_len <= 2
                    # token(3) must be all digits
                    and utils.is_str_ascii_digits(token3, token3_len)
                ):
                    mi = utils.slice_to_uint(token3, 0, token3_len, token3_len)
                    self._pos += 2  # skip token(2..3)
            self._pos += 1  # skip token(1)
        # Otherwise: unsupported
        else:
            return False  # exit: invalid

        # Compute UTC offset: when timezone is not ignored
        if not self._ignoretz:
            offset: cython.int = sign * (hh * 3_600 + mi * 60)
            if not -86_400 <= offset <= 86_400:
                raise ValueError(
                    "Invalid UTC offset '%d' in seconds, "
                    "must be between -86,400 and 86,400." % (offset)
                )
            if self._res.is_tzoffset_set():
                self._res.tzoffset += offset  # add to base
            else:
                self._res.tzoffset = offset  # set base
            self._res.tzoffset_finalized = True  # prevent further changes
        return True  # exit: success

    # . tokens - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def _has_token(self, offset: cython.Py_ssize_t) -> cython.bint:
        """(internal) Check whether a token `exists` at a position relative to the current index `<'bool'>`.

        Interprets `offset` relative to the current token cursor `self._pos` and
        returns whether that resulting index is within the valid token range.
        - `offset == 0` → current token
        - `offset > 0`  → lookahead (`+1` = next token, etc.)
        - `offset < 0`  → lookbehind (`-1` = previous token, etc.)

        :param offset `<'int'>`: Relative offset from the current token index (`self._pos`).
        :return `<'bool'>`: True if the token exists, otherwise False.

        ## Notes
        - This method does `NOT` advance the internal cursor; it simply checks
          if the token at the specified relative position exists.
        """
        return 0 <= (self._pos + offset) < self._length

    @cython.cfunc
    @cython.inline(True)
    def _get_token(self, offset: cython.Py_ssize_t) -> str:
        """(internal) Return the token at a position relative to the current index `<'str/None'>`.

        Interprets `offset` relative to the current token cursor `self._pos` and
        retrieves the token at that index.
        - `offset == 0` → current token
        - `offset > 0`  → lookahead (`+1` = next token, etc.)
        - `offset < 0`  → lookbehind (`-1` = previous token, etc.)

        :param offset `<'int'>`: Relative offset from the current token index (`self._pos`).
        :returns `<'str/None'>`: The token string at `self._pos + offset`, or `None` if out of bound.

        ## Notes
        - This method does `NOT` advance the internal cursor; it simply reads
          the token at the specified relative position.
        """
        idx: cython.Py_ssize_t = self._pos + offset
        if not 0 <= idx < self._length:
            return None
        return cython.cast(str, list_getitem(self._tokens, idx))

    @cython.cfunc
    @cython.inline(True)
    def _get_token1(self) -> str:
        """(internal) Return the `next` token (at `self._pos + 1`) `<'str/None'>`.

        This is a cached “peek” helper. On first call at the current cursor position,
        it fetches `self._get_token(1)` and stores it in `self._token1`. Subsequent
        calls at the same position return the cached value. The cache must be invalidated
        (set to `None`) whenever `self._pos` changes.

        :returns `<'str/None'>`: The token string immediately after the current one,
            or `None` if the next token does not exists.

        ## Notes
        - This method does `NOT` advance the internal cursor; it simply reads
          the next token relative to the current position.
        """
        if self._token1 is None:
            self._token1 = self._get_token(1)
        return self._token1

    @cython.cfunc
    @cython.inline(True)
    def _get_next_token(self) -> str:
        """(internal) Advance to and return the next token `<'str/None'>`.

        Increments the internal cursor (`self._pos += 1`) and returns the token
        at the new position. If the advanced index exceeds the token list length,
        returns `None` to signal EOF.

        :returns `<'str/None'>`: The next token string,
            or `None` if there are no more tokens.

        ## Notes
        - Intended usage is to initialize `self._pos = -1` before a read
          loop and call this at the top of each iteration.
        - If additional peek caches (e.g., `_token2`) are introduced, they
          should also be reset here.
        """
        # Reset peeks
        self._reset_token_peeks()

        # Get next token
        self._pos += 1
        idx: cython.Py_ssize_t = self._pos
        if idx >= self._length:
            return None
        return cython.cast(str, list_getitem(self._tokens, idx))

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(check=False)
    def _reset_token_peeks(self) -> cython.bint:
        """(internal) Reset cached token peeks.

        This method invalidates any cached token peeks (e.g., `self._token1`)
        so that subsequent calls to the peek methods will re-fetch from the
        token list.

        ## Notes
        - This method should be called whenever the internal cursor
          (`self._pos`) is changed manually or externally.
        """
        self._token1 = None
        return True

    # . setters - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _set_ymd_by_token(
        self,
        flag: cython.int,
        token: str = None,
        token_len: cython.Py_ssize_t = -1,
        token_kind: cython.int = -1,
    ) -> cython.bint:
        """(internal) Try to assign a Y/M/D component from a single token `<'bool'>`.

        Interprets `token` as either:
        - a pure-integer calendar field (year/month/day)
        - a month name/abbr (e.g., "Jan", "September")

        :param flag `<'int'>`: The Y/M/D flag (0=UNKNOWN, 1=YEAR, 2=MONTH, 3=DAY).
            Use 0 when the token is ambiguous (e.g., “12”).
        :param token `<'str/None'>`: The candidate token for Y/M/D component. Defaults to `None`.
        :param token_len `<'int'>`: Optional length of `token`.
            Defaults to `-1` (let the method computes it).
        :param token_kind `<'int'>`: Optional numeric classification of `token`.
            Defaults to `-1` (let the method computes it).

            - 0 = non-numeric (may still be month)
            - 1 = integer
            - 2 = decimal     (rejected)

        :returns `<'bool'>`: True if a Y/M/D component was written to `Result`; False otherwise.
        """
        # Get token length
        if token is None:
            return False
        if token_len <= 0:
            token_len = str_len(token)
        if token_len == 0:
            return False  # exit: invalid

        # Ensure token numeric kind
        if token_kind < 0:
            token_kind = utils.parse_numeric_kind(token, token_len)
        if token_kind == 2:  # Y/M/D token cannot be decimal
            return False  # exit: invalid

        # Integer token
        if token_kind == 1:
            return self._res.set_ymd_str(flag, token, token_len)

        # String: Could be month token
        month: cython.int = self._cfg.get_month(token)
        if month != -1 and not self._cfg.is_jump(token):
            return self._res.set_ymd_int(2, month)

        # Not Y/M/D token
        return False  # exit: invalid

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _set_hms_by_token(
        self,
        flag: cython.int,
        token: str = None,
        token_len: cython.Py_ssize_t = -1,
        token_kind: cython.int = -1,
    ) -> cython.bint:
        """(Internal) Try set the H/M/S from a single `numeric` token `<'bool'>`.

        Thie method routes a single numeric `token` to one of the specialized setters:
        - `flag == 0` → hour   → `_set_hour_by_token(...)`
        - `flag == 1` → minute → `_set_minute_by_token(...)`
        - `flag == 2` → second → `_set_second_by_token(...)`

        :param flag `<'int'>`: H/M/S flag (0=hour, 1=minute, 2=second).
            Any other value is invalid.
        :param token `<'str/None'>`: The candidate token for H/M/S. Defaults to `None`.
        :param token_len `<'int'>`: Optional length of `token`.
            Defaults to `-1` (let the method computes it).
        :param token_kind `<'int'>`: Optional numeric classification of `token`.
            Defaults to `-1` (let the method computes it).

            - 0 = non-numeric (rejected)
            - 1 = integer
            - 2 = decimal

        :returns `<'bool'>`: True if the designated field was set successfully; False otherwise.
        """
        # Hour flag
        if flag == 0:
            return self._set_hour_by_token(token, token_len, token_kind)
        # Minute flag
        elif flag == 1:
            return self._set_minute_by_token(token, token_len, token_kind)
        # Second flag
        elif flag == 2:
            return self._set_second_by_token(token, token_len, token_kind)
        # Invalid flag
        else:
            return False

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _set_hour_by_token(
        self,
        token: str = None,
        token_len: cython.Py_ssize_t = -1,
        token_kind: cython.int = -1,
    ) -> cython.bint:
        """(internal) Try set the hour (and optionally minute) from a single `numeric` token `<'bool'>`.

        Accepts `token` either as:
        - `Integer hours` (e.g., `'9'`, `'23'`)      → sets `hour`
        - `Decimal hours` (e.g., `'14.5'`, `'7.25'`) → sets `hour` to the integer part
          and computes `minute = round(fraction * 60)` (clamp to 59).

        :param token `<'str/None'>`: The candidate token for hour. Defaults to `None`.
        :param token_len `<'int'>`: Optional length of `token`.
            Defaults to `-1` (let the method computes it).
        :param token_kind `<'int'>`: Optional numeric classification of `token`.
            Defaults to `-1` (let the method computes it).

            - 0 = non-numeric (rejected)
            - 1 = integer
            - 2 = decimal

        :returns `<'bool'>`: True if `hour` (and possibly `minute`) was set successfully; False otherwise.
        """
        # Get token length
        if token is None:
            return False
        if token_len <= 0:
            token_len = str_len(token)
        if token_len == 0:
            return False  # exit: invalid

        # Ensure is numeric token
        if token_kind < 0:
            token_kind = utils.parse_numeric_kind(token, token_len)
        if token_kind == 0:
            return False  # exit: invalid

        # Integer token
        if token_kind == 1:
            hh: cython.int = utils.slice_to_uint(token, 0, token_len, token_len)
            if not 0 <= hh < 24:
                return False  # exit: invalid
            self._res.hour = hh
            return True  # exit: success

        # Decimal token
        frac: cython.double = utils.slice_to_ufloat(token, 0, token_len, token_len)
        hh: cython.int = int(frac)
        if not 0 <= hh < 24:
            return False  # exit: invalid
        self._res.hour = hh
        # fraction to minute
        r: cython.double = frac % 1
        if r:
            self._res.minute = min(math.lround(r * 60), 59)
        return True  # exit: success

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _set_minute_by_token(
        self,
        token: str = None,
        token_len: cython.Py_ssize_t = -1,
        token_kind: cython.int = -1,
    ) -> cython.bint:
        """(internal) Try set the minute (and optionally second) from a single `numeric` token `<'bool'>`.

        Accepts `token` either as:
        - `Integer minutes` (e.g., `'7'`, `'59'`)      → sets `minute`
        - `Decimal minutes` (e.g., `'12.5'`, `'3.25'`) → sets `minute to the integer part
          and computes `second = round(fraction * 60)` (clamp to 59).

        :param token `<'str/None'>`: The candidate token for minute. Defaults to `None`.
        :param token_len `<'int'>`: Optional length of `token`.
            Defaults to `-1` (let the method computes it).
        :param token_kind `<'int'>`: Optional numeric classification of `token`.
            Defaults to `-1` (let the method computes it).

            - 0 = non-numeric (rejected)
            - 1 = integer
            - 2 = decimal

        :returns `<'bool'>`: True if `minute` (and possibly `second`) was set successfully; False otherwise.
        """
        # Get token length
        if token is None:
            return False
        if token_len <= 0:
            token_len = str_len(token)
        if token_len == 0:
            return False  # exit: invalid

        # Ensure is numeric token
        if token_kind < 0:
            token_kind = utils.parse_numeric_kind(token, token_len)
        if token_kind == 0:
            return False  # exit: invalid

        # Integer token
        if token_kind == 1:
            mi: cython.int = utils.slice_to_uint(token, 0, token_len, token_len)
            if not 0 <= mi < 60:
                return False  # exit: invalid
            self._res.minute = mi
            return True  # exit: success

        # Decimal token
        frac: cython.double = utils.slice_to_ufloat(token, 0, token_len, token_len)
        mi: cython.int = int(frac)
        if not 0 <= mi < 60:
            return False  # exit: invalid
        self._res.minute = mi
        # fraction to second
        r: cython.double = frac % 1
        if r:
            self._res.second = min(math.lround(r * 60), 59)
        return True  # exit: success

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _set_second_by_token(
        self,
        token: str = None,
        token_len: cython.Py_ssize_t = -1,
        token_kind: cython.int = -1,
    ) -> cython.bint:
        """(internal) Try set the `second` (and optionally `microsecond`) from a single numeric token `<'bool'>`.

        Accepts `token` either as:
        - `Integer seconds` (e.g., `'7'`, `'59'`)          → sets `second`
        - `Decimal seconds` (e.g., `'12.5'`, `'3.250001'`) → sets `second` to the integer part
          and `microsecond` to the fraction (up to 6 digits, exceeding are ignored).

        :param token `<'str/None'>`: The candidate token for second. Defaults to `None`.
        :param token_len `<'int'>`: Optional length of `token`.
            Defaults to `-1` (let the method computes it).
        :param token_kind `<'int'>`: Optional numeric classification of `token`.
            Defaults to `-1` (let the method computes it).

            - 0 = non-numeric (rejected)
            - 1 = integer
            - 2 = decimal

        :returns `<'bool'>`: True if `second` (and possibly `microsecond`) was set successfully; False otherwise.
        """
        # Get token length
        if token is None:
            return False
        if token_len <= 0:
            token_len = str_len(token)
        if token_len == 0:
            return False  # exit: invalid

        # Ensure is numeric token
        if token_kind < 0:
            token_kind = utils.parse_numeric_kind(token, token_len)
        if token_kind == 0:
            return False  # exit: invalid

        # Integer token
        if token_kind == 1:
            ss: cython.int = utils.slice_to_uint(token, 0, token_len, token_len)
            if not 0 <= ss < 60:
                return False  # exit: invalid
            self._res.second = ss
            return True  # exit: success

        # Decimal token
        _sf = utils.parse_second_and_fraction(token, 0, token_len)
        if _sf.second == -1:
            return False  # exit: invalid
        self._res.second = _sf.second
        self._res.microsecond = _sf.microsecond
        return True  # exit: success

    @cython.cfunc
    @cython.inline(True)
    @cython.exceptval(-1, check=False)
    def _adjust_hour_by_ampm(self, hour: cython.int, flag: cython.int) -> cython.int:
        """(internal) Adjust `hour` to 24-hour sacle according to an AM/PM flag `<'int'>`.

        :param hour `<'int'>`: The hour value to adjust (0..23).
        :param flag `<'int'>`: AM/PM flag (0=AM, 1=PM).
        :returns `<'int'>`: Hour on a 24-hour scale (0..23).

        ## Mapping
        - `1..11 AM` → unchanged
        - `12 AM`    → `0`
        - `1..11 PM` → `+12`
        - `12 PM`    → unchanged
        - `0 AM/PM`  → unchanged
        """
        if 1 <= hour <= 11:
            if flag == 1:
                hour += 12
            return hour
        elif hour == 12:
            return 0 if flag == 0 else 12
        else:
            return hour

    # Internal
    @cython.cfunc
    @cython.inline(True)
    def _cls(self) -> object:
        """(internal) Access the class object of the current instance `<'type[Parser]'>`."""
        if self.__cls is None:
            self.__cls = self.__class__
        return self.__cls


_DEFAULT_PARSER: Parser = Parser()


# Parse --------------------------------------------------------------------------------------
@cython.ccall
def parse(
    dtstr: str,
    default: object = None,
    yearfirst: object = None,
    dayfirst: object = None,
    ignoretz: cython.bint = True,
    isoformat: cython.bint = True,
    cfg: Configs = None,
    dtclass: object = None,
) -> datetime.datetime:
    """Parse a date/time string into a datetime `<'datetime.datetime'>`.

    This is a convenience wrapper around `Parser.parse()`.
        - When `cfg` is `None` it uses a module-level default parser for speed.
        - Otherwise it constructs a temporary `Parser(cfg)`.

    ## Parsing Strategies
    1) `ISO fast-path` (when `isoformat=True`): attempts an ISO 8601 calendar/ordinal/week
        date plus optional time, fractional seconds, and timezone. If an extra tail remains
        (e.g., AM/PM, weekday, timezone tail), a lightweight ISO-extra pass handles it.
    2) `Heuristic token path` (fallback or when `isoformat=False`): tokenizes the string
        and scans left→right, using specialized handlers for numeric blocks, month/weekday
        names, AM/PM, timezone names, and timezone offsets.

    After parsing, ambiguous Y/M/D fields are resolved using `yearfirst`/`dayfirst` (or the
    configured defaults when they are `None`). Finally, a datetime is built using parsed
    fields plus `default` for any missing calendar components.

    :param dtstr `<'str'>`: The input date/time string.
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
    :param dtclass `<'type[datetime.datetime]/None'>`: Optional custom datetime class. Defaults to `None`.
        If `None` uses python's built-in `datetime.datetime` as the constructor.
    :returns `<'datetime.datetime'>`: The parsed datetime (or subclass if 'dtclass' is specified).
    :raises `<'ParserFailedError'>`: If nothing extractable is found (or ISO parsing
        fails and token scanning yields no fields).
    :raises `<'ParserBuildError'>`: If fields cannot be assembled into a datetime
        (e.g., invalid field combination, unsupported custom class).

    ## Field Construction
    - `Y/M/D`: use parsed values; if missing, copy from `default` (if provided), otherwise raise.
        If `day > 28`, it is clamped to the month's maximum.
    - `Weekday`: if a weekday was parsed and does not match `(Y, M, D)`, the date is shifted by
        the difference so the resulting weekday matches the requested one (within the same week as
        the parsed date).
    - `Time`: unset H/M/S/us default to `0`. AM/PM is applied when present.
    - `Timezone`:
        * If `ignoretz=True`, any parsed timezone info is ignored and a naive datetime
            (`tzinfo=None`) is returned.
        * Otherwise, a timezone-aware datetime is returned if a timezone name/offset was parsed:
            UTC for offset `0`, or a fixed-offset timezone for non-zero offsets.

    ## Ambiguous Y/M/D
    Both `yearfirst` and `dayfirst` control how ambiguous digit tokens are interpreted;
    `yearfirst` has higher priority. When all three are ambiguous (e.g., `01/05/09`):
    - `yearfirst=False & dayfirst=False` → `M/D/Y`  → `2009-01-05`
    - `yearfirst=False & dayfirst=True`  → `D/M/Y`  → `2009-05-01`
    - `yearfirst=True  & dayfirst=False` → `Y/M/D`  → `2001-05-09`
    - `yearfirst=True  & dayfirst=True`  → `Y/D/M`  → `2001-09-05`

    When the year is already known (e.g., `32/01/05`), `dayfirst` alone decides between `Y/M/D`
    vs `Y/D/M`. When only one value is ambiguous, the parser picks the only consistent
    interpretation and ignores the flags.
    """
    # fmt: off
    if cfg is None:
        return _DEFAULT_PARSER.parse(dtstr, default, yearfirst, dayfirst, ignoretz, isoformat, dtclass)
    else:
        return Parser(cfg).parse(dtstr, default, yearfirst, dayfirst, ignoretz, isoformat, dtclass)
    # fmt: on


@cython.ccall
def parse_obj(
    dtobj: object,
    default: object = None,
    yearfirst: object = None,
    dayfirst: object = None,
    ignoretz: cython.bint = True,
    isoformat: cython.bint = True,
    cfg: Configs = None,
    dtclass: object = None,
) -> datetime.datetime:
    """Parse a datetime-like object into a datetime `<'datetime.datetime'>`.

    :param dtobj `<'object'>`: A datetime-like object, supports:

        - `<'str'>`                 → parsed via function `parse()`, honoring `default`, `yearfirst`, `dayfirst`,
                                      `ignoretz`, `isoformat`, `cfg`, and `dtclass`.
        - `<'datetime.datetime'>`   → returns as-is or re-create using optional `dtclass`.
        - `<'datetime.date'>`       → converts to timezone-naive datetime with the same date fields, optionally using `dtclass`.
        - `<'int/float'>`           → interprets as `seconds since Unix epoch` and converts to timezone-naive datetime
                                      (fractional seconds → microseconds).
        - `<'np.datetime64'>`       → converts to timezone-naive datetime; resolution finer than microseconds is truncated.

    :param dtclass `<'type[datetime.datetime]/None'>`: Optional custom datetime class. Defaults to `None`.
        If `None` uses python's built-in `datetime.datetime` as the constructor.

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

    :returns `<'datetime.datetime'>`: The parsed/converted datetime (or subclass if 'dtclass' is specified).
    :raises `<'ParserFailedError'>`: On unsupported input types or any conversion/parsing failed.
    :raises `<'ParserBuildError'>`: If a string parse succeeds but fields cannot be assembled (string input).

    ## Notes
    - Non-string inputs do `NOT` use `default`, `yearfirst`, `dayfirst`, `ignoretz`, `isoformat` or `cfg`.
    """
    # . datetime string
    if isinstance(dtobj, str):
        if not is_str_exact(dtobj):
            dtobj = str(dtobj)
        return parse(
            dtobj, default, yearfirst, dayfirst, ignoretz, isoformat, cfg, dtclass
        )
    try:
        # . datetime.datetime
        if utils.is_dt(dtobj):
            return utils.dt_fr_dt(dtobj, dtclass)
        # . datetime.date
        if utils.is_date(dtobj):
            return utils.dt_fr_date(dtobj, None, dtclass)
        # . numeric
        if isinstance(dtobj, (int, float)):
            return utils.dt_fr_sec(dtobj, None, dtclass)
        # . np.datetime64
        if utils.is_dt64(dtobj):
            return utils.dt64_to_dt(dtobj, None, dtclass)
    except Exception as err:
        errors.raise_parser_failed_error(
            _DEFAULT_PARSER.__cls,
            "Failed to parse '%s' %s." % (dtobj, type(dtobj)),
            err,
        )

    # . invalid
    errors.raise_parser_failed_error(
        _DEFAULT_PARSER.__cls,
        "Failed to parse '%s' %s.\nUnsupported data type." % (dtobj, type(dtobj)),
    )


@cython.ccall
@cython.exceptval(-2, check=False)
def parse_month(
    token: int | str | None,
    cfg: Configs = None,
    raise_error: cython.bint = True,
) -> cython.int:
    """Normalize a month token to month number 1(Jan)..12(Dec) `<'int'>`.

    :param token `<'int/str/None'>`: Month token to normalize, accepts:

        - `None` → returns `-1` (or raises if `raise_error=True`)
        - `int`  → returns the number if in `1..12`; returns `-1` (or raises) otherwise.
                   Special case: `-1` is passed through as a sentinel.
        - `str`  → resolved via `Configs.get_month` (e.g., "Jan", "September",
                   localized aliases). Returns `1..12`, or `-1` (or raises) if unrecognized.

    :param cfg `<'Configs/None'>`: Configs used for string lookup. Defaults to `None`.
        If `None` uses module's default Configs.
    :param raise_error `<'bool'>`: If True, raise `InvalidMonthError` on invalid input;
        if False, return `-1`. Defaults to True.
    :returns `<'int'>`: Month number in `1..12`, or `-1` if invalid and `raise_error=False`.
    :raises `<'InvalidMonthError'>`: On invalid `token` input when `raise_error=True`.
    """
    # <'None'>
    if token is None:
        return -1  # exit

    # `<'int'>`
    if isinstance(token, int):
        num: cython.longlong = token
        if num == -1:
            return -1
        if not (1 <= num <= 12):
            if raise_error:
                raise errors.InvalidMonthError(
                    "Invalid month number '%d', must be between 1(Jan)..12(Dec)." % num
                )
            return -1
        return num  # exit

    # <'str'>
    if isinstance(token, str):
        if cfg is None:
            cfg = _DEFAULT_CONFIGS
        num: cython.longlong = cfg.get_month(token)
        if num == -1 and raise_error:
            raise errors.InvalidMonthError(
                "Invalid month '%s', not recognized." % token
            )
        return num  # exit

    # Invalid
    if raise_error:
        raise errors.InvalidMonthError(
            "Invalid month '%s' %s.\n"
            "Expects integer (1-12) or literal month name." % (token, type(token))
        )
    return -1


@cython.ccall
@cython.exceptval(-2, check=False)
def parse_weekday(
    token: int | str | None,
    cfg: Configs = None,
    raise_error: cython.bint = True,
) -> cython.int:
    """Normalize a weekday token to weekday number 0(Mon)..6(Sun) `<'int'>`.

    :param token `<'int/str/None'>`: Weekday token to normalize, accepts:

        - `None` → returns `-1` (or raises if `raise_error=True`)
        - `int`  → returns the number if in `0..6`; returns `-1` (or raises) otherwise.
                   Special case: `-1` is passed through as a sentinel.
        - `str`  → resolved via `Configs.get_weekday` (e.g., "Mon", "Sunday",
                   localized aliases). Returns `0..6`, or `-1` (or raises) if unrecognized.

    :param cfg `<'Configs/None'>`: Configs used for string lookup. Defaults to `None`.
        If `None` uses module's default Configs.
    :param raise_error `<'bool'>`: If True, raise `InvalidWeekdayError` on invalid input;
        if False, return `-1`. Defaults to True.
    :returns `<'int'>`: Weekday number in `0..6`, or `-1` if invalid and `raise_error=False`.
    :raises `<'InvalidWeekdayError'>`: On invalid `token` input when `raise_error=True`.
    """
    # <'None'>
    if token is None:
        return -1  # exit

    # `<'int'>`
    if isinstance(token, int):
        num: cython.longlong = token
        if num == -1:
            return -1
        if not (0 <= num <= 6):
            if raise_error:
                raise errors.InvalidWeekdayError(
                    "Invalid weekday number '%d', must be between 0(Mon)..6(Sun)." % num
                )
            return -1
        return num  # exit

    # <'str'>
    if isinstance(token, str):
        if cfg is None:
            cfg = _DEFAULT_CONFIGS
        num: cython.longlong = cfg.get_weekday(token)
        if num == -1 and raise_error:
            raise errors.InvalidWeekdayError(
                "Invalid weekday '%s', not recognized." % token
            )
        return num  # exit

    # Invalid
    if raise_error:
        raise errors.InvalidWeekdayError(
            "Invalid weekday '%s' %s.\n"
            "Expects integer (0-6) or literal weekday name." % (token, type(token))
        )
    return -1
