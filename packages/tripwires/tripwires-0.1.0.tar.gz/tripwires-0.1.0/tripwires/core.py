"""Core hashing and normalization functionality."""

from pathlib import Path

import xxhash

from tripwires.exceptions import FileProcessingError
from tripwires.file_types import is_binary_file


def normalize_content(content: str) -> str:
    """
    Normalize text content for cross-platform hashing.

    Normalization steps:
    1. Convert line endings to LF (\n)
    2. Remove trailing whitespace from each line
    3. Ensure exactly one newline at end of file

    Args:
        content: Raw text content

    Returns:
        Normalized text content
    """
    # Step 1: Normalize line endings to LF
    # Handle \r\n first, then \r
    content = content.replace("\r\n", "\n")
    content = content.replace("\r", "\n")

    # Step 2: Remove trailing whitespace from each line
    lines = content.split("\n")
    normalized_lines = [line.rstrip(" \t") for line in lines]
    content = "\n".join(normalized_lines)

    # Step 3: Ensure exactly one newline at end of file
    # Remove any trailing newlines, then add exactly one
    content = content.rstrip("\n")
    if content:  # Only add newline if file is not empty
        content += "\n"

    return content


def read_and_normalize_file(file_path: Path) -> str:
    """
    Read a file and return its normalized content.

    Reads the file as UTF-8 text, applies cross-platform content normalization
    (line ending conversion, whitespace cleanup), and returns the result.
    Binary files are rejected to ensure consistent hash behavior.

    Args:
        file_path: Path to the file to read

    Returns:
        Normalized file content ready for hashing

    Raises:
        FileNotFoundError: If the file does not exist
        FileProcessingError: If the file cannot be processed (binary, encoding issues, etc.)
    """
    # Check if it's a binary file (this will raise FileNotFoundError if file doesn't exist)
    if is_binary_file(file_path):
        raise FileProcessingError("Binary files are not supported", str(file_path))

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        # Let FileNotFoundError bubble up naturally
        raise
    except UnicodeDecodeError as e:
        raise FileProcessingError(f"Cannot decode file as UTF-8: {e}", str(file_path))
    except OSError as e:
        # Handle other IO errors (permissions, etc.)
        raise FileProcessingError(f"Cannot read file: {e}", str(file_path))

    return normalize_content(content)


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the fast xxHash3-128 hash of a normalized file.

    Reads the file, applies content normalization for cross-platform consistency,
    and returns the xxHash3-128 hash. This provides significantly better performance
    than SHA-256 while maintaining excellent hash quality and collision resistance
    for file integrity checking.

    Args:
        file_path: Path to the file to hash

    Returns:
        Lowercase hexadecimal xxHash3-128 hash string (32 characters)

    Raises:
        FileProcessingError: If the file cannot be processed (binary, encoding, etc.)
        FileNotFoundError: If the file does not exist
    """
    normalized_content = read_and_normalize_file(file_path)

    # Compute xxHash3-128 hash (much faster than SHA-256, excellent collision resistance)
    xxhash_hasher = xxhash.xxh3_128()
    xxhash_hasher.update(normalized_content.encode("utf-8"))

    return xxhash_hasher.hexdigest().lower()


def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """
    Verify that a file matches its expected hash.

    Convenience function that computes the current hash of a file and compares
    it to the expected value. Used internally by the checking logic.

    Args:
        file_path: Path to the file to verify
        expected_hash: Expected xxHash3-128 hash (lowercase hexadecimal, 32 characters)

    Returns:
        True if the file matches the expected hash, False otherwise

    Raises:
        FileProcessingError: If the file cannot be processed
    """
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash
