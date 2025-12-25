import random
import string
from contextlib import suppress
from datetime import date
from pathlib import Path
from typing import Any


def str_to_hex(s: str, /) -> str:
    """
    Obtain and return the hex representation of *s*.

    This is an encapsulation of the built-in methods *<str>.encode()* and *<bytes>.hex()*.

    :param s: the input string
    :return: the hex representation of the input string
    :raises AttributeError: *s* is not a string
    :raises UnicodeEncodeError:  a UTF-8 encoding error occurred
    """
    return s.encode(encoding="utf-8").hex()


def str_from_hex(s: str, /) -> str:
    """
    Obtain and return the original string from its hex representation in *s*.

    This is an encapsulation of the built-in methods *bytes.fromhex()* and *<bytes>.decode()*

    :param s: the hex representation of a string
    :return: the original string
    :raises ValueError: *s* is not a valid hexadecimal string
    :raises TypeError: *s* is not a string
    :raises UnicodeDecodeError: a UTF-8 decoding error occurred
    """
    return bytes.fromhex(s).decode(encoding="utf-8")


def str_as_list(s: str,
                /,
                sep: str = ",") -> list[str]:
    """
    Return *s* as a *list*, by splitting its contents separated by *sep*.

    The returned substrings are fully whitespace-trimmed. If *s* is *None*, an empty list is returned.
    If it is an empty *str*, a list containing an empty *str* is returned. If it is not a *str*,
    a list containing itself is returned.

    :param s: the string value to be worked on
    :param sep: the separator (defaults to ",")
    :return: a list built from the contents of *s*, or containing *s* itself, if it is not a string
    """
    # declare the return variable
    result: list[str]

    if isinstance(s, str):
        result = [s.strip() for s in s.split(sep=sep)]
    elif s is None:
        result = []
    else:
        result = [s]

    return result


def str_sanitize(s: str, /) -> str:
    """
    Clean the given *s* string.

    The sanitization is carried out by:
        - removing backslashes
        - replacing double quotes with single quotes
        - replacing newlines and tabs with whitespace
        - replacing multiple consecutive spaces with a single space

    :param s: the string to be cleaned
    :return: the cleaned string
    """
    cleaned: str = s.replace("\\", "") \
                    .replace('"', "'") \
                    .replace("\n", " ") \
                    .replace("\t", " ")
    return " ".join(cleaned.split())


def str_split_on_mark(s: str,
                      /,
                      mark: str) -> list[str]:
    """
    Extract from *s* the text segments separated by *mark*, and return them in a *list*.

    The separator itself will not be in the returned list.

    :param s: the string to be inspected
    :param mark: the separator
    :return: the list of text segments extracted
    """
    # initialize the return variable
    result: list[str] = []

    pos: int = 0
    skip: int = len(mark)
    after: int = s.find(mark)
    while after >= 0:
        result.append(s[pos:after])
        pos = after + skip
        after = s.find(mark, pos)
    if pos < len(s):
        result.append(s[pos:])
    else:
        result.append("")

    return result


def str_find_char(s: str,
                  /,
                  chars: str) -> int:
    """
    Locate and return the position of the first occurrence, in *s*, of a character in *chars*.

    :param s: the string to be inspected
    :param chars: the reference characters
    :return: the position of the first character in *chars*, or *-1* if none was found
    """
    # initialize the return variable
    result: int = -1

    # search for whitespace
    for inx, char in enumerate(s):
        if char in chars:
            result = inx
            break

    return result


def str_find_whitespace(s: str, /) -> int:
    """
    Locate and return the position of the first occurrence of a *whitespace* character in *s*.

    :param s: the string to be inspected
    :return: the position of the first whitespace character, or *-1* if none was found
    """
    # initialize the return variable
    result: int = -1

    # search for whitespace
    for inx, char in enumerate(s):
        if char.isspace():
            result = inx
            break

    return result


