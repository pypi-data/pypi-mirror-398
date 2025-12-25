from .datetime_pomes import (
    TZ_LOCAL, DateFormat, DatetimeFormat,
    date_reformat, date_weekday,
    date_parse, datetime_parse,
    timestamp_interval, timestamp_duration
)
from .dict_pomes import (
    dict_has_key, dict_has_value, dict_get_value, dict_set_value,
    dict_reduce, dict_listify, dict_transform, dict_merge, dict_coalesce,
    dict_clone, dict_get_key, dict_get_keys, dict_from_object, dict_from_list,
    dict_replace_value, dict_pop, dict_pop_all, dict_unique_values,
    dict_jsonify, dict_hexify, dict_stringify
)
from .email_pomes import (
    EmailParam, email_setup, email_send, email_codify,
)
from .encoding_pomes import (
    encode_ascii_hex, decode_ascii_hex
)
from .env_pomes import (
    APP_PREFIX,
    env_get_str, env_get_strs,
    env_get_int, env_get_ints,
    env_get_float, env_get_floats,
    env_get_enum, env_get_enums,
    env_get_bool, env_get_bytes,
    env_get_date, env_get_path, env_get_obj, env_is_docker
)
from .file_pomes import (
    TEMP_FOLDER, Mimetype,
    file_get_data, file_get_extension,
    file_get_mimetype, file_is_binary
)
from .func_pomes import (
    func_capture_args, func_defaulted_args, func_specified_args,
    func_capture_params, func_defaulted_params, func_specified_params
)
from .list_pomes import (
    list_compare, list_correlate, list_bin_search,
    list_flatten, list_unflatten, list_get_coupled,
    list_elem_starting_with, list_elem_with_attr, list_transform,
    list_prune_duplicates, list_prune_in, list_prune_not_in,
    list_jsonify, list_hexify, list_hierarchize, list_stringify
)
from .obj_pomes import (
    IntEnumUseName, StrEnumUseName,
    obj_is_serializable, obj_to_dict, exc_format
)
from .str_pomes import (
    str_to_hex, str_from_hex, str_to_lower, str_to_upper,
    str_as_list, str_sanitize, str_split_on_mark,
    str_between, str_positional, str_random, str_splice,
    str_find_char, str_find_whitespace, str_rreplace,
    str_from_any, str_to_bool, str_to_int, str_to_float,
    str_is_int, str_is_float, str_is_hex
)
from .validation_msgs import (
    validate_set_msgs, validate_update_msgs
)
from .validation_pomes import (
    VALIDATION_MSG_LANGUAGE, VALIDATION_MSG_PREFIX, MsgLang, IntStrEnum,
    validate_value, validate_bool, validate_int, validate_decimal,
    validate_str, validate_date, validate_datetime, validate_enum,
    validate_email, validate_pwd, validate_cron, validate_ints, validate_strs,
    validate_format_error, validate_format_errors, validate_unformat_errors
)
from .xml_pomes import (
    XML_FILE_HEADER,
    xml_to_dict, xml_normalize_keys
)

