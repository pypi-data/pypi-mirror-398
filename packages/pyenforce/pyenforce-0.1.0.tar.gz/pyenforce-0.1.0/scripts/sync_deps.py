#!/usr/bin/env python3
"""Script to synchronize optional dependencies in pyproject.toml.

It updates the 'all' group to include all other optional dependencies, sorts
dependencies within each group, and ensures a consistent order of groups.
"""

import sys
import tomllib
from pathlib import Path
from typing import cast

# Constants
ALL_GROUP = "all"
OPTIONAL_DEPS_HEADER = "[project.optional-dependencies]\n"


class SectionNotFoundError(Exception):
    """Raised when the optional-dependencies section is not found."""


class NoChangeError(Exception):
    """Raised when no changes are needed to the file."""


def load_pyproject(path: Path) -> dict[str, object]:
    """Load the pyproject.toml file.

    Args:
        path: Path to the pyproject.toml file.

    Returns:
        The parsed TOML data.

    """
    if not path.exists():
        sys.exit(1)

    with path.open("rb") as f:
        return tomllib.load(f)


def sync_and_sort_deps(
    optional_deps: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Sync the 'all' group and sort all dependency lists.

    Args:
        optional_deps: The optional-dependencies dictionary.

    Returns:
        The updated dictionary with 'all' group synced and all lists sorted.

    """
    # Sort all dependency lists
    sorted_deps = {
        group: sorted(deps) for group, deps in optional_deps.items()
    }

    # Sync 'all' group: union of all other groups
    sorted_deps[ALL_GROUP] = sorted(
        {
            dep
            for group, deps in sorted_deps.items()
            if group != ALL_GROUP
            for dep in deps
        },
    )

    return sorted_deps


def generate_section_content(optional_deps: dict[str, list[str]]) -> list[str]:
    """Generate content for the [project.optional-dependencies] section.

    Args:
        optional_deps: The updated optional-dependencies dictionary.

    Returns:
        A list of strings representing the lines of the new section.

    """
    # Order keys: 'all' first, then alphabetical
    sorted_keys = [
        ALL_GROUP,
        *sorted(k for k in optional_deps if k != ALL_GROUP),
    ]

    new_section_lines = [OPTIONAL_DEPS_HEADER]
    for key in sorted_keys:
        if not (deps := optional_deps.get(key)):
            continue

        # Multiline for 'all' or multi-item; inline for single
        if len(deps) > 1 or key == ALL_GROUP:
            new_section_lines.append(f"{key} = [\n")
            new_section_lines.extend(f'  "{dep}",\n' for dep in deps)
            new_section_lines.append("]\n")
        else:
            new_section_lines.append(f'{key} = ["{deps[0]}"]\n')

    new_section_lines.append("\n")
    return new_section_lines


def _find_section_bounds(lines: list[str]) -> tuple[int, int]:
    """Find the start and end indices of the optional-dependencies section.

    Args:
        lines: All lines from the file.

    Returns:
        A tuple of (start_idx, end_idx).

    Raises:
        SectionNotFoundError: If the optional-dependencies section is not
            found.

    """
    header_stripped = OPTIONAL_DEPS_HEADER.strip()
    for i, line in enumerate(lines):
        if line.strip() == header_stripped:
            start_idx = i
            # Find end: next section or EOF
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith("["):
                    return (start_idx, j)
            return (start_idx, len(lines))
    raise SectionNotFoundError


def _update_section(
    lines: list[str],
    new_section_lines: list[str],
) -> list[str]:
    """Update the file with new section content, replacing or appending.

    Args:
        lines: All lines from the file.
        new_section_lines: The new section content.

    Returns:
        New lines with the section updated.

    Raises:
        NoChangeError: If no changes are needed.

    """
    try:
        start_idx, end_idx = _find_section_bounds(lines)
    except SectionNotFoundError:
        # Append new section
        prefix = ["\n"] if lines and lines[-1].strip() else []
        return lines + prefix + new_section_lines

    # Replace existing section
    if lines[start_idx:end_idx] == new_section_lines:
        raise NoChangeError
    return lines[:start_idx] + new_section_lines + lines[end_idx:]


def update_file(path: Path, new_section_lines: list[str]) -> bool:
    """Update the pyproject.toml file with the new section content.

    Args:
        path: Path to the pyproject.toml file.
        new_section_lines: The lines of the new section.

    Returns:
        True if the file was changed, False otherwise.

    """
    with path.open(encoding="utf-8") as f:
        lines = f.readlines()

    try:
        new_lines = _update_section(lines, new_section_lines)
    except NoChangeError:
        return False

    with path.open("w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return True


def main() -> None:
    """Execute main function."""
    pyproject_path = Path("pyproject.toml")

    data = load_pyproject(pyproject_path)
    project = cast("dict[str, object]", data.get("project", {}))
    optional_deps = cast(
        "dict[str, list[str]]",
        project.get("optional-dependencies", {}),
    )

    updated_deps = sync_and_sort_deps(optional_deps)
    new_section_lines = generate_section_content(updated_deps)

    sys.exit(int(update_file(pyproject_path, new_section_lines)))


if __name__ == "__main__":
    main()
