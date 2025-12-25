import filetype
import puremagic
import mimetypes
from contextlib import suppress
from enum import StrEnum
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import gettempdir
from typing import Final

from .env_pomes import APP_PREFIX, env_get_path

TEMP_FOLDER: Final[Path] = env_get_path(key=f"{APP_PREFIX}_TEMP_FOLDER",
                                        def_value=Path(gettempdir()))


# see https://mimetype.io/all-types
class Mimetype(StrEnum):
    """
    Commonly used mimetypes.
    """
    AAC = "audio/aac"
    AVI = " video/x-msvideo"
    BINARY = "application/octet-stream"
    BMP = "image/bmp"
    BZIP = "application/x-bzip"
    CSS = "text/css"
    CSV = "text/csv"
    DER = "application/x-x509-ca-cert"
    DOC = "application/msword"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DWG = "image/vnd.dwg"
    EXE = "application/x-msdownload"
    FLAC = "audio/x-flac"
    FLV = "video/x-flv"
    GIF = "image/gif"
    GZIP = "application/gzip"
    HTML = "text/html"
    ICO = "image/x-icon"
    JAR = "application/java-archive"
    JAVASCRIPT = "text/javascript"
    JPEG = "image/jpeg"
    JPX = "image/jpx"
    JS = "text/javascript"
    JSON = "application/json"
    MKV = "video/x-matroska"
    MSWORD = "application/msword"
    MP3 = "audio/mpeg"
    MP4 = "video/mp4"
    MPEG = "video/mpeg"
    MIDI = "audio/midi"
    MULTIPART = "multipart/form-data"
    ODP = "application/vnd.oasis.opendocument.presentation"
    ODS = "application/vnd.oasis.opendocument.spreadsheet"
    OGG = "audio/ogg"
    P7B = "application/x-pkcs7-certificates"
    P7S = "application/pkcs7-signature"
    PDF = "application/pdf"
    PNG = "image/png"
    PPT = "application/vnd.ms-powerpoint"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    PSD = "image/vnd.adobe.photoshop"
    RAR = "application/x-rar-compressed"
    RTF = "application/rtf"
    SOAP = "application/soap+xml"
    SWF = "application/x-shockwave-flash"
    TEXT = "text/plain"
    TIFF = "image/tiff"
    URLENCODED = "application/x-www-form-urlencoded"
    WASM = "application/wasm"
    WAV = "audio/x-wav"
    WEBM = "audio/webm"
    WEBP = "image/webp"
    X7Z = "application/x-7z-compressed"
    XLS = "application/vnd.ms-excel"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    XML = "application/xml"
    ZIP = "application/zip"


def file_get_data(file_data: BytesIO | StringIO | Path | str | bytes,
                  max_len: int = None,
                  chunk_size: int = None) -> bytes | None:
    """
    Retrieve the data in *file_data*, as implicitly defined by its data type.

    The distinction is made with the parameter's type:
        - type *BytesIO*: *file_data* is a stream of bytes (collect and returned as is)
        - type *StringIO*: *file_data* is a stream of characters (collect and returned as utf8-encoded)
        - type *Path*: *file_data* is a path to a file holding the data
        - type *str*: *file_data* holds the data (returned as utf8-encoded)
        - type *bytes*: *file_data* holds the data (returned as is)

    :param file_data: the data as implicitly defined by its data type
    :param max_len: optional maximum length of the data to return, defaults to all data
    :param chunk_size: optional chunk size to use in reading the data, defaults to 128 KB
    :return: the data, or *None* if the file data could not be obtained
    """
    # initialize the return variable
    result: bytes | None = None

    # normalize the maximum length parameter
    if isinstance(max_len, bool) or \
       not isinstance(max_len, int) or max_len < 0:
        max_len = 0

    # normalize the chunk size
    if isinstance(chunk_size, bool) or \
       not isinstance(chunk_size, int) or chunk_size <= 0:
        chunk_size = 128 * 1024

    # what is the argument type ?
    if isinstance(file_data, bytes):
        # argument is type 'bytes'
        result = file_data

    elif isinstance(file_data, str):
        # argument is type 'str'
        result = file_data.encode(encoding="utf-8")

    elif isinstance(file_data, BytesIO | StringIO):
        # argument is type 'stream'
        file_data.seek(0)
        result = file_data.read()
        if isinstance(result, str):
            result = result.encode(encoding="utf-8")

    elif isinstance(file_data, Path):
        # argument is a file path
        file_bytes: bytearray = bytearray()
        file_path: Path = Path(file_data)
        # get the data
        with file_path.open(mode="rb") as f:
            buf_size: int = min(max_len, chunk_size) if max_len else chunk_size
            in_bytes: bytes = f.read(buf_size)
            while in_bytes:
                file_bytes += in_bytes
                if max_len:
                    if max_len <= len(file_bytes):
                        break
                    buf_size = min(max_len - len(file_bytes), chunk_size)
                else:
                    buf_size = chunk_size
                in_bytes = f.read(buf_size)
        result = bytes(file_bytes)

    if result and max_len and len(result) > max_len:
        result = result[:max_len]

    return result


