"""Command-line interface for tripwires."""

import sys
from pathlib import Path

import typer

from tripwires.core import compute_file_hash
from tripwires.exceptions import FileProcessingError, ManifestError, ValidationError
from tripwires.manifest import load_manifest, write_manifest
from tripwires.model import CheckResult, CheckStatus, Manifest
from tripwires.output import ConsoleOutput, OutputInterface

app = typer.Typer(
    name="tripwires",
    help="Lightweight guardrails for AI-assisted development teams",
    add_completion=False,
)


def get_manifest_path(manifest: str | None) -> Path:
    """
    Get the manifest path from an optional string.

    Args:
        manifest: Optional manifest path string

    Returns:
        Path object (default: ./tripwires.yml)
    """
    if manifest is None:
        return Path("tripwires.yml")
    return Path(manifest)


def get_output_interface(custom_class: str | None = None) -> OutputInterface:
    """
    Get the output interface to use for reporting.

    Loads a custom output class if specified, otherwise falls back to console output.
    The custom class can be specified via CLI flag or environment variable, with
    CLI flag taking priority.

    Args:
        custom_class: Optional fully qualified class name (e.g., "mymodule.MyOutput")

    Returns:
        OutputInterface instance (custom class or ConsoleOutput fallback)
    """
    import importlib
    import os

    # Priority: CLI flag > Environment variable > Default console
    output_class = custom_class or os.getenv("TRIPWIRES_OUTPUT_CLASS")

    if output_class:
        try:
            # Parse module.class format (e.g., "myproject.outputs.JsonOutput")
            module_name, class_name = output_class.rsplit(".", 1)
            module = importlib.import_module(module_name)
            output_cls = getattr(module, class_name)
            instance = output_cls()
            # We expect this to be an OutputInterface, but can't verify at runtime
            return instance  # type: ignore[no-any-return]
        except (ValueError, ImportError, AttributeError) as e:
            # Fall back to console output if custom class fails
            print(f"Warning: Failed to load custom output class '{output_class}': {e}")
            print("Falling back to console output.")

    return ConsoleOutput()


def check_files(manifest_path: Path, output: OutputInterface) -> list[CheckResult]:
    """
    Check all files in the manifest against their expected hashes.

    Loads the manifest, iterates through all tracked files, computes current hashes,
    and compares them against expected values. Reports results through the output
    interface and handles errors gracefully.

    Args:
        manifest_path: Path to the manifest file to load
        output: Output interface for reporting progress and results

    Returns:
        List of CheckResult objects containing status for each file

    Raises:
        SystemExit: On manifest loading errors (exit code 2)
    """
    try:
        manifest = load_manifest(manifest_path)
    except (ManifestError, ValidationError) as e:
        output.report_error(str(e))
        sys.exit(2)

    paths = manifest.get_paths()
    output.report_start(str(manifest_path), len(paths))

    results: list[CheckResult] = []

    for path_str in paths:
        file_path = Path(path_str).resolve()
        expected_hash = manifest.get_hash(path_str)

        try:
            actual_hash = compute_file_hash(file_path)

            if actual_hash == expected_hash:
                result = CheckResult(
                    path=path_str,
                    status=CheckStatus.MATCH,
                    expected_hash=expected_hash,
                    actual_hash=actual_hash,
                )
            else:
                result = CheckResult(
                    path=path_str,
                    status=CheckStatus.MISMATCH,
                    expected_hash=expected_hash,
                    actual_hash=actual_hash,
                )
        except FileProcessingError as e:
            result = CheckResult(
                path=path_str,
                status=CheckStatus.ERROR,
                expected_hash=expected_hash,
                error_message=str(e),
            )

        results.append(result)
        output.report_file_result(result)

    return results


def update_manifest_hashes(manifest_path: Path, output: OutputInterface) -> None:
    """
    Update all file hashes in the manifest.

    Recomputes hashes for all files tracked in the manifest and updates the
    manifest file with the new values. This is typically used after making
    deliberate changes to monitored files.

    Args:
        manifest_path: Path to the manifest file to update
        output: Output interface for reporting
    """
    try:
        manifest = load_manifest(manifest_path)
    except (ManifestError, ValidationError) as e:
        output.report_error(str(e))
        sys.exit(2)

    paths = manifest.get_paths()
    output.report_update_start(str(manifest_path), len(paths))

    updated_count = 0

    for path_str in paths:
        file_path = Path(path_str).resolve()

        try:
            new_hash = compute_file_hash(file_path)
            manifest.set_hash(path_str, new_hash)
            output.report_file_updated(path_str, new_hash)
            updated_count += 1
        except FileProcessingError as e:
            output.report_error(f"Cannot update {path_str}: {e}")
            sys.exit(2)

    # Write the updated manifest
    try:
        write_manifest(manifest, manifest_path)
    except ManifestError as e:
        output.report_error(str(e))
        sys.exit(2)

    output.report_update_complete(updated_count)


@app.command()
def check(
    manifest: str
    | None = typer.Option(
        None,
        "--manifest",
        "-m",
        help="Path to manifest file (default: ./tripwires.yml)",
    ),
    output_class: str
    | None = typer.Option(
        None,
        "--output-class",
        "-o",
        help="Custom output class (module.ClassName format)",
    ),
) -> None:
    """Check files against their expected hashes."""
    manifest_path = get_manifest_path(manifest)

    output = get_output_interface(output_class)

    try:
        results = check_files(manifest_path, output)
        output.report_summary(results)

        # Let the output interface determine the exit code
        exit_code = output.determine_exit_code(results)
        sys.exit(exit_code)

    except KeyboardInterrupt:  # pragma: no cover
        output.report_error("Operation cancelled by user")
        sys.exit(2)


@app.command()
def update(
    manifest: str
    | None = typer.Option(
        None,
        "--manifest",
        "-m",
        help="Path to manifest file (default: ./tripwires.yml)",
    )
) -> None:
    """Update file hashes in the manifest."""
    manifest_path = get_manifest_path(manifest)

    output = get_output_interface()

    try:
        update_manifest_hashes(manifest_path, output)
        sys.exit(0)
    except KeyboardInterrupt:  # pragma: no cover
        output.report_error("Operation cancelled by user")
        sys.exit(2)


@app.command()
def init(
    path: str
    | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Directory where to create tripwires.yml (default: current directory)",
    ),
    manifest: str
    | None = typer.Option(
        None,
        "--manifest",
        "-m",
        help="Name of manifest file to create (default: tripwires.yml)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing manifest file",
    ),
) -> None:
    """Initialize a new tripwires manifest file."""
    if path is None:
        target_dir = Path.cwd()
    else:
        target_dir = Path(path).resolve()

    if manifest is None:
        manifest_path = target_dir / "tripwires.yml"
    else:
        manifest_path_obj = Path(manifest)
        if manifest_path_obj.is_absolute():
            manifest_path = manifest_path_obj
        else:
            manifest_path = target_dir / manifest

    output = get_output_interface()

    # Check if file already exists
    if manifest_path.exists() and not force:
        output.report_error(f"Manifest file already exists: {manifest_path}")
        output.report_error("Use --force to overwrite")
        sys.exit(2)

    # Create empty manifest
    try:
        empty_manifest = Manifest(paths={})
        write_manifest(empty_manifest, manifest_path)

        # Report success
        output.report_init_success(manifest_path)

    except Exception as e:  # pragma: no cover
        output.report_error(f"Failed to create manifest: {e}")
        sys.exit(2)


if __name__ == "__main__":  # pragma: no cover
    app()
