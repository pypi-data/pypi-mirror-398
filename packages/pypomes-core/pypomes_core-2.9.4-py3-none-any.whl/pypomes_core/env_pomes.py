import ast
import os
from base64 import b64decode, urlsafe_b64decode
from contextlib import suppress
from datetime import date
from dateutil import parser
from dateutil.parser import ParserError
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any, Final, Literal

# the prefix for the names of the environment variables
APP_PREFIX: Final[str] = os.getenv(key="PYPOMES_APP_PREFIX",
                                   default="")


def env_get_str(key: str,
                values: list[str] = None,
                ignore_case: bool = False,
                def_value: str = None) -> str | None:
    """
    Retrieve the string value defined for *key* in the current operating environment.

    If *values* is specified, the value obtained is checked for occurrence therein.

    :param key: the key which the value is associated with
    :param values: optional list of valid values
    :param ignore_case: specifies whether to ignore capitalization
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the string value associated with the key, or *def_value* if error
    """
    # initialize the return variable
    result: str | None = None

    value: str = os.getenv(key)
    # allow for value to be defined as an empty string
    if value is None:
        result = def_value
    elif values:
        val: str = value
        if ignore_case:
            val = value.lower() if isinstance(value, str) else value
            values = [v.lower() if isinstance(v, str) else v for v in values]
        if val in values:
            result = value
    else:
        result = value

    return result


def env_get_strs(key: str,
                 values: list[str] = None,
                 ignore_case: bool = False) -> list[str] | None:
    """
    Retrieve the string values defined for *key* in the current operating environment.

    The values must be provided as a comma-separated list of strings.
    If *values* is specified, the values obtained are checked for occurrence therein, with *ignore_case*
    determining whether to ignore capitalization. On failure, *None* is returned.

    :param key: the key the values ares associated with
    :param values: optional list of valid values
    :param ignore_case: specifies whether to ignore capitalization when checking with *values*
    :return: the string values associated with the key, or *def_value* if error
    """
    # initialize the return variable
    result: list[str] | None = None

    vals: str = os.getenv(key)
    if vals:
        result = vals.split(",")
        if values:
            if ignore_case:
                vals = vals.lower()
                values = [v.lower() if isinstance(v, str) else v for v in values]
            for val in vals.split(","):
                if val not in values:
                    result = None
                    break
    return result


def env_get_int(key: str,
                values: list[int] = None,
                def_value: int = None) -> int | None:
    """
    Retrieve the integer value defined for *key* in the current operating environment.

    If *values* is specified, the value obtained is checked for occurrence therein.

    :param key: the key which the value is associated with
    :param values: optional list of valid values
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the integer value associated with the key, or *def_value* if error
    """
    result: int | None
    try:
        result = int(os.environ[key])
        if values and result not in values:
            result = None
    except (AttributeError, KeyError, TypeError):
        result = def_value

    return result


def env_get_ints(key: str,
                 values: list[str] = None) -> list[int] | None:
    """
    Retrieve the integer values defined for *key* in the current operating environment.

    The values must be provided as a comma-separated list of integers.
    If *values* is specified, the values obtained are checked for occurrence therein.
    On failure, *None* is returned.

    :param key: the key the values ares associated with
    :param values: optional list of valid values
    :return: the integer values associated with the key, or *def_value* if error
    """
    result: list[int] | None = None
    # noinspection PyUnusedLocal
    with suppress(Exception):
        vals: list[str] = os.environ[key].split(",")
        if vals:
            result = [int(val) for val in vals]
            if values:
                for val in result:
                    if val not in values:
                        result = None
                        break
    return result


def env_get_float(key: str,
                  values: list[float] = None,
                  def_value: float = None) -> float | None:
    """
    Retrieve the float value defined for *key* in the current operating environment.

    If *values* is specified, the value obtained is checked for occurrence therein.

    :param key: the key which the value is associated with
    :param values: optional list of valid values
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the float value associated with the key, or *def_value* if error
    """
    result: float | None
    try:
        result = float(os.environ[key])
        if values and result not in values:
            result = None
    except (AttributeError, KeyError, TypeError):
        result = def_value

    return result


