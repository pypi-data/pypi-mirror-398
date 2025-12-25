import json
import os
from enum import IntEnum, StrEnum
from types import TracebackType
from typing import Any


class IntEnumUseName(IntEnum):
    """
    A marker indicating that the attribute *name* should, in some circumstances, be used in lieu of
    *value*, as when it becomes necessary to locate an instance of this class by looking for a *str*
    having its name, rather then for an *int* having its value (examples in the *env_pomes* module).
    """


class StrEnumUseName(StrEnum):
    """
    A marker indicating that the attribute *name* should be used in lieu of *value*, as the latter
    is intended to be a description of the *StrEnum* instance.
    """


def obj_is_serializable(obj: Any) -> bool:
    """
    Determine if *obj* is serializable.

    :param obj: the reference object
    :return: *True* if serializable, *False* otherwise
    """
    # initialize the return variable
    result: bool = True

    # verify the object
    try:
        json.dumps(obj)
    except (TypeError, OverflowError):
        result = False

    return result


def obj_to_dict(obj: Any,
                omit_private: bool = True) -> dict[str, Any] | list[Any] | Any:
    """
    Convert the generic object *obj* to a *dict*.

    The conversion is done recursively. Attributes for which exceptions are raised on attempt
    to access them are silently omitted.

    :param obj: the object to be converted
    :param omit_private: whether to omit private attributes (defaults to *True*)
    :return: the dict obtained from *obj*
    """
    # declare the return variable
    result: dict[str, Any] | list[Any] | Any

    if isinstance(obj, dict):
        result = {str(k): obj_to_dict(obj=v,
                                      omit_private=omit_private) for k, v in obj.items()}
    elif isinstance(obj, list | tuple | set):
        result = [obj_to_dict(obj=item,
                              omit_private=omit_private) for item in obj]
    elif hasattr(obj, "__dict__") or not isinstance(obj, str | int | float | bool | type(None)):
        result = {}
        for attr in dir(obj):
            if not (omit_private and attr.startswith("_")):
                value: Any = getattr(obj,
                                     attr,
                                     None)
                if value is not None and not callable(value):
                    result[attr] = obj_to_dict(obj=value,
                                               omit_private=omit_private)
    else:
        result = obj

    return result


def exc_format(exc: Exception,
               exc_info: tuple[type[BaseException], BaseException, TracebackType]) -> str:
    """
    Format the error message resulting from the exception raised in execution time.

    The format to use: <python_module>, <line_number>: <exc_class> - <exc_text>

    :param exc: the exception raised
    :param exc_info: information associated with the exception
    :return: the formatted message
    """
    tback: TracebackType = exc_info[2]
    cls: str = str(exc.__class__)

    # retrieve the execution point where the exception was raised (bottom of the stack)
    tlast: TracebackType = tback
    while tlast.tb_next:
        tlast = tlast.tb_next

    # retrieve the module name and the line number within the module
    try:
        fname: str = os.path.split(p=tlast.tb_frame.f_code.co_filename)[1]
    except Exception:  # noqa: # noinspection PyBroadException
        fname: str = "<unknow module>"
    fline: int = tlast.tb_lineno

    return f"{fname}, {fline}, {cls[8:-2]} - {exc}"