def file_get_extension(mimetype: Mimetype | str) -> str | None:
    """
    Obtain and return the file extension best associated with mime type *mimetype*.

    This complements Python's *mimetypes.guess_extension()*, which fails for a number of
    frequently used mime types. In those cases, if *mimetype* is an instance of *Mimetype*,
    its *enum* name is used as extension. For consistency, the extension is returned as a
    lowercase string, with the leading dot ('.').

    :param mimetype: the reference mime type
    :return: the extension, with the leading dot ('.'), best associated with *mimetype*, or *None* on fail.
    """
    # initialize the return variable
    result: str = mimetypes.guess_extension(type=mimetype)

    if not result and mimetype in Mimetype:
        mimetype = Mimetype(mimetype)
        # noinspection PyProtectedMember
        result = f".{mimetype._name_.lower()}"

    return result


def file_get_mimetype(file_data: Path | str | bytes) -> Mimetype | str:
    """
    Heuristics to determine the mimetype for *file_data*.

    The content is retrieved for analysis according to *file_data*'s type:
        - type *bytes*: *file_data* holds the data
        - type *str*: *file_data* holds the data as utf8-encoded
        - type *Path*: *file_data* is a path to a file holding the data

    The heuristics used, as heuristics go, provides an educated guess, not an accurate result.
    If a mimetype is found, and it is not in *Mimetype* (which is a small subset of known mimetypes),
    then its identifying string is returned.

    :param file_data: file data, or the path to locate the file
    :return: the probable mimetype, as a *Mimetype* object or as a string
    """
    mimetype: str | None = None
    if isinstance(file_data, str):
        file_data = file_data.encode()
    with suppress(TypeError):
        kind: filetype.Type = filetype.guess(obj=file_data)
        if kind:
            mimetype = kind.mime

    if not mimetype:
        with suppress(puremagic.PureError):
            if isinstance(file_data, Path):
                mimetype = puremagic.from_file(filename=file_data,
                                               mime=True)
            else:
                mimetype = puremagic.from_string(string=file_data,
                                                 mime=True)
    result: Mimetype | str
    if mimetype:
        # for unknown mimetypes, return its identifying string
        result = Mimetype(mimetype) if mimetype in Mimetype else mimetype
    elif file_is_binary(file_data=file_data):
        result = Mimetype.BINARY
    else:
        result = Mimetype.TEXT

    return result


def file_is_binary(file_data: Path | str | bytes) -> bool:
    """
    Heuristics to determine whether the content of *file_data* is binary.

    The content is retrieved for analysis according to *file_data*'s type:
        - type *bytes*: *file_data* holds the data
        - type *str*: *file_data* holds the data as utf8-encoded
        - type *Path*: *file_data* is a path to a file holding the data

    The heuristics used, as heuristics go, provide an educated guess, not an accurate result.
    In the present case, the first 4 KBytes of the file data is inspected for the occurrence
    of characters normally absent in text files. Thus the presence of characters other than
    *bell*, *backspace*, *horizontal tab*, *newline*, *form feed*, *carriage return*, *escape*,
    and those in ASCII range [32 - 255] (except 127), would flag the file as binary.
    Empty or null content is considered to be non-binary.

    :param file_data: file data, or the path to locate the file
    :return: *True* if the determination resulted positive, *False* otherwise
    """
    # obtain up to 1024 bytes of content for analysis
    chunk: bytes = file_get_data(file_data=file_data,
                                 max_len=4096) or b""
    # check for null byte
    result: bool = b"\0" in chunk

    # check for non-printable characters
    if not result:
        # remove the chars listed below - chars remaining indicates content is binary
        #    7: \a (bell)
        #    8: \b (backspace)
        #    9: \t (horizontal tab)
        #   10: \n (newline)
        #   12: \f (form feed)
        #   13: \r (carriage return)
        #   27: \x1b (escape)
        #   0x20 - 0x100, less 0x7f: 32-255 char range, less 127 (the DEL control char)
        text_characters = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        translation: bytes = chunk.translate(None,
                                             delete=text_characters)
        result = bool(translation)

    return result
