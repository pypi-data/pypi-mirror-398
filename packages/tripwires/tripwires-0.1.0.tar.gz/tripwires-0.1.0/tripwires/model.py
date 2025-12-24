"""Data models for tripwires."""

from dataclasses import dataclass, field
from enum import Enum


def validate_hash(hash_value: str) -> None:
    """
    Validate a SHA-256 hash value.

    Args:
        hash_value: Hash string to validate

    Raises:
        ValueError: If hash is not 32 lowercase hexadecimal characters (xxHash3-128)
    """
    if len(hash_value) != 32:
        raise ValueError(f"hash must be 32 characters: {hash_value}")
    if not all(c in "0123456789abcdef" for c in hash_value):
        raise ValueError(f"hash must be lowercase hex: {hash_value}")


class CheckStatus(Enum):
    """Status of a file check operation."""

    MATCH = "match"
    MISMATCH = "mismatch"
    ERROR = "error"


@dataclass
class CheckResult:
    """Result of checking a single file."""

    path: str
    status: CheckStatus
    expected_hash: str
    actual_hash: str | None = None
    error_message: str | None = None

    @property
    def is_match(self) -> bool:
        """Return True if the file matches its expected hash."""
        return self.status == CheckStatus.MATCH

    @property
    def is_mismatch(self) -> bool:
        """Return True if the file has a hash mismatch."""
        return self.status == CheckStatus.MISMATCH

    @property
    def is_error(self) -> bool:
        """Return True if there was an error processing the file."""
        return self.status == CheckStatus.ERROR


@dataclass
class Group:
    """Represents a group of files with a description."""

    description: str
    paths: dict[str, str]

    def __post_init__(self) -> None:
        """Validate the group after initialization."""
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")
        if not isinstance(self.paths, dict):
            raise ValueError("paths must be a dictionary")

        for path, hash_value in self.paths.items():
            if not isinstance(path, str):
                raise ValueError(f"path must be a string: {path}")
            if not isinstance(hash_value, str):
                raise ValueError(f"hash must be a string: {hash_value}")
            validate_hash(hash_value)


@dataclass
class Manifest:
    """Represents a tripwires manifest file.

    Supports both flat structure (paths dict) and grouped structure (groups dict).
    At least one must be provided, both can be used together.
    """

    paths: dict[str, str] | None = None
    groups: dict[str, Group] | None = None
    _all_paths: dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the manifest after initialization."""
        # Ensure at least one structure is provided
        if self.paths is None and self.groups is None:
            raise ValueError("Either paths or groups must be provided")

        # Initialize empty dicts if None, but keep original None if explicitly passed
        # This allows tests to check for None values
        if self.paths is None and self.groups is not None:
            # Only initialize paths as empty dict if groups are provided and paths is None
            pass  # Keep paths as None for test compatibility

        if self.groups is None:
            self.groups = {}

        # Validate paths structure if provided
        if self.paths:
            if not isinstance(self.paths, dict):
                raise ValueError("paths must be a dictionary")
            for path, hash_value in self.paths.items():
                if not isinstance(path, str):
                    raise ValueError(f"path must be a string: {path}")
                if not isinstance(hash_value, str):
                    raise ValueError(f"hash must be a string: {hash_value}")
                validate_hash(hash_value)

        # Validate groups structure if provided
        if self.groups:
            if not isinstance(self.groups, dict):
                raise ValueError("groups must be a dictionary")
            for group_name, group in self.groups.items():
                if not isinstance(group_name, str):
                    raise ValueError(f"group name must be a string: {group_name}")
                if not isinstance(group, Group):
                    raise ValueError(f"group must be a Group instance: {group}")

        # Build combined paths dict and check for duplicates
        self._build_all_paths()

    def _build_all_paths(self) -> None:
        """Build the combined paths dict and validate no duplicates."""
        self._all_paths = {}

        # Add flat paths
        if self.paths:
            for path, hash_value in self.paths.items():
                self._all_paths[path] = hash_value

        # Add grouped paths, checking for duplicates
        if self.groups:
            for group_name, group in self.groups.items():
                for path, hash_value in group.paths.items():
                    if path in self._all_paths:
                        raise ValueError(f"Duplicate path found: {path}")
                    self._all_paths[path] = hash_value

    def get_paths(self) -> list[str]:
        """Get sorted list of all paths in the manifest."""
        return sorted(self._all_paths.keys())

    def get_hash(self, path: str) -> str:
        """Get the expected hash for a path."""
        if path not in self._all_paths:
            raise KeyError(f"Path not found: {path}")
        return self._all_paths[path]

    def set_hash(self, path: str, hash_value: str) -> None:
        """Set the hash for a path."""
        validate_hash(hash_value)

        # Update in the appropriate location
        if self.paths and path in self.paths:
            self.paths[path] = hash_value
        elif self.groups:
            # Find the group containing this path
            for group in self.groups.values():
                if path in group.paths:
                    group.paths[path] = hash_value
                    break
            else:
                # Path not found in any group, add to flat paths
                if self.paths is None:
                    self.paths = {}
                self.paths[path] = hash_value

        # Rebuild the combined paths dict
        self._build_all_paths()

    def has_groups(self) -> bool:
        """Return True if the manifest uses groups."""
        return bool(self.groups)

    def get_group_names(self) -> list[str]:
        """Get sorted list of group names."""
        return sorted(self.groups.keys()) if self.groups else []

    def get_group(self, name: str) -> Group:
        """Get a group by name."""
        if not self.groups or name not in self.groups:
            raise KeyError(f"Group not found: {name}")
        return self.groups[name]

    def add_file(
        self, path: str, hash_value: str, group_name: str | None = None
    ) -> None:
        """
        Add a file to the manifest.

        Args:
            path: The file path
            hash_value: The expected hash for the file
            group_name: Optional group name to add the file to. If None, adds to flat paths.
        """
        validate_hash(hash_value)

        if group_name is not None:
            # Add to specific group
            if self.groups is None:
                self.groups = {}
            if group_name not in self.groups:
                raise KeyError(f"Group not found: {group_name}")
            self.groups[group_name].paths[path] = hash_value
        else:
            # Add to flat paths
            if self.paths is None:
                self.paths = {}
            self.paths[path] = hash_value

        # Rebuild the combined paths dict
        self._build_all_paths()
