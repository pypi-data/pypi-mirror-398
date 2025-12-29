from pathlib import Path

from blends.content.custom_parsers import custom_parsers_by_language
from blends.models import EXTENSION_TO_LANGUAGE, Content, Language
from blends.utils.logs import log_blocking

MAX_FILE_SIZE: int = 1024 * 500


class FileTooLargeError(Exception):
    pass


def get_language_by_path(path: Path) -> Language:
    return EXTENSION_TO_LANGUAGE.get(path.suffix.lower(), Language.NOT_SUPPORTED)


def _get_file_raw_content(file_path: Path, size: int = MAX_FILE_SIZE) -> bytes:
    file_size = file_path.stat().st_size
    if file_size > size:
        raise FileTooLargeError(str(file_path))

    with file_path.open("rb") as handle:
        return handle.read(size)


def get_content_by_path(
    path: Path,
    max_size: int = MAX_FILE_SIZE,
) -> Content | None:
    """Interface function for the content module.

    Loads and returns file content for a given path.
    Accepts a Path to a file and an optional maximum file size in bytes.
    Reads the file up to the specified size, decodes to string, and wraps both bytes and string
    in a Content object. Applies language-aware custom parsers and validators if applicable,
    returning parsed or validated content. Returns None if the file cannot be read or is too large.

    Expects:
        path: Path to the file to be read.
        max_size: Maximum allowed file size in bytes (default: 512 KB).

    Returns:
        Content object with bytes, string, and file size, or None if reading fails or file is too
        large.

    """
    content = None
    language = get_language_by_path(path)
    try:
        content_bytes = _get_file_raw_content(path, max_size)
        content_str = content_bytes.decode("utf-8", errors="ignore")
        content = Content(content_bytes, content_str, language, path)

    except FileTooLargeError:
        log_blocking("warning", "File too large: %s, ignoring", path)
        return None
    except (FileNotFoundError, PermissionError, OSError, IsADirectoryError):
        content = None
        log_blocking("error", "Error reading file: %s", str(path))
        return None
    if content and (language_parsers := custom_parsers_by_language.get(language)):
        for custom_parser in language_parsers:
            if custom_parser.validator(content) and (
                fixed_content := custom_parser.parser(content)
            ):
                return fixed_content

    return content
