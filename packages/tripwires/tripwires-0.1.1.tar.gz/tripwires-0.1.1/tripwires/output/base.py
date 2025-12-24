"""Abstract base class for output interfaces."""

from abc import ABC, abstractmethod
from pathlib import Path

from tripwires.model import CheckResult


class OutputInterface(ABC):
    """Abstract interface for outputting tripwires results."""

    @abstractmethod
    def report_start(self, manifest_path: str, file_count: int) -> None:
        """Report the start of a check operation."""
        pass  # pragma: no cover

    @abstractmethod
    def report_file_result(self, result: CheckResult) -> None:
        """Report the result of checking a single file."""
        pass  # pragma: no cover

    @abstractmethod
    def report_summary(self, results: list[CheckResult]) -> None:
        """Report a summary of all results."""
        pass  # pragma: no cover

    def report_update_start(self, manifest_path: str, file_count: int) -> None:
        """Report the start of an update operation."""
        print(f"🔄 Updating {file_count} file hashes in manifest: {manifest_path}")

    def report_file_updated(self, path: str, new_hash: str) -> None:
        """Report that a file's hash was updated."""
        print(f"📝 {path} → {new_hash[:8]}...")

    def report_update_complete(self, updated_count: int) -> None:
        """Report completion of update operation."""
        print(f"\n✨ Updated {updated_count} file hashes successfully!")

    @abstractmethod
    def report_error(self, message: str) -> None:
        """Report an error message."""
        pass  # pragma: no cover

    def report_init_success(self, manifest_path: Path) -> None:
        """Report successful initialization of a manifest file."""
        print(f"✨ Created empty manifest: {manifest_path}")
        print("📝 Add files to protect by editing the manifest or running:")
        print(
            f'   echo \'  "path/to/file.py": "placeholder_64char_hash"\' >> {manifest_path.name}'
        )
        print("   tripwires update")

    # Helper methods for data preparation (can be overridden if needed)
    def _calculate_summary_stats(self, results: list[CheckResult]) -> dict[str, int]:
        """Calculate summary statistics from results."""
        return {
            "total": len(results),
            "matches": sum(1 for r in results if r.is_match),
            "mismatches": sum(1 for r in results if r.is_mismatch),
            "errors": sum(1 for r in results if r.is_error),
        }

    def _group_results_by_status(
        self, results: list[CheckResult]
    ) -> dict[str, list[CheckResult]]:
        """Group results by their status for easier processing."""
        return {
            "matches": [r for r in results if r.is_match],
            "mismatches": [r for r in results if r.is_mismatch],
            "errors": [r for r in results if r.is_error],
        }

    def _get_failures_only(self, results: list[CheckResult]) -> list[CheckResult]:
        """Return only failed/error results for failure-focused output."""
        return [r for r in results if r.is_mismatch or r.is_error]

    def determine_exit_code(self, results: list[CheckResult]) -> int:
        """
        Determine the exit code based on results.

        Override this method in custom output classes to implement different
        exit code policies (e.g., warning-only mode, custom thresholds, etc.).

        Default behavior:
        - 0: All files match their expected hashes
        - 1: Hash mismatches detected
        - 2: File processing errors occurred

        Args:
            results: List of check results

        Returns:
            Exit code (0-255)
        """
        has_errors = any(r.is_error for r in results)
        has_mismatches = any(r.is_mismatch for r in results)

        if has_errors:
            return 2
        elif has_mismatches:
            return 1
        else:
            return 0