def str_between(s: str,
                /,
                from_str: str,
                to_str: str) -> str:
    """
    Extract and return the *substring* in *s* located between the delimiters *from_str* and *to_str*.

    :param s: the string to be inspected
    :param from_str: the initial delimiter
    :param to_str: the final delimiter
    :return: the extracted substring, or *None* if no substring was obtained
    """
    # initialize the return variable
    result: str | None = None

    pos1: int = s.find(from_str)
    if pos1 >= 0:
        pos1 += len(from_str)
        pos2: int = s.find(to_str, pos1)
        if pos2 >= pos1:
            result = s[pos1:pos2]

    return result


def str_positional(s: str,
                   /,
                   keys: tuple[str, ...],
                   values: tuple[str, ...]) -> Any:
    """
    Locate the position of *s* within *keys*, and return the element in the same position in *values*.

    :param s: the source string
    :param keys: the tuple holding the keys to be inspected
    :param values: the tuple holding the positionally corresponding values
    :return: the value positionally corresponding to the source string, or *None* if not found
    """
    # noinspection PyUnusedLocal
    result: Any = None
    with suppress(Exception):
        pos: int = keys.index(s)
        result = values[pos]

    return result


def str_random(size: int,
               chars: str | list[str] = None) -> str:
    """
    Generate and return a random string containing *len* characters.

    If *chars* is  provided, either as a string or as a list of characters, the characters
    therein will be used in the construction of the random string. Otherwise, a concatenation of
    *string.ascii_letters*, *string.digits*, and *string.punctuation* will provide the base characters.

    :param size: the length of the target random string
    :param chars: optional characters to build the random string from (a string or a list of characters)
    :return: the random string
    """
    # establish the base characters
    if not chars:
        chars: str = string.ascii_letters + string.digits + string.punctuation
    elif isinstance(chars, list):
        chars: str = "".join(chars)

    # generate and return the random string
    # ruff: noqa: S311 - Standard pseudo-random generators are not suitable for cryptographic purposes
    return "".join(random.choice(seq=chars) for _ in range(size))


def str_rreplace(s: str,
                 /,
                 old: str,
                 new: str,
                 count: int = 1) -> str:
    """
    Replace at most *count* occurrences of substring *old* with string *new* in *s*, in reverse order.

    :param s: the string to have a substring replaced
    :param old: the substring to replace
    :param new: the string replacement
    :param count: the maximum number of replacements (defaults to 1)
    :return: the modified string
    """
    return s[::-1].replace(old[::-1], new[::-1], count)[::-1]


def str_splice(s: str,
               /,
               seps: tuple[str, ...]) -> tuple[str, ...]:
    """
    Splice *s* into segments delimited by the ordered list of separators *seps*.

    The number of segments returned is always the number of separators in *seps*, plus 1.
    An individual segment returned can be null or an empty string. If no separators are found,
    the returned tuple will contain *s* as its last element, and *None* as the remaining elements.
    Separators will not be part of their respective segments.

    Separators in *seps* can not be *None* or empty strings. If no separators are provided
    (*seps* itself is an empty list), then the returned tuple will contain *s* as its only element.
    If *s* starts with the separator, then the return tuple's first element will be an empty string.
    If *s* ends with the separator, then the return tuple's last element will be an empty string.

    These examples illustrate the various possibilities (*s* = 'My string to be spliced'):
      - () ===> ('My string to be spliced',)
      - ('My') ===> ('',  'string to be spliced')
      - ('tri') ===> ('My s', 'ng to be spliced')
      - ('iced') ===> ('My string to be spl', '')
      - ('X', 'B') ===> (None, None, 'My string to be spliced')
      - ('M', 'd') ===> ('', 'y string to be splice', '')
      - ('s', 's', 'd') ===> ('My ', 'tring to be ', 'plice', '')
      - ('X', 'ri', 'be') ===> (None, 'My st', 'ng to ', ' spliced')

    :param s: the source string
    :param seps: the ordered list of separators
    :return: tuple with the segments obtained, or *None* if *s* is not a string

    """
    # initialize the return variable
    result: tuple[str, ...] | None = None

    if isinstance(s, str) and None not in seps and "" not in seps:
        segments: list[str | None] = []
        for sep in seps:
            pos: int = s.find(sep)
            if pos < 0:
                segments.append(None)
            else:
                segments.append(s[:pos])
                s = s[pos + len(sep):]
                if not s:
                    break

        segments.append(s)
        segments.extend([None] * (len(seps) - len(segments)))
        result = tuple(segments)

    return result


