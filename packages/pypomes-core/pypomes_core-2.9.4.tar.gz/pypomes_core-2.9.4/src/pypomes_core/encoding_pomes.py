def encode_ascii_hex(source: bytes) -> bytes:
    r"""
    Encode binary content in *source* into text.

    This encoding is done with characters for bytes in the ASCII range, with the
    *backslash-escaped* representation for the special characters *LF*, *HT*, *CR*, *VT*, *FF* and *BS*,
    and with the representation *\\xNN* for the others (where *N* is a hexadecimal digit in *[0-9a-f]*).

    :param source: the binary content to be encoded
    :return: the encoded text content
    """
    # initialize the return variable
    result: bytes = b""

    # traverse 'source', encoding the non-ASCII bytes
    pos: int = 0
    while pos < len(source):
        char: bytes = source[pos:pos+1]
        if char != b"\\" and b" " <= char <= b"~":
            result += char                                  # char   - ASCII char, less the backslash
        else:
            byte_str: str
            match char:
                case b"\\":
                    byte_str = "\\\\"                       # \,  \\ - backslash
                case b"\x0A":
                    byte_str = "\\n"                        # LF, \n - line feed
                case b"\x0D":
                    byte_str = "\\r"                        # CR, \r - carriage return
                case b"\x09":
                    byte_str = "\\t"                        # HT, \t - horizontal tab
                case b"\x0B":
                    byte_str = "\\v"                        # VT, \v - vertical tab
                case b"\x0C":
                    byte_str = "\\f"                        # FF, \f  - form feed
                case b"\x08":
                    byte_str = "\\b"                        # BS, \b - backspace
                case _:
                    int_char = int.from_bytes(char, "little")
                    lower_char: int = int_char % 16             # \xNN
                    upper_char: int = round((int_char - lower_char) / 16)
                    byte_str = "\\x" + hex(upper_char)[2:] + hex(lower_char)[2:]

            result += byte_str.encode(encoding="utf-8")

        pos += 1

    return result


def decode_ascii_hex(source: bytes) -> bytes:
    r"""
    Decode text content in *source* into binary.

    This decoding is done for character-encoding text to bytes in the ASCII range, with the
    *backslash-escaped* representation for the special characters LF, HT, CR, VT, FF and BS,
    and with the representation *\\xNN* for the others (where *N* is a hexadecimal digit [0-9a-f]).

    :param source: the text content to be decoded
    :return: the decoded binary content
    """
    # initialize the return variable
    result: bytes = b""

    # traverse 'source', decoding the occurrences of '\'
    byte_val: bytes
    pos1: int = 0
    # locate the first '\'
    pos2: int = source.find(b"\\")
    while pos2 >= 0:
        result += source[pos1:pos2]
        next_byte: bytes = source[pos2+1:pos2+2]
        shift: int = 2
        match next_byte:
            case b"x":
                # '\x' prefixes a character denoted by a hexadecimal string ('\x00' through '\xff')
                # HAZARD: intermediate chars are necessary - 'int(byte)' breaks for byte > '\x09'
                upper_char: str = source[pos2+2:pos2+3].decode()
                lower_char: str = source[pos2+3:pos2+4].decode()
                int_val: int = 16 * int(upper_char, base=16) + int(lower_char, base=16)
                byte_val = bytes([int_val])
                shift = 4
            case b"n":
                byte_val = b"\x0A"                  # LF, \n - line feed
            case b"r":
                byte_val = b"\x0D"                  # CR, \r - carriage return
            case b"t":
                byte_val = b"\x09"                  # HT, \t - horizontal tab
            case b"v":
                byte_val = b"\x0B"                  # VT, \v - vertical tab
            case b"f":
                byte_val = b"\x0C"                  # FF, \f - form feed
            case b"b":
                byte_val = b"\x08"                  # BS, \b  - backspace
            case _:
                byte_val = source[pos2+1:pos2+2]    # byte following '\'

        pos1 = pos2 + shift
        result += byte_val
        # locate the next '\'
        pos2 = source.find(b"\\", pos1)

    result += source[pos1:]

    return result
