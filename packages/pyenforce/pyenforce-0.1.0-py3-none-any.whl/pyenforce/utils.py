"""Utility functions for pyenforce.

This module contains helper functions used across the application, such as:
- Inferring the target Python version from project configuration.
"""

import re
import tomllib
from pathlib import Path


def get_target_python_version() -> tuple[int, int, int] | None:
    """Infer the target Python version from pyproject.toml.

    Read the 'project.requires-python' field from 'pyproject.toml'
    and extract the version as a tuple of (major, minor, patch).

    Returns:
        tuple[int, int, int] | None: The target Python version as a tuple
            (e.g., (3, 12, 0)), or None if it cannot be determined.
            Patch version defaults to 0 if not specified.

    """
    try:  # pylint: disable=too-many-try-statements
        with Path("pyproject.toml").open("rb") as f:
            data = tomllib.load(f)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return None

    requires_python = data.get("project", {}).get("requires-python", "")
    # Match patterns like "3.12", ">=3.11", "~=3.12.0", "3.12.1"
    if match := re.search(r"3\.(\d+)(?:\.(\d+))?", requires_python):
        major = 3
        minor = int(match.group(1))
        patch = int(match.group(2)) if match.group(2) else 0
        return (major, minor, patch)

    return None
