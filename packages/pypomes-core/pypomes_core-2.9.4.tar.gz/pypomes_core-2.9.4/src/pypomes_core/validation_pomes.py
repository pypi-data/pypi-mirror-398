import re
import string
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum, IntEnum, StrEnum, auto
from logging import Logger
from typing import Any, Final, TypeVar

from .datetime_pomes import TZ_LOCAL
from .env_pomes import APP_PREFIX, env_get_str, env_get_enum
from .str_pomes import (
    str_as_list, str_sanitize, str_find_char, str_find_whitespace
)
# define a TypeVar constrained to IntEnum or StrEnum
IntStrEnum = TypeVar("IntStrEnum", bound=IntEnum | StrEnum)


class MsgLang(StrEnum):
    """
    Possible languages for error reporting.
    """
    EN = auto()
    PT = auto()


VALIDATION_MSG_LANGUAGE: Final[MsgLang] = env_get_enum(key=f"{APP_PREFIX}_VALIDATION_MSG_LANGUAGE",
                                                       enum_class=MsgLang,
                                                       def_value=MsgLang.EN)
VALIDATION_MSG_PREFIX: Final[str] = env_get_str(key=f"{APP_PREFIX}_VALIDATION_MSG_PREFIX",
                                                def_value=APP_PREFIX)
CRON_REGEX: Final[re.Pattern] = re.compile(
     r"^"                                                                                   # start of string
     r"((\*|([0-5]?\d)(-([0-5]?\d))?(/\d+)?)(,(\*|([0-5]?\d)(-([0-5]?\d))?(/\d+)?))*)\s+"   # minute
     r"((\*|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(/\d+)?)"
     r"(,(\*|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(/\d+)?))*)\s+"                            # hour
     r"((\*|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(/\d+)?)"
     r"(,(\*|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(/\d+)?))*)\s+"                    # day of month
     r"((\*|(0?[1-9]|1[0-2])(-(0?[1-9]|1[0-2]))?(/\d+)?)"
     r"(,(\*|(0?[1-9]|1[0-2])(-(0?[1-9]|1[0-2]))?(/\d+)?))*)\s+"                            # month
     r"((\*|0-7?(/\d+)?)(,(\*|0-7?(/\d+)?))*)"                                              # day of week
     r"$"                                                                                   # end of string
)
CRON_EMAIL: Final[re.Pattern] = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_value(attr: str,
                   value: str | float | Decimal,
                   min_value: int = None,
                   max_value: int = None,
                   values: list = None,
                   ignore_case: bool = False,
                   required: bool = False) -> str | None:
    """
    Validate *value* according to value, range, or membership in *values*, as specified.

    :param attr: the name of the attribute
    :param value: the value to be validated
    :param min_value: if *value* is a string, specifies its minimum length; otherwise, specifies its minimum value
    :param max_value: if *value* is a string, specifies its maximum length; otherwise, specifies its maximum value
    :param values: if provided, requires *val* to be contained therein
    :param ignore_case: specifies whether to ignore capitalization when handling string values
    :param required:  requires *value* to be specified
    :return: *None* if *value* passes validation, or the corresponding error message otherwise
    """
    # initialize the return variable
    result: str | None = None

    if value is None or value == "":
        if isinstance(required, bool) and required:
            # 121: Required attribute
            result = validate_format_error(121,
                                           f"@{attr}")
    elif isinstance(values, list):
        val: str | float | Decimal = value
        vals: list = values
        if ignore_case:
            val = value.lower() if isinstance(value, str) else value
            vals = [v.lower() if isinstance(v, str) else v for v in values]
        if val not in vals:
            length: int = len(values)
            if length == 1:
                # 149: Invalid value {}: must be {}
                result = validate_format_error(149,
                                               value,
                                               values[0],
                                               f"@{attr}")
            else:
                # 150: Invalid value {}: must be one of {}
                result = validate_format_error(150,
                                               value,
                                               values[:length],
                                               f"@{attr}")
    elif isinstance(value, str):
        length: int = len(value)
        if min_value is not None and max_value == min_value and length != min_value:
            # 146: Invalid value {}: length must be {}
            result = validate_format_error(146,
                                           value,
                                           min_value,
                                           f"@{attr}")
        elif min_value is not None and length < min_value:
            # 147: Invalid value {}: length shorter than {}
            result = validate_format_error(147,
                                           value,
                                           min_value,
                                           f"@{attr}")
        elif max_value is not None and max_value < length:
            # 148: Invalid value {}: length longer than {}
            result = validate_format_error(148,
                                           value,
                                           max_value,
                                           f"@{attr}")
    elif ((min_value is not None and value < min_value) or
          (max_value is not None and value > max_value)):
        if min_value is not None and max_value is not None:
            # 151: Invalid value {}: must be in the range {}
            result = validate_format_error(151,
                                           value,
                                           [min_value, max_value],
                                           f"@{attr}")
        elif min_value is not None:
            # 144: Invalid value {}: must be greater than {}
            result = validate_format_error(144,
                                           value,
                                           min_value,
                                           f"@{attr}")
        else:
            # 143: Invalid value {}: must be less than {}
            result = validate_format_error(143,
                                           value,
                                           max_value,
                                           f"@{attr}")
    return result