def str_to_lower(s: str, /) -> str:
    """
    Safely convert *s* to lower-case.

    If *s* is not a *str*, then it is itself returned.

    :param s: the string to convert to lower-case
    :return: *s* in lower-case, or *s* itself, if is not a string
    """
    return s.lower() if isinstance(s, str) else s


def str_to_upper(s: str, /) -> str:
    """
    Safely convert *s* to upper-case.

    If *s* is not a *str*, then it is itself returned.

    :param s: the string to convert to upper-case
    :return: *s* in upper-case, or *s* itself, if it is not a string
    """
    return s.upper() if isinstance(s, str) else s


def str_from_any(s: Any, /) -> str:
    """
    Convert *s* to its string representation.

    These are the string representations returned:
        - *None*: the string 'None'
        - *bool*: the string 'True' of 'False'
        - *str* : the source string itself
        - *bytes*: its hex representation
        - *date*: the date in ISO format (*datetime* is a *date* subtype)
        - *Path*: its POSIX form
        - all other types: their *str()* representation

    :param s: the data to be converted to string.
    :return: the string representation of the source data
    """
    # declare the return variable
    result: str

    # obtain the string representation
    if isinstance(s, bytes):
        result = s.hex()
    elif isinstance(s, date):
        result = s.isoformat()
    elif isinstance(s, Path):
        result = s.as_posix()
    else:
        result = str(s)

    return result


def str_to_bool(s: str, /) -> bool | None:
    """
    Obtain and return the *bool* value encoded in *s*.

    These are the criteria:
        - case is disregarded
        - the string values accepted to stand for *True* are *1*, *t*, or *true*
        - the string values accepted to stand for *False* are *0*, *f*, or *false*
        - all other values causes *None* to be returned

    :param s: the encoded bool value
    :return: the decoded bool value, or *None* if *s* fails the encoding criteria
    """
    # initialize the return variable
    result: bool | None = None

    if s in ["1", "t", "true"]:
        result = True
    elif s in ["0", "f", "false"]:
        result = False

    return result


def str_to_int(s: str, /) -> int | None:
    """
    Silently obtain and return the *int* value encoded in *s*.

    :param s: the encoded int value
    :return: the decoded *int* value, or *None* on error
    """
    # noinspection PyUnusedLocal
    result: int | None = None
    with suppress(Exception):
        result = int(s)

    return result


def str_to_float(s: str, /) -> float | None:
    """
    Silently obtain and return the *float* value encoded in *s*.

    :param s: the encoded float value
    :return: the decoded *float* value, or *None* on error
    """
    # noinspection PyUnusedLocal
    result: float | None = None
    with suppress(Exception):
        result = float(s)

    return result


def str_is_int(s: str, /) -> bool:
    """
    Determine whether *s* encodes a valid positive or negative integer.

    :param s: the encoded value
    :return: *True* if *s* encodes a valid integer, *False* otherwise
    """
    # declare the return variable
    result: bool

    try:
        int(s)
        result = True
    except ValueError:
        result = False

    return result


def str_is_float(s: str, /) -> bool:
    """
    Determine whether *s* encodes a valid positive or negative floating-point number.

    :param s: the encoded value
    :return: *True* if *s* encodes a valid floating-point number, *False* otherwise
    """
    # declare the return variable
    result: bool

    try:
        float(s)
        result = True
    except ValueError:
        result = False

    return result


def str_is_hex(s: str, /) -> bool:
    """
    Determine whether *s* encodes a valid hexadecimal integer.

    :param s: the encoded value
    :return: *True* if *s* encodes a valid hexadecimal number, *False* otherwise
    """
    # declare the return variable
    result: bool

    #  remove the prefix
    if s.startswith(("0x", "0X")):
        s = s[2:]
    try:
        int(s)
        result = True
    except ValueError:
        result = False

    return result
