"""
File I/O operations for MCard.

This module handles safe file reading, streaming, and directory traversal.
It is designed to be robust against large files, binary content, and pathological text.
"""

import hashlib
import logging
import time
import threading
from pathlib import Path
from typing import Any, Optional, Union, List

from mcard.config.settings import settings
from mcard.model.interpreter import ContentTypeInterpreter

logger = logging.getLogger(__name__)


def soft_wrap_long_lines(text: str, max_line_length: int = 1000) -> str:
    """Insert newlines into very long single lines to prevent pathological processing.
    This is a safe text normalization step for minified or long-line content.
    """
    if max_line_length <= 0:
        return text
    out_lines: list[str] = []
    for line in text.splitlines() or [text]:
        if len(line) <= max_line_length:
            out_lines.append(line)
            continue
        # Chunk the long line
        for i in range(0, len(line), max_line_length):
            out_lines.append(line[i : i + max_line_length])
    # Preserve trailing newline if present in input
    result = "\n".join(out_lines)
    return result


def stream_read_normalized_text(
    file_path: Path, *, byte_cap: int, wrap_width: int
) -> dict[str, Any]:
    """Stream-read bytes up to byte_cap, decode with replacement, and insert soft wraps on the fly.
    Returns dict with keys: text, original_size, original_sha256_prefix.
    """
    sha = hashlib.sha256()
    total_size = 0
    produced_chars: list[str] = []
    current_len = 0
    with open(file_path, "rb") as f:
        remaining = byte_cap
        while remaining > 0:
            chunk = f.read(min(8192, remaining))
            if not chunk:
                break
            sha.update(chunk)
            total_size += len(chunk)
            remaining -= len(chunk)
            try:
                s = chunk.decode("utf-8", errors="replace")
            except Exception:
                s = chunk.decode("latin-1", errors="replace")
            for ch in s:
                if ch == "\r":
                    # Normalize CR to nothing; let CRLF become just LF via the subsequent '\n'
                    continue
                produced_chars.append(ch)
                if ch == "\n":
                    current_len = 0
                else:
                    current_len += 1
                    if wrap_width > 0 and current_len >= wrap_width:
                        produced_chars.append("\n")
                        current_len = 0
    return {
        "text": "".join(produced_chars),
        "original_size": total_size,
        "original_sha256_prefix": sha.hexdigest()[:16],
    }


def read_file_safely(
    file_path: Union[str, Path],
    allow_pathological: bool = False,
    max_bytes: Optional[int] = None,
) -> bytes:
    """
    Read file content with timeout protection and size limits.

    Args:
        file_path: Path to the file to read
        allow_pathological: If True, bypass long-line/pathological content checks
        max_bytes: If set, cap the number of bytes read to this value

    Returns:
        File content as bytes

    Raises:
        TimeoutError: If reading takes too long
        IOError: If file cannot be read
    """
    file_path = Path(file_path)
    
    # Check file size first
    try:
        file_size = file_path.stat().st_size
    except OSError as e:
        raise OSError(f"Cannot access file {file_path}: {e}")

    max_file_size = 50 * 1024 * 1024  # 50MB limit

    if file_size > max_file_size:
        raise OSError(f"File too large: {file_size} bytes (max {max_file_size})")

    # Timeout configurable with a small bias for larger files
    base_timeout = settings.file_processing.read_timeout_secs
    timeout_seconds = (
        5.0 if file_size > 50 * 1024 and base_timeout >= 5 else base_timeout
    )

    result = [None]
    exception = [None]

    def read_with_timeout():
        try:
            with open(file_path, "rb") as file:
                # For potentially problematic files, read in chunks with progress checking
                if (
                    file_size > 50 * 1024 or max_bytes is not None
                ):  # Files > 50KB or when capping
                    content = bytearray()
                    chunk_size = 8192
                    bytes_read = 0
                    start_time = time.time()

                    to_read = max_bytes if max_bytes is not None else file_size

                    while bytes_read < to_read:
                        if time.time() - start_time > timeout_seconds:
                            raise TimeoutError(
                                f"Reading timeout exceeded for {file_path}"
                            )

                        remaining = to_read - bytes_read
                        chunk = file.read(min(chunk_size, remaining))
                        if not chunk:
                            break
                        content.extend(chunk)
                        bytes_read += len(chunk)

                        # Check for pathological content patterns during reading unless allowed
                        if (
                            (not allow_pathological)
                            and len(content) > 32768
                            and b"\n" not in content
                            and b"\r" not in content
                        ):
                            raise OSError(
                                f"File appears to be a single massive line: {file_path}"
                            )

                    result[0] = bytes(content)
                else:
                    result[0] = file.read()
        except Exception as e:
            exception[0] = e

    # Use threading for timeout since signal doesn't work well on all platforms
    thread = threading.Thread(target=read_with_timeout)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        # Thread is still running, reading is taking too long
        logger.warning(
            f"File reading timed out after {timeout_seconds}s: {file_path}"
        )
        raise TimeoutError(f"File reading timed out for {file_path}")

    if exception[0]:
        logger.error(f"Error reading file {file_path}: {exception[0]}")
        raise exception[0]

    if result[0] is None:
        raise OSError(f"Failed to read file: {file_path}")

    return result[0]


def is_problematic_file(file_path: Path) -> bool:
    """
    Check if a file is likely to cause processing issues.
    """
    try:
        file_size = file_path.stat().st_size

        # Skip empty files
        if file_size == 0:
            return False

        # If it's a known type that can have long lines, be more permissive
        file_extension = file_path.suffix.lower()
        is_known_type = ContentTypeInterpreter._is_known_long_line_extension(
            file_extension
        )

        # For known types, still have size limits to prevent pathological cases
        if is_known_type and file_size > 1024 * 1024:  # 1MB limit for known types
            logger.warning(
                f"Skipping large file of known type: {file_path} ({file_size} bytes)"
            )
            return True

        with open(file_path, "rb") as f:
            # Sample from beginning, middle, and end for large files
            sample_size = min(32 * 1024, file_size)  # 32KB sample
            samples = []

            if (
                file_size > 100 * 1024
            ):  # For files > 100KB, check multiple positions
                positions = [0, file_size // 2, max(0, file_size - sample_size)]
            else:
                positions = [0]

            for pos in positions:
                f.seek(pos)
                sample = f.read(sample_size)
                if sample:
                    samples.append(sample)

            for sample in samples:
                # Check for binary content that's not structured
                if ContentTypeInterpreter._is_unstructured_binary(sample):
                    logger.warning(
                        f"Skipping unstructured binary file: {file_path}"
                    )
                    return True

                # Check for pathological line patterns
                if ContentTypeInterpreter._has_pathological_lines(
                    sample, is_known_type
                ):
                    logger.warning(
                        f"Skipping file with pathological line structure: {file_path}"
                    )
                    return True

        return False

    except Exception as e:
        logger.warning(f"Error checking file {file_path}: {e}")
        return True  # Skip files we can't check


def list_files(directory: Union[str, Path], recursive: bool = False) -> List[Path]:
    """
    Load all files from the specified directory.
    Explicitly skips hidden files and directories (starting with .).
    """
    import os
    dir_path = Path(directory) if isinstance(directory, str) else directory
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory '{dir_path}' does not exist.")

    safe_files = []
    
    if recursive:
        for root, dirs, filenames in os.walk(str(dir_path)):
            # Modify dirs in-place to skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                    
                file_path = Path(root) / filename
                if not is_problematic_file(file_path):
                    safe_files.append(file_path)
    else:
        # Non-recursive: just list top level
        # os.walk matches this if we break, but simpler usually:
        for item in dir_path.iterdir():
            if item.name.startswith('.'):
                continue
            if item.is_file():
                if not is_problematic_file(item):
                    safe_files.append(item)

    logger.info(
        f"Found {len(safe_files)} safe files in {dir_path}"
    )
    return safe_files


def process_file_content(
    file_path: Union[str, Path],
    *,
    force_binary: bool = False,
    allow_pathological: bool = False,
    max_bytes: Optional[int] = None,
) -> dict[str, Any]:
    """
    Process a file and return its metadata and content.
    """
    # Read file content as bytes
    content = read_file_safely(
        file_path, allow_pathological=allow_pathological, max_bytes=max_bytes
    )

    # Analyze the content to get MIME type and other metadata
    # For very large files or files with extremely long lines, use a sample
    content_sample = content
    if len(content) > 1024 * 1024:  # 1MB limit for content type detection
        content_sample = content[: 1024 * 1024]
        logger.info(f"Using content sample for large file: {file_path}")

    mime_type, extension = ContentTypeInterpreter.detect_content_type(content_sample)
    is_binary = ContentTypeInterpreter.is_binary_content(content_sample)

    # Force binary mode if requested
    if force_binary:
        is_binary = True
        # If detection thought it's text, override to a safe default
        if not mime_type or mime_type.startswith("text/"):
            mime_type = "application/octet-stream"

    # For text files, try to decode the content
    if not is_binary and mime_type.startswith("text/"):
        try:
            # Decode the content as UTF-8 for text files
            content = content.decode("utf-8")
        except UnicodeDecodeError:
            # If UTF-8 fails, try with error replacement
            try:
                content = content.decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning(
                    f"Failed to decode content for {file_path} as UTF-8: {e}"
                )

    return {
        "content": content,
        "filename": Path(file_path).name,
        "mime_type": mime_type,
        "extension": extension,
        "is_binary": is_binary,
        "size": len(content),  # Use original content size, not sample
    }