def validate_bool(source: dict[str, Any],
                  attr: str,
                  default: bool = None,
                  required: bool = False,
                  errors: list[str] = None,
                  logger: Logger = None) -> bool | None:
    """
    Validate the boolean value associated with *attr* in *source*.

    If provided, this value must be on of:
        - a *bool*
        - the integer *1* or *0*
        - the string *1*, *t*, or *true*, case disregarded
        - the string *0*, *f*, or *false*, case disregarded

    :param source: *dict* containing the value to be validated
    :param attr: the name of the attribute whose value is being validated
    :param default: default value, overrides *required*
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # initialize the return variable
    result: bool | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # retrieve the value
    value = source.get(suffix)

    # validate it
    if value is None or value == "":
        if default is not None:
            value = default
        elif required:
            # 121: Required attribute
            stat = validate_format_error(121,
                                         f"@{attr}")
    elif isinstance(value, str):
        if value.lower() in ["1", "t", "true"]:
            value = True
        elif value.lower() in ["0", "f", "false"]:
            value = False
        else:
            # 152: Invalid value {}: must be type {}
            stat = validate_format_error(152,
                                         value,
                                         "bool",
                                         f"@{attr}")
    # bool is subtype of int
    elif isinstance(value, int) and not isinstance(value, bool):
        if value == 1:
            value = True
        elif value == 0:
            value = False
        else:
            # 152: Invalid value {}: must be type {}
            stat = validate_format_error(152,
                                         value,
                                         "bool",
                                         f"@{attr}")
    elif not isinstance(value, bool):
        # 152: Invalid value {}: must be type {}
        stat = validate_format_error(152,
                                     value,
                                     "bool",
                                     f"@{attr}")
    if stat:
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)
    else:
        result = value

    return result


def validate_int(source: dict[str, Any],
                 attr: str,
                 min_val: int = None,
                 max_val: int = None,
                 values: list[int] = None,
                 default: int = None,
                 required: bool = False,
                 errors: list[str] = None,
                 logger: Logger = None) -> int | None:
    """
    Validate the *int* value associated with *attr* in *source*.

    If provided, this value must be a *int*, or a valid string representation of a *int*.

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param min_val: the minimum value accepted
    :param max_val:  the maximum value accepted
    :param values: optional list of allowed values
    :param default: optional default value, overrides *required*
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # initialize the return variable
    result: int | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # retrieve the value
    value: int = source.get(suffix)

    # validate it ('bool' is subtype of 'int')
    if value is None and isinstance(default, int) and not isinstance(default, bool):
        value = default
    elif isinstance(value, str) and value.isnumeric():
        value = int(value)
    elif value is not None and \
            (isinstance(value, bool) or not isinstance(value, int)):
        # 152: Invalid value {}: must be type {}
        stat = validate_format_error(152,
                                     value,
                                     "int",
                                     f"@{attr}")
    if not stat:
        stat = validate_value(attr=attr,
                              value=value,
                              min_value=min_val,
                              max_value=max_val,
                              values=values,
                              required=required)
    if stat:
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)
    else:
        result = value

    return result


