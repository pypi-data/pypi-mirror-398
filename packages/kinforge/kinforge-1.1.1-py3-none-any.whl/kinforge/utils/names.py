"""Utilities for name handling and validation."""

import re


def ns_join(namespace: str | None, name: str) -> str:
    """Join namespace and name with '/' separator. Handles None and empty string."""
    if namespace is None or namespace == "":
        return name
    return f"{namespace}/{name}"


def validate_sdf_name(name: str, context: str = "name") -> None:
    """
    Validate that a name is suitable for SDF export.

    Raises ValueError if the name contains invalid characters.
    SDF names should be XML-compatible and avoid special characters.
    """
    if not name:
        raise ValueError(f"Invalid {context}: name cannot be empty")

    # Check for invalid characters (spaces, special chars that could break XML/SDF)
    if not re.match(r"^[a-zA-Z0-9_/\-\.]+$", name):
        raise ValueError(
            f"Invalid {context} {name!r}: contains invalid characters. "
            f"Only alphanumeric, underscore, hyphen, dot, and slash are allowed."
        )

    # Check for leading/trailing slashes or whitespace
    if name != name.strip():
        raise ValueError(
            f"Invalid {context} {name!r}: cannot have leading/trailing whitespace"
        )


def is_base_link(name: str) -> bool:
    """
    Check if a link name represents a base link.

    Returns True if the final segment (after last '/') is exactly 'base'.
    This avoids false positives like 'database' or 'firebase'.
    """
    segments = name.split("/")
    return segments[-1] == "base"
