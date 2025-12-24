"""Tripwires - Lightweight guardrails for AI-assisted development teams."""

__version__ = "0.1.0"
__author__ = "tripwires contributors"

from tripwires.exceptions import (
    FileProcessingError,
    ManifestError,
    TripwiresError,
    ValidationError,
)
from tripwires.model import CheckResult, Manifest

__all__ = [
    "CheckResult",
    "FileProcessingError",
    "Manifest",
    "ManifestError",
    "TripwiresError",
    "ValidationError",
    "__version__",
]