def env_get_floats(key: str,
                   values: list[str] = None) -> list[float] | None:
    """
    Retrieve the float values defined for *key* in the current operating environment.

    The values must be provided as a comma-separated list of floats.
    If *values* is specified, the values obtained are checked for occurrence therein.
    On failure, *None* is returned.

    :param key: the key the values ares associated with
    :param values: optional list of valid values
    :return: the float values associated with the key, or *def_value* if error
    """
    result: list[float] | None = None
    # noinspection PyUnusedLocal
    with suppress(Exception):
        vals: list[str] = os.environ[key].split(",")
        if vals:
            result = [float(val) for val in vals]
            if values:
                for val in result:
                    if val not in values:
                        result = None
                        break
    return result


def env_get_enum(key: str,
                 enum_class: type[IntEnum | StrEnum],
                 values: list[IntEnum | StrEnum] = None,
                 def_value: IntEnum | StrEnum = None) -> Any:
    """
    Retrieve the enum value defined for *key* in the current operating environment.

    If provided, this value must be a name or a value corresponding to an instance of a subclass of *enum_class*.
    The only accepted values for *enum_class* are subclasses of  *StrEnum* or *IntEnum*.
    If *values* is specified, the value obtained is checked for occurrence therein.
    On failure, *None* is returned.

    :param key: the key which the value is associated with
    :param enum_class: the *enum* class to consider (must be a subclass of *IntEnum* or *StrEnum*)
    :param values: optional list of allowed values (defaults to all elements of *enum_class*)
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the value associated with the key, or *def_value* if error
    """
    from .obj_pomes import IntEnumUseName, StrEnumUseName

    # initialize the return variable
    result: Any = None

    if issubclass(enum_class, IntEnumUseName | StrEnumUseName):
        # noinspection PyUnresolvedReferences
        name: str = env_get_str(key=key,
                                values=[e.name for e in (values or enum_class)],
                                ignore_case=True,
                                def_value=def_value.name if def_value else None)
        if isinstance(name, str):
            for e in enum_class:
                if e.name.lower() == name.lower():
                    result = e
                    break
    else:
        value: Any = None
        vals: list = [e.value for e in (values or enum_class)]
        if issubclass(enum_class, StrEnum):
            value: str = env_get_str(key=key,
                                     values=vals,
                                     def_value=def_value)
        elif issubclass(enum_class, IntEnum):
            value: int = env_get_int(key=key,
                                     values=vals,
                                     def_value=def_value)
        if value:
            result = enum_class(value)

    return result


def env_get_enums(key: str,
                  enum_class: type[IntEnum | StrEnum]) -> list:
    """
    Retrieve the enum values defined for *key* in the current operating environment.

    If provided, these value must be names or values corresponding to an instance of a subclass of *enum_class*.
    The only accepted values for *enum_class* are subclasses of *StrEnum* or *IntEnum*. It must be possible
    to convert all names associated with *key* to enum instances. On failure, *None* is returned.

    :param key: the key which the values are associated with
    :param enum_class: the *enum* class to consider (must be a subclass of *IntEnum* or *StrEnum*)
    :return: the values associated with the key, or *def_value* if error
    """
    from .obj_pomes import IntEnumUseName, StrEnumUseName

    # initialize the return variable
    result: list | None = None

    enums: list = []
    values: str = os.getenv(key)
    if values:
        found: bool = False
        names: list[str] = values.split(",")
        for name in names:
            found = False
            if issubclass(enum_class, IntEnumUseName | StrEnumUseName):
                for e in enum_class:
                    if e.name.lower() == name.lower():
                        enums.append(e)
                        found = True
                        break
            else:
                if issubclass(enum_class, IntEnum) and name.isdigit():
                    value: int = int(name)
                else:
                    value: str = name
                if value in enum_class:
                    # noinspection PyCallingNonCallable
                    enums.append(enum_class(value))
                    found = True
            # break on the first failure
            if not found:
                break
        if found:
            result = enums

    return result