__all__ = [
    # __init__
    "pypomes_versions",
    # datetime_pomes
    "TZ_LOCAL", "DateFormat", "DatetimeFormat",
    "date_reformat", "date_weekday",
    "date_parse", "datetime_parse",
    "timestamp_interval", "timestamp_duration",
    # dict_pomes
    "dict_has_key", "dict_has_value", "dict_get_value", "dict_set_value",
    "dict_reduce", "dict_listify", "dict_transform", "dict_merge", "dict_coalesce",
    "dict_clone", "dict_get_key", "dict_get_keys", "dict_from_object", "dict_from_list",
    "dict_replace_value", "dict_pop", "dict_pop_all", "dict_unique_values",
    "dict_jsonify", "dict_hexify", "dict_stringify",
    # email_pomes
    "EmailParam", "email_setup", "email_send", "email_codify",
    # encoding_pomes
    "encode_ascii_hex", "decode_ascii_hex",
    # env_pomes
    "APP_PREFIX",
    "env_get_str", "env_get_strs",
    "env_get_int", "env_get_ints",
    "env_get_float", "env_get_floats",
    "env_get_enum",  "env_get_enums",
    "env_get_bool", "env_get_bytes",
    "env_get_date", "env_get_path", "env_get_obj", "env_is_docker",
    # file_pomes
    "TEMP_FOLDER", "Mimetype",
    "file_get_data", "file_get_extension",
    "file_get_mimetype", "file_is_binary",
    # func_pomes
    "func_capture_args", "func_defaulted_args", "func_specified_args",
    "func_capture_params", "func_defaulted_params", "func_specified_params",
    # list_pomes
    "list_compare", "list_correlate", "list_bin_search",
    "list_flatten", "list_unflatten", "list_get_coupled",
    "list_elem_starting_with", "list_elem_with_attr", "list_transform",
    "list_prune_duplicates", "list_prune_in", "list_prune_not_in",
    "list_jsonify", "list_hexify", "list_hierarchize", "list_stringify",
    # obj_pomes
    "IntEnumUseName", "StrEnumUseName",
    "obj_is_serializable", "obj_to_dict", "exc_format",
    # str_pomes
    "str_to_hex", "str_from_hex", "str_to_lower", "str_to_upper",
    "str_as_list", "str_sanitize", "str_split_on_mark",
    "str_between", "str_positional", "str_random", "str_splice",
    "str_find_char", "str_find_whitespace", "str_rreplace",
    "str_from_any", "str_to_bool", "str_to_int", "str_to_float",
    "str_is_int", "str_is_float", "str_is_hex",
    # validation_msgs
    "validate_set_msgs", "validate_update_msgs",
    # validation_pomes
    "VALIDATION_MSG_LANGUAGE", "VALIDATION_MSG_PREFIX", "MsgLang", "IntStrEnum",
    "validate_value", "validate_bool", "validate_int", "validate_decimal",
    "validate_str", "validate_date", "validate_datetime", "validate_enum",
    "validate_email", "validate_pwd", "validate_cron", "validate_ints", "validate_strs",
    "validate_format_error", "validate_format_errors", "validate_unformat_errors",
    # xml_pomes
    "XML_FILE_HEADER",
    "xml_to_dict", "xml_normalize_keys"
]

from contextlib import suppress
from importlib import import_module
from importlib.metadata import version
__version__: str = version("pypomes_core")
__version_info__: tuple = tuple(int(i) for i in __version__.split(".") if i.isdigit())


def pypomes_versions() -> dict[str, str]:
    """
    Retrieve the versions of the *Pypomes* packages in use.

    :return: the versions of the Pypomes packages in use
    """
    result: dict[str, str] = {
        "PyPomes-Core": __version__
    }

    with suppress(Exception):
        result["PyPomes-Cloud"] = import_module(name="pypomes_cloud").__version__

    with suppress(Exception):
        result["PyPomes-Crypto"] = import_module(name="pypomes_crypto").__version__

    with suppress(Exception):
        result["PyPomes-DB"] = import_module(name="pypomes_db").__version__

    with suppress(Exception):
        result["PyPomes-HTTP"] = import_module(name="pypomes_http").__version__

    with suppress(Exception):
        result["PyPomes-IAM"] = import_module(name="pypomes_iam").__version__

    with suppress(Exception):
        result["PyPomes-JWT"] = import_module(name="pypomes_jwt").__version__

    with suppress(Exception):
        result["PyPomes-LDAP"] = import_module(name="pypomes_ldap").__version__

    with suppress(Exception):
        result["PyPomes-Logging"] = import_module(name="pypomes_logging").__version__

    with suppress(Exception):
        result["PyPomes-Messaging"] = import_module(name="pypomes_messaging").__version__

    with suppress(Exception):
        result["PyPomes-S3"] = import_module(name="pypomes_s3").__version__

    with suppress(Exception):
        result["PyPomes-Scheduling"] = import_module(name="pypomes_scheduling").__version__

    with suppress(Exception):
        result["PyPomes-SOAP"] = import_module(name="pypomes_soap").__version__

    with suppress(Exception):
        result["PyPomes-SOB"] = import_module(name="pypomes_sob").__version__

    return result
