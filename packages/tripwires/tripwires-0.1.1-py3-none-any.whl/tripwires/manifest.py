"""Manifest file loading, writing, and validation."""

from pathlib import Path
from typing import Any

import yaml

from tripwires.exceptions import ManifestError, ValidationError
from tripwires.model import Group, Manifest


def load_manifest(manifest_path: Path) -> Manifest:
    """
    Load and validate a manifest file.

    Args:
        manifest_path: Path to the manifest file

    Returns:
        Loaded and validated Manifest object

    Raises:
        ManifestError: If the manifest file is missing, invalid, or malformed
        ValidationError: If manifest contents are invalid
    """
    # Check if manifest file exists
    if not manifest_path.exists():
        raise ManifestError("Manifest file not found", str(manifest_path))

    # Load YAML content
    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ManifestError(f"Invalid YAML: {e}", str(manifest_path))
    except OSError as e:
        raise ManifestError(f"Cannot read manifest file: {e}", str(manifest_path))

    # Validate structure
    if not isinstance(data, dict):
        raise ManifestError("Manifest must be a YAML dictionary", str(manifest_path))

    # Check for required keys - need either paths or groups
    has_paths = "paths" in data
    has_groups = "groups" in data

    if not has_paths and not has_groups:
        raise ManifestError(
            "Manifest must contain either 'paths' or 'groups'", str(manifest_path)
        )

    # Parse paths if present
    paths_data = None
    if has_paths:
        paths_data = data["paths"]
        if not isinstance(paths_data, dict):
            raise ManifestError("'paths' must be a dictionary", str(manifest_path))

    # Parse groups if present
    groups_data = None
    if has_groups:
        groups_raw = data["groups"]
        if not isinstance(groups_raw, dict):
            raise ManifestError("'groups' must be a dictionary", str(manifest_path))

        groups_data = {}
        for group_name, group_raw in groups_raw.items():
            if not isinstance(group_raw, dict):
                raise ManifestError(
                    f"Group '{group_name}' must be a dictionary", str(manifest_path)
                )

            if "description" not in group_raw:
                raise ManifestError(
                    f"Group '{group_name}' missing required 'description'",
                    str(manifest_path),
                )

            if "paths" not in group_raw:
                raise ManifestError(
                    f"Group '{group_name}' missing required 'paths'", str(manifest_path)
                )

            if not isinstance(group_raw["paths"], dict):
                raise ManifestError(
                    f"Group '{group_name}' paths must be a dictionary",
                    str(manifest_path),
                )

            try:
                groups_data[group_name] = Group(
                    description=group_raw["description"], paths=group_raw["paths"]
                )
            except ValueError as e:
                raise ValidationError(
                    f"Invalid group '{group_name}': {e}", str(manifest_path)
                )

    # Create and validate Manifest object
    try:
        manifest = Manifest(paths=paths_data, groups=groups_data)
    except ValueError as e:
        raise ValidationError(str(e), str(manifest_path))

    # Validate that all paths exist and resolve properly
    for path_str in manifest.get_paths():
        try:
            file_path = Path(path_str)
            resolved_path = file_path.resolve()

            # Check if the file exists
            if not resolved_path.exists():
                raise ValidationError(
                    f"Path does not exist: {path_str}", str(manifest_path)
                )

        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid path '{path_str}': {e}", str(manifest_path))

    return manifest


def write_manifest(manifest: Manifest, manifest_path: Path) -> None:
    """
    Write a manifest to disk with deterministic formatting.

    Args:
        manifest: Manifest object to write
        manifest_path: Path where to write the manifest

    Raises:
        ManifestError: If the manifest cannot be written
    """
    # Create the YAML data structure
    data: dict[str, Any] = {}

    # Add flat paths if they exist
    if manifest.paths:
        data["paths"] = dict(sorted(manifest.paths.items()))

    # Add groups if they exist
    if manifest.groups:
        groups_data = {}
        for group_name in sorted(manifest.groups.keys()):
            group = manifest.groups[group_name]
            groups_data[group_name] = {
                "description": group.description,
                "paths": dict(sorted(group.paths.items())),
            }
        data["groups"] = groups_data

    try:
        # Ensure parent directory exists
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML with consistent formatting
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,  # We already sorted manually
                indent=2,
                allow_unicode=True,
            )
    except OSError as e:
        raise ManifestError(f"Cannot write manifest file: {e}", str(manifest_path))
    except yaml.YAMLError as e:
        raise ManifestError(
            f"Cannot serialize manifest to YAML: {e}", str(manifest_path)
        )


def validate_manifest_paths(manifest: Manifest, base_path: Path | None = None) -> None:
    """
    Validate that all paths in a manifest exist and are accessible.

    Args:
        manifest: Manifest to validate
        base_path: Base path to resolve relative paths from (defaults to current working directory)

    Raises:
        ValidationError: If any paths are invalid or inaccessible
    """
    if base_path is None:
        base_path = Path.cwd()

    for path_str in manifest.get_paths():
        try:
            file_path = Path(path_str)
            if not file_path.is_absolute():
                file_path = base_path / file_path

            resolved_path = file_path.resolve()

            if not resolved_path.exists():
                raise ValidationError(f"Path does not exist: {path_str}")

            if not resolved_path.is_file():
                raise ValidationError(f"Path is not a file: {path_str}")

        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid path '{path_str}': {e}")