def env_get_bool(key: str,
                 def_value: bool = None) -> bool:
    """
    Retrieve the boolean value defined for *key* in the current operating environment.

    These are the criteria:
        - case is disregarded
        - the string values accepted to stand for *True* are *1*, *t*, or *true*
        - the string values accepted to stand for *False* are *0*, *f*, or *false*
        - all other values causes *None* to be returned

    :param key: the key which the value is associated with
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the boolean value associated with the key, or *def_value* if error
    """
    result: bool | None
    try:
        if os.environ[key].lower() in ["1", "t", "true"]:
            result = True
        elif os.environ[key].lower() in ["0", "f", "false"]:
            result = False
        else:
            result = None
    except (AttributeError, KeyError, TypeError):
        result = def_value

    return result


def env_get_bytes(key: str,
                  encoding: Literal["base64", "base64url", "hex", "utf8"] = "base64url",
                  values: list[bytes] = None,
                  def_value: bytes = None) -> bytes | None:
    """
    Retrieve the byte value defined for *key* in the current operating environment.

    The string defined in the environment must contain the *bytes* value encoded as defined in *encoding*.
    If *values* is specified, the value obtained is checked for occurrence therein.
    On failure, *None* is returned.

    :param key: the key which the value is associated with
    :param encoding: the representation of the *bytes* value
    :param values: optional list of valid values
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the byte value associated with the key, or *def_value* if error
    """
    result: bytes | None = None
    try:
        value: str = os.environ[key]
        match encoding:
            case "hex":
                result = bytes.fromhex(value)
            case "utf8":
                result = value.encode()
            case "base64":
                result = b64decode(s=value)
            case "base64url":
                result = urlsafe_b64decode(s=value)
        if values and result not in values:
            result = None
    except (AttributeError, KeyError, TypeError):
        result = def_value

    return result


def env_get_date(key: str,
                 def_value: date = None) -> date:
    """
    Retrieve the date value defined for *key* in the current operating environment.

    :param key: the key which the value is associated with
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the date value associated with the key, or *def_value* if error
    """
    result: date
    try:
        result = parser.parse(os.environ[key]).date()
    except (AttributeError, KeyError, TypeError, ParserError, OverflowError):
        result = def_value

    return result


def env_get_path(key: str,
                 def_value: Path = None) -> Path:
    """
    Retrieve the path value defined for *key* in the current operating environment.

    :param key: the key which the value is associated with
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the path value associated with the key, or *def_value* if error
    """
    result: Path
    try:
        result = Path(os.environ[key]).resolve()
    except (AttributeError, KeyError, TypeError):
        result = def_value

    return result


def env_get_obj(key: str,
                def_value: Any = None) -> Any:
    """
    Retrieve the string-marshalled object defined for *key* in the current operating environment.

    As an example, suppose the string *"{'name': 'Alice', 'age': 30, 'city': 'New York'}"*.
    When properly unmarshalled, it yields the *dict* object
        {
            'name': 'Alice',
            'age': 30,
            'city': 'New York'
        }

    :param key: the key which the value is associated with
    :param def_value: the value to return, if obtaining the value for *key* fails (defaults to *None*)
    :return: the unmarshalled object associated with the key, or *def_value* if error
    """
    result: Any
    try:
        result = ast.literal_eval(node_or_string=os.environ[key])
    except (AttributeError, KeyError, TypeError):
        result = def_value

    return result


def env_is_docker() -> bool:
    """
    Determine whether the application is running inside a Docker container.

    Note that a reasonable, but not infallible, heuristics is used.

    :return: 'True' if this could be determined, 'False' otherwise
    """
    result: bool = Path("/.dockerenv").exists()
    if not result:
        with (suppress(Exception),
              Path("/proc/1/cgroup", "rt").open() as f):
            result = "docker" in f.read()

    return result
