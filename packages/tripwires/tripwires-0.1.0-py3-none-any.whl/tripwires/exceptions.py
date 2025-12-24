"""Custom exceptions for tripwires."""


class TripwiresError(Exception):
    """Base exception for all tripwires errors."""

    def __init__(self, message: str, path: str | None = None) -> None:
        """
        Initialize a tripwires error.

        Args:
            message: Error message
            path: Optional path associated with the error
        """
        self.path = path
        if path:
            message = f"{message}: {path}"
        super().__init__(message)


class ManifestError(TripwiresError):
    """Raised when there are issues with manifest files."""

    pass


class FileProcessingError(TripwiresError):
    """Raised when there are issues processing files (binary, encoding, etc.)."""

    pass


class ValidationError(TripwiresError):
    """Raised when validation fails (invalid paths, bad hashes, etc.)."""

    pass
