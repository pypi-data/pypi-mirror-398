"""File type detection and binary file handling."""

from pathlib import Path

# Comprehensive list of known text file extensions
TEXT_EXTENSIONS: set[str] = {
    # Programming languages
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".cxx",
    ".cc",
    ".h",
    ".hpp",
    ".hxx",
    ".cs",
    ".php",
    ".rb",
    ".pl",
    ".swift",
    ".kt",
    ".scala",
    ".clj",
    ".hs",
    ".elm",
    ".ex",
    ".exs",
    ".lua",
    ".r",
    ".R",
    ".m",
    ".mm",
    ".f",
    ".f90",
    ".f95",
    ".pas",
    ".pp",
    ".inc",
    ".asm",
    ".s",
    ".go",
    ".rs",
    # Web technologies
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".xml",
    ".svg",
    # Configuration and data formats
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
    ".properties",
    ".env",
    ".envrc",
    # Documentation and text
    ".md",
    ".txt",
    ".rst",
    ".adoc",
    ".tex",
    ".rtf",
    # Shell and scripts
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".bat",
    ".cmd",
    ".ps1",
    # SQL and database
    ".sql",
    ".ddl",
    ".dml",
    # Special files (without dots)
    ".dockerfile",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".gitmodules",
    ".gitkeep",
    ".npmignore",
    ".dockerignore",
}

# Files without extensions that are typically text
TEXT_FILENAMES: set[str] = {
    "Dockerfile",
    "Makefile",
    "Rakefile",
    "Gemfile",
    "Pipfile",
    "LICENSE",
    "README",
    "CHANGELOG",
    "CONTRIBUTING",
    "AUTHORS",
}


def is_text_file(file_path: Path) -> bool:
    """
    Determine if a file should be treated as a text file.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file should be treated as text, False otherwise
    """
    # Check by extension
    if file_path.suffix.lower() in TEXT_EXTENSIONS:
        return True

    # Check by filename for files without extensions
    if file_path.name in TEXT_FILENAMES:
        return True

    return False


def has_null_bytes(file_path: Path, max_bytes: int = 8192) -> bool:
    """
    Check if a file contains null bytes in the first max_bytes.

    Args:
        file_path: Path to the file to check
        max_bytes: Maximum number of bytes to read (default 8KB)

    Returns:
        True if null bytes are found, False otherwise
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(max_bytes)
            return b"\x00" in chunk
    except OSError:
        # If we can't read the file, assume it's binary
        return True


def is_binary_file(file_path: Path) -> bool:
    """
    Determine if a file is binary and should not be processed.

    Uses extension allowlist first, then falls back to null byte detection.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file is binary, False if it's text
    """
    # First check if it's a known text file type
    if is_text_file(file_path):
        return False

    # For unknown extensions, check for null bytes
    return has_null_bytes(file_path)