def validate_decimal(source: dict[str, Any],
                     attr: str,
                     min_val: float = None,
                     max_val: float = None,
                     required: bool = False,
                     values: list[float | int] = None,
                     default: float = None,
                     errors: list[str] = None,
                     logger: Logger = None) -> Decimal | None:
    """
    Validate the *float* value associated with *attr* in *source*.

    If provided, this value must be a *float*, or a valid string representation of a *float*.

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param min_val: the minimum value accepted
    :param max_val:  the maximum value accepted
    :param values: optional list of allowed values
    :param default: optional default value, overrides *required*
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # initialize the return variable
    result: Decimal | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # retrieve the value
    value: Decimal = source.get(suffix)

    # validate it
    if value is None and isinstance(default, int | float | Decimal):
        value = Decimal(value=default)
    elif (isinstance(value, float) or
          (isinstance(value, int) and not isinstance(value, bool)) or
          (isinstance(value, str) and value.replace(".", "", 1).isnumeric())):
        value = Decimal(value=value)
    elif isinstance(value, bool) or \
            (value is not None and not isinstance(value, int | float | Decimal)):
        # 152: Invalid value {}: must be type {}
        stat = validate_format_error(152,
                                     value,
                                     "decimal",
                                     f"@{attr}")
    if not stat:
        stat = validate_value(attr=attr,
                              value=value,
                              min_value=min_val,
                              max_value=max_val,
                              values=values,
                              required=required)
    if stat:
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)
    else:
        result = value

    return result


def validate_str(source: dict[str, Any],
                 attr: str,
                 min_length: int = None,
                 max_length: int = None,
                 values: list[str] = None,
                 default: str = None,
                 ignore_case: bool = False,
                 required: bool = False,
                 errors: list[str] = None,
                 logger: Logger = None) -> str | None:
    """
    Validate the *str* value associated with *attr* in *source*.

    If provided, this value must be a *str*.

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param min_length: optional minimum length accepted
    :param max_length:  optional maximum length accepted
    :param values: optional list of allowed values
    :param default: optional default value, overrides *required*
    :param ignore_case: specifies whether to ignore capitalization
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # initialize the return variable
    result: str | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # obtain the value
    value: str | None = source.get(suffix)

    # validate it
    if value is None and isinstance(default, str):
        value = default
    elif value is not None and not isinstance(value, str):
        # 152: Invalid value {}: must be type {}
        stat = validate_format_error(152,
                                     value,
                                     "str",
                                     f"@{attr}")
    else:
        stat = validate_value(attr=attr,
                              value=value,
                              min_value=min_length,
                              max_value=max_length,
                              values=values,
                              ignore_case=ignore_case,
                              required=required)
    if stat:
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)
    else:
        result = value

    return result


def validate_date(source: dict[str, Any],
                  attr: str,
                  day_first: bool = False,
                  default: date = None,
                  required: bool = False,
                  errors: list[str] = None,
                  logger: Logger = None) -> date | None:
    """
    Validate the *date* value associated with *attr* in *source*.

    If provided, this value must be a *date* or *datetime*, a valid string representation of
    a *date* or *datetime*, or an integer or float encoding a UNIX-style *timestamp*.
    If the value obtained is a *datetime*, its *date* part is returned.

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param day_first: indicates that the day precedes the month in the string representing the date
    :param default: optional default value, overrides *required*
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # import needed module
    from .datetime_pomes import date_parse

    # initialize the return variable
    result: date | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # obtain the value
    value: str = source.get(suffix)

    # validate it
    if value:
        if isinstance(value, datetime):
            result = value.date()
        elif isinstance(value, date):
            result = value
        elif isinstance(value, int | float):
            result = datetime.fromtimestamp(value).date()
        else:
            result = date_parse(dt_str=value,
                                dayfirst=day_first)
        if not result:
            # 141: Invalid value {}
            stat = validate_format_error(141,
                                         value,
                                         f"@{attr}")
        elif result > datetime.now(tz=TZ_LOCAL).date():
            # 153: Invalid value {}: date is later than the current date
            stat = validate_format_error(153,
                                         value,
                                         f"@{attr}")
    elif isinstance(default, date):
        result = default
    elif isinstance(required, bool) and required:
        # 121: Required attribute
        stat = validate_format_error(121,
                                     f"@{attr}")
    if stat:
        result = None
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)

    return result


def validate_datetime(source: dict[str, Any],
                      attr: str,
                      day_first: bool = True,
                      default: datetime = None,
                      required: bool = False,
                      errors: list[str] = None,
                      logger: Logger = None) -> datetime | None:
    """
    Validate the *datetime* value associated with *attr* in *source*.

    If provided, this value must be a *date* or *datetime*, a valid string representation of
    a *date* or *datetime*, or an integer or float encoding a UNIX-style timestamp.
    If the value obtained is a *date*, it is converted to a *datetime* by appending *00:00:00*.

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param day_first: indicates that the day precedes the month in the string representing the date
    :param default: optional default value, overrides *required*
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # import needed module
    from .datetime_pomes import datetime_parse

    # initialize the return variable
    result: datetime | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # obtain and validate the value
    value: str = source.get(suffix)
    if value:
        if isinstance(value, datetime):
            result = value
        elif isinstance(value, date):
            result = datetime.combine(result, time())
        elif isinstance(value, int | float):
            result = datetime.fromtimestamp(value)
        else:
            result = datetime_parse(dt_str=value,
                                    dayfirst=day_first)
        if not result:
            # 141: Invalid value {}
            stat = validate_format_error(141,
                                         value,
                                         f"@{attr}")
        elif result > datetime.now(tz=TZ_LOCAL):
            # 153: Invalid value {}: date is later than the current date
            stat = validate_format_error(153,
                                         value,
                                         f"@{attr}")
    elif isinstance(default, datetime):
        result = default
    elif isinstance(required, bool) and required:
        # 121: Required attribute
        stat = validate_format_error(121,
                                     f"@{attr}")
    if stat:
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)

    return result


def validate_enum(source: dict[str, Any],
                  attr: str,
                  enum_class: type[IntEnum | StrEnum],
                  values: list[IntEnum | StrEnum | str | int | Decimal] = None,
                  default: IntEnum | StrEnum | str | int | Decimal = None,
                  required: bool = False,
                  errors: list[str] = None,
                  logger: Logger = None) -> IntStrEnum:
    """
    Validate the *enum* value associated with *attr* in *source*.

    If provided, this value must be a name or a value corresponding to an instance of a subclass of *enum_class*.
    The only accepted values for *enum_class* are subclasses of  *StrEnum* or *IntEnum*.
    If *values* is specified, the value obtained is checked for occurrence therein.

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param enum_class: the *enum* class to consider (must be a subclass of *IntEnum* or *StrEnum*)
    :param default: optional default value, overrides *required*
    :param values: optional list of allowed values (defaults to all elements of *enum_class*)
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value as an instance of *enum_class*, or *None* if validation failed
    """
    from .obj_pomes import StrEnumUseName
    # initialize the return variable
    result: IntEnum | StrEnum | None = None

    if issubclass(enum_class, StrEnumUseName):
        pos: int = attr.rfind(".") + 1
        suffix: str = attr[pos:]
        value: Any = source.get(suffix)
        if isinstance(value, Enum):
            source = source.copy()
            source[attr] = value.name
        # noinspection PyProtectedMember
        vals: list[str | int | Decimal] = [v.name if isinstance(v, Enum) else v
                                           for v in (values or enum_class._member_names_)]
        name: str = validate_str(source=source,
                                 attr=attr,
                                 values=vals,
                                 default=default.name if isinstance(default, Enum) else default,
                                 ignore_case=True,
                                 required=required,
                                 errors=errors,
                                 logger=logger)
        if name:
            for e in enum_class:
                if e.name.lower() == name.lower():
                    result = e
                    break
    else:
        value: Any = None
        vals: list[str | int | Decimal] = [v.value if isinstance(v, Enum) else v
                                           for v in (values or enum_class)]
        if issubclass(enum_class, StrEnum):
            value: str = validate_str(source=source,
                                      attr=attr,
                                      values=vals,
                                      default=default.value if isinstance(default, Enum) else default,
                                      required=required,
                                      errors=errors,
                                      logger=logger)
        elif issubclass(enum_class, IntEnum):
            value: int = validate_int(source=source,
                                      attr=attr,
                                      values=vals,
                                      default=default.value if isinstance(default, Enum) else default,
                                      required=required,
                                      errors=errors,
                                      logger=logger)
        if value:
            result = enum_class(value)

    return result


def validate_email(source: dict[str, Any],
                   attr: str,
                   default: str = None,
                   required: bool = False,
                   errors: list[str] = None,
                   logger: Logger = None) -> str | None:
    """
    Validate the email value associated with *attr* in *source*.

    If provided, this value must be a syntactically correct email.

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param default: optional default value, overrides *required*
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # initialize the return variable
    result: str | None = None

    value: str = validate_str(source=source,
                              attr=attr,
                              default=default,
                              required=required,
                              errors=errors,
                              logger=logger)
    if value:
        if CRON_EMAIL.match(value):
            result = value
        elif isinstance(errors, list):
            # 141: Invalid value {}
            errors.append(validate_format_error(141,
                                                value,
                                                f"@{attr}"))
    elif isinstance(required, bool) and required and isinstance(errors, list):
        # 121: Required attribute
        errors.append(validate_format_error(121,
                                            f"@{attr}"))
    return result


def validate_pwd(source: dict[str, Any],
                 attr: str,
                 required: bool = False,
                 errors: list[str] = None,
                 logger: Logger = None) -> str | None:
    r"""
    Validate the password value associated with *attr* in *source*.

    If provided, this value must abide by the following rules:
      - length >= 8
      - at least 1 digit (in range [0-9])
      - at least 1 lower-case letter (in range [a-z])
      - at least 1 uppercase letter (in renge [A-Z])
      - at least 1 special character (#$%&"'()*+,-./:;<=>?@[\]^_`{|}~!)

    :param source: *dict* containing the value to be validated
    :param attr: the attribute associated with the value to be validated
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated value, or *None* if validation failed
    """
    # initialize the return variable
    result: str | None = None

    value: str = validate_str(source=source,
                              attr=attr,
                              required=required,
                              errors=errors,
                              logger=logger)
    if value:
        if (len(value) >= 8 and
            str_find_char(value,
                          chars=string.digits) >= 0 and
            str_find_char(value,
                          chars=string.ascii_uppercase) >= 0 and
            str_find_char(value,
                          chars=string.ascii_lowercase) >= 0 and
            str_find_char(value,
                          chars=string.punctuation) >= 0):
            result = value
        elif isinstance(errors, list):
            # 237: Value {} does not meet the formation rules
            errors.append(validate_format_error(237,
                                                value,
                                                f"@{attr}"))
    elif isinstance(required, bool) and required and isinstance(errors, list):
        # 121: Required attribute
        errors.append(validate_format_error(121,
                                            f"@{attr}"))
    return result


def validate_cron(source: dict[str, Any],
                  attr: str,
                  required: bool = False,
                  errors: list[str] = None,
                  logger: Logger = None) -> str | None:
    r"""
    Validate the *CRON* expression associated with *attr* in *source*.

    A valid *CRON* expression has the syntax *<min> <hour> <day> <month> <day-of-week>*, and can include:
      - numbers (e.g. '5')
      - ranges (e.g. '1-5')
      - lists (e.g. '1,2,3')
      - steps (e.g. '*/15')
      - wildcards ('*')

    The following meta-expressions may be substituted for their equivalent CRON expressions:
      - @annually: "0 0 1 1 *"  (on January 1st, at 00h00)
      - @daily:    "1 0 * * *"  (daily, at 00h01)
      - @hourly:   "0 * * * *"  (every hour, at minute 0 - ??h00)
      - @midnight: "0 0 * * *"  (daily, at 00h00)
      - @monthly:  "0 0 1 * *"  (on the first day of the month, at 00h00)
      - @reboot:   "1 0 * * *"  (same as @daily)
      - @weekly:   "0 0 * * 0"  (on Sundays, at 00h00)
      - @yearly:   "0 0 1 1 *"  (same as @annually)

    :param source: *dict* containing the expression to be validated
    :param attr: the attribute associated with the expression to be validated
    :param required: specifies whether a value must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the validated expression, or *None* if validation failed
    """
    # initialize the return variable
    result: str | None = None

    expr: str = validate_str(source=source,
                             attr=attr,
                             required=required,
                             errors=errors,
                             logger=logger)
    if expr:
        match expr:
            case "@annually" | "@yearly":
                result = "0 0 1 1 *"                      # on January 1st, at 00h00
            case "@daily" | "@reboot":
                result = "1 0 * * *"                      # daily, at 00h01
            case "@hourly":
                result = "0 * * * *"                      # every hour, at minute 0 (??h00)
            case "@midnight":
                result = "0 0 * * *"                      # daily, at 00h00
            case "@monthly":
                result = "0 0 1 * *"                      # on the first day of the month, at 00h00
            case "@weekly":
                result = "0 0 * * 0"                      # on Sundays, at 00h00
            case _:
                if CRON_REGEX.match(expr):
                    result = expr
                elif isinstance(errors, list):
                    # 213: Invalid CRON expression {}
                    errors.append(validate_format_error(238,
                                                        expr,
                                                        f"@{attr}"))
    elif isinstance(required, bool) and required and isinstance(errors, list):
        # 121: Required attribute
        errors.append(validate_format_error(121,
                                            f"@{attr}"))
    return result


def validate_ints(source: dict[str, Any],
                  attr: str,
                  sep: str = ",",
                  min_val: int = None,
                  max_val: int = None,
                  required: bool = False,
                  errors: list[str] = None,
                  logger: Logger = None) -> list[int] | None:
    """
    Validate the list of *int* values associated with *attr* in *source*.

    If provided as a string, the elements therein must be valid string representations of *ints*, separated
    by *sep* (which defaults to a *comma*). Note that an empty string os an empty list are acceptable values,
    yielding an empty list of *ints*.

    :param source: *dict* containing the list of values to be validated
    :param attr: the attribute associated with the list of values to be validated
    :param sep: the separator in the list of values
    :param min_val: the minimum value accepted
    :param max_val:  the maximum value accepted
    :param required: whether the list of values must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the list of validated values, or *None* if validation failed or not required and no values found
    """
    # initialize the return variable
    result: list[int] | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # obtain the values
    values: list = source.get(suffix)
    if values:
        if isinstance(values, str):
            values = str_as_list(values,
                                 sep=sep)
        if isinstance(values, list):
            ints: list[int] = []
            if len(values) > 0:
                for inx, value in enumerate(values):
                    if (isinstance(value, str) and value.isdigit()) or \
                            (isinstance(value, int) and not isinstance(value, bool)):
                        ints.append(int(value))
                        stat = validate_value(attr=f"@{attr}[{inx+1}]",
                                              value=int(value),
                                              min_value=min_val,
                                              max_value=max_val)
                    else:
                        # 152: Invalid value {}: must be type {}
                        stat = validate_format_error(152,
                                                     value,
                                                     "int",
                                                     f"@{attr}[{inx+1}]")
                    if stat:
                        break
            if not stat:
                result = ints
        else:
            # 152: Invalid value {}: must be type {}
            stat = validate_format_error(152,
                                         values,
                                         "list",
                                         f"@{attr}")

    if isinstance(required, bool) and required and not stat and result is None:
        # 121: Required attribute
        stat = validate_format_error(121,
                                     f"@{attr}")
    if stat:
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)

    return result


def validate_strs(source: dict[str, Any],
                  attr: str,
                  sep: str = ",",
                  min_length: int = None,
                  max_length: int = None,
                  required: bool = False,
                  errors: list[str] = None,
                  logger: Logger = None) -> list[str] | None:
    """
    Validate the list of *str* values associated with *attr* in *source*.

    If provided as a string, the elements therein must be separated by *sep* (which defaults to a *comma*).
    Note that an empty string os an empty list are acceptable values, yielding an empty list of *strs*.

    :param source: *dict* containing the list of values to be validated
    :param attr: the attribute associated with the list of values to be validated
    :param sep: the separator in the list of values
    :param min_length: optional minimum length accepted
    :param max_length:  optional maximum length accepted
    :param required: whether the list of values must be provided
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the list of validated values, or *None* if validation failed or not required and no values found
    """
    # initialize the return variable
    result: list[str] | None = None

    stat: str | None = None
    pos: int = attr.rfind(".") + 1
    suffix: str = attr[pos:]

    # obtain the values
    values: list = source.get(suffix)
    if values:
        if isinstance(values, str):
            values = str_as_list(values,
                                 sep=sep)
        if isinstance(values, list):
            strs: list[str] = []
            if len(values) > 0:
                for inx, value in enumerate(values):
                    strs.append(value)
                    if isinstance(value, str):
                        stat = validate_value(attr=f"@{attr}[{inx+1}]",
                                              value=value,
                                              min_value=min_length,
                                              max_value=max_length)
                    else:
                        # 152: Invalid value {}: must be type {}
                        stat = validate_format_error(152,
                                                     value,
                                                     "str",
                                                     f"@{attr}[{inx+1}]")
                    if stat:
                        break
            if not stat:
                result = strs
        else:
            # 152: Invalid value {}: must be type {}
            stat = validate_format_error(152,
                                         values,
                                         "list",
                                         f"@{attr}")

    if required and not stat and result is None:
        # 121: Required attribute
        stat = validate_format_error(121,
                                     f"@{attr}")
    if stat:
        if logger:
            logger.error(msg=stat)
        if isinstance(errors, list):
            errors.append(stat)

    return result


def validate_format_error(error_id: int,
                          /,
                          *args: Any,
                          **kwargs: dict[str, Any]) -> str:
    """
    Format and return the error message identified by *err_id* in the standard messages list.

    The message is built from the message element in the standard messages list, identified by *error_id*.
    The occurrences of *{}* in the element are sequentially replaced by the given *args*.
    When replacing, an instance of *args* is surrounded by single quotes if it contains no blankspaces.
    The element in *args* prefixed with *@*, if present, is appended to the end of the message.

    Optional custom language and prefix, replacing those defined respectively by the environment variables
    *VALIDATION_MSG_LANGUAGE* and *VALIDATION_MSG_PREFIX*, may be provided in *kwargs*, with the corresponding
    keys *msg_lang*, and *msg_prefix*.

    Suppose this function is invoked with:
      - *error_id*: 147 (defined as: Invalid value {}: length shorter than {})
      - *args*: 'my_value', 10, '@my_attr'
    The formatted error message will be (*<VMP>* is the validation message prefix):
      - <VMP>147: Invalid value 'my_value': length shorter than 10 @my_attr

    if the value of *error_id* is *100*, then the message prefix *<VMP><error-id>* is omitted.

    :param error_id: the identification of the message element
    :param args: optional non-keyworded arguments to format the error message with
    :param kwargs: optional keyworded arguments to define language and prefix
    :return: the formatted error message
    """
    # obtain definitions for prefix and language
    msg_prefix: str = kwargs.get("msg_prefix") if "msg_prefix" in kwargs else VALIDATION_MSG_PREFIX
    msg_lang: MsgLang = validate_enum(source=kwargs or {},
                                      attr="msg_lang",
                                      enum_class=MsgLang,
                                      default=VALIDATION_MSG_LANGUAGE)
    # retrieve the messages list
    match msg_lang:
        case MsgLang.EN:
            from .validation_msgs import _ERR_MSGS_EN
            err_msgs = _ERR_MSGS_EN
        case MsgLang.PT:
            from .validation_msgs import _ERR_MSGS_PT
            err_msgs = _ERR_MSGS_PT
        case _:
            err_msgs = {}

    # initialize the return variable
    result: str = ""
    if error_id != 100:
        if msg_prefix:
            result += msg_prefix + str(error_id) + ": "
        result += err_msgs.get(error_id, "")

    # apply the provided arguments
    for arg in args:
        if arg is None:
            pos1: int = result.find(": {}")
            pos2: int = result.find(" {}")
            if pos1 < 0 or pos2 < pos1:
                result = result.replace(" {}", "", 1)
            else:
                result = result.replace(": {}", "", 1)
        elif not result or (isinstance(arg, str) and arg.startswith("@")):
            result += " " + arg
        elif isinstance(arg, str) and arg.find(" ") > 0:
            result = result.replace("{}", arg, 1)
        else:
            result = result.replace("{}", f"'{arg}'", 1)

    return result


def validate_format_errors(errors: list[str],
                           **kwargs: dict) -> list[dict[str, str]]:
    """
    Build and return a list of *dicts* from the list of errors in *errors*.

    Each element in *errors* is encoded as a *dict*.
    This list is typically used in a returning *JSON* string.

    Optional custom language and prefix, replacing those defined respectively by the environment variables
    *VALIDATION_MSG_LANGUAGE* and *VALIDATION_MSG_PREFIX*, may be provided in *kwargs*, with the corresponding
    keys *msg_lang*, and *msg_prefix*.

    Suppose *errors* contains (*<VMP>* is the validation message prefix):
      - <VMP>147: Invalid value 'my_value': length shorter than 10 @my_attr
    The returned list will contain the *dict*:
      - {
      -   "attribute": "my_attr",
      -   "code": <VMP>147,
      -   "description": Invalid value 'my_value': length shorter than 10
      - }

    :param errors: the list of errors to build the list of *dicts* with
    :param kwargs: optional keyworded arguments to define formatting language and prefix
    :return: the built list of *dicts*
    """
    # obtain definitions for prefix and language
    msg_prefix: str = kwargs.get("msg_prefix") if "msg_prefix" in kwargs else VALIDATION_MSG_PREFIX
    msg_lang: MsgLang = validate_enum(source=kwargs or {},
                                      attr="msg_lang",
                                      enum_class=MsgLang,
                                      default=VALIDATION_MSG_LANGUAGE)
    # initialize the return variable
    result: list[dict[str, str]] = []

    # extract error code, description, and attribute from text
    for error in errors:

        # locate the last indicator for the attribute
        pos = error.rfind("@")

        # is there a whitespace in the attribute's name ?
        if pos > 0 and str_find_whitespace(error[pos:]) > 0:
            # yes, disregard the attribute
            pos = -1

        # was the attribute's name found ?
        if pos == -1:
            # no
            out_error: dict[str, str] = {}
            desc: str = error
        else:
            # yes
            term: str = "attribute" if msg_lang == MsgLang.EN else "atributo"
            out_error: dict[str, str] = {term: error[pos + 1:]}
            desc: str = error[:pos - 1]

        # does the text contain an error code ?
        if msg_prefix and desc.startswith(msg_prefix):
            # yes
            term: str = "code" if msg_lang == MsgLang.EN else "codigo"
            pos: int = desc.find(":")
            out_error[term] = desc[0:pos]
            desc = desc[pos+2:]

        term: str = "description" if msg_lang == MsgLang.EN else "descricao"
        out_error[term] = desc
        result.append(out_error)

    return result


def validate_unformat_errors(errors: list[dict[str, str] | str],
                             **kwargs: dict) -> list[str]:
    """
    Extract and return the list of errors used to build the list of dicts *errors*.

    Optional custom language, replacing the one defined by the environment variable
    *VALIDATION_MSG_LANGUAGE*, may be provided in *kwargs*, with the key *msg_lang*.

    :param errors: the list of dicts to extract the errors from
    :param kwargs: optional keyworded arguments to define formatting language
    :return: the built list of errors
    """
    # obtain definitions for language and prefix
    msg_lang: MsgLang = validate_enum(source=kwargs or {},
                                      attr="msg_lang",
                                      enum_class=MsgLang,
                                      default=VALIDATION_MSG_LANGUAGE)
    # initialize the return variable
    result: list[str] = []

    # define the dictionary keys
    name: str = "code" if msg_lang == MsgLang.EN else "codigo"
    desc: str = "description" if msg_lang == MsgLang.EN else "descricao"

    # traverse the list of dicts
    for error in errors:
        if isinstance(error, dict):
            desc: str = str_sanitize(error.get(desc) or "''")
            result.append(f"{error.get(name)}: {desc}")
        else:
            result.append(error)

    return result
