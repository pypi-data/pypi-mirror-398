"""
Console output implementation with emoji-friendly formatting.

This module implements the default human-readable output format for tripwires.
The output follows a clear flow:

1. report_start() - Shows operation beginning and scope
2. report_file_result() - Called once per file during processing (real-time feedback)
3. report_summary() - Shows aggregated results at the end
4. report_error() - Used for system/operational errors (separate from file check failures)
"""


from tripwires.model import CheckResult
from tripwires.output.base import OutputInterface


class ConsoleOutput(OutputInterface):
    """
    Default console output with emoji-friendly formatting.

    Designed for interactive use where users want real-time feedback
    and a clear summary of results.
    """

    def report_start(self, manifest_path: str, file_count: int) -> None:
        """
        Report the start of a check operation.

        Called once at the beginning to give users context about what's happening.
        Shows the manifest being used and how many files will be processed.
        """
        print(f"🔍 Checking {file_count} files using manifest: {manifest_path}")

    def report_file_result(self, result: CheckResult) -> None:
        """
        Report the result of checking a single file.

        Called once per file as it's being processed, providing real-time feedback.
        This gives users immediate visibility into which files pass/fail without
        waiting for the entire operation to complete.

        Note: This is for individual file results, not system errors.
        """
        if result.is_match:
            print(f"✅ {result.path}")
        elif result.is_mismatch:
            print(f"❌ {result.path} (hash mismatch)")
        elif result.is_error:  # pragma: no branch
            print(f"🚫 {result.path} ({result.error_message})")

    def report_summary(self, results: list[CheckResult]) -> None:
        """
        Report a summary of all results after processing completes.

        Called once at the end to provide an aggregated view of all file results.
        This helps users quickly understand the overall outcome without having
        to mentally tally up the individual file results.

        Uses the base class helper method to calculate statistics, then formats
        them in a human-readable way.
        """
        stats = self._calculate_summary_stats(results)

        print("\n📊 Summary:")
        print(f"   Total files: {stats['total']}")
        print(f"   ✅ Matches: {stats['matches']}")

        # Only show problem categories if they exist
        if stats["mismatches"] > 0:
            print(f"   ❌ Mismatches: {stats['mismatches']}")

        if stats["errors"] > 0:
            print(f"   🚫 Errors: {stats['errors']}")

        # Status message based on results
        if stats["mismatches"] == 0 and stats["errors"] == 0:
            print("🎉 All files match their expected hashes!")
        elif stats["mismatches"] > 0 and stats["errors"] == 0:
            print("⚠️ Some files don't match their expected hashes!")
        elif stats["mismatches"] == 0 and stats["errors"] > 0:
            print("🚫 Some files had errors during processing!")
        else:  # Both mismatches and errors
            print("❌ Issues found: files with hash mismatches and processing errors!")

    def report_error(self, message: str) -> None:
        """
        Report a system/operational error.

        Used for errors that prevent the operation from proceeding normally,
        such as:
        - Cannot read manifest file
        - Cannot write to manifest file
        - Invalid manifest format
        - Permission errors

        This is different from report_file_result() which handles per-file
        check failures (hash mismatches, unreadable files, etc.).
        """
        print(f"❌ Error: {message}")
