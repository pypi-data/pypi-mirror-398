"""PyEnforce package.

This package provides a centralized way to run various code quality tools
(such as ruff, mypy, pylint, bandit, semgrep, vulture) with consistent
configurations. It serves as a wrapper around these tools to ensure uniform
code quality standards across the project.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyenforce")
except PackageNotFoundError:
    # Fallback for when package is not installed
    __version__ = "0.0.0"
