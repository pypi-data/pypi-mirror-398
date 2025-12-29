"""Tool definitions for pyenforce.

This module contains the configuration for all supported tools (ruff, mypy,
pylint, bandit, semgrep, vulture), including their default arguments and
dynamic argument generation logic. It defines the `TOOLS` dictionary which
maps tool names to their respective `Tool` configuration objects.
"""

from pathlib import Path

from pyenforce.runner import Tool
from pyenforce.utils import get_target_python_version

CONFIG_DIR = Path(__file__).parent / "configs"


def _get_ruff_format_args() -> list[str]:
    """Generate arguments for Ruff format.

    This includes:
    1. Base arguments (format command, config file).
    2. Dynamic arguments based on the environment (e.g., target Python
       version).

    Returns:
        list[str]: The complete list of arguments for the Ruff format command.

    """
    args = ["format", "--config", str(CONFIG_DIR / "ruff.toml")]

    if version := get_target_python_version():
        _, minor, _ = version
        args.extend(["--target-version", f"py3{minor}"])

    return args


def _get_ruff_check_args() -> list[str]:
    """Generate arguments for Ruff check.

    This includes:
    1. Base arguments (check command, config file).
    2. Dynamic arguments based on the environment (e.g., target Python
       version).

    Returns:
        list[str]: The complete list of arguments for the Ruff check command.

    """
    args = ["check", "--config", str(CONFIG_DIR / "ruff.toml")]

    if version := get_target_python_version():
        _, minor, _ = version
        args.extend(["--target-version", f"py3{minor}"])

    return args


TOOLS = {
    "fmt": Tool(
        command="ruff",
        args=_get_ruff_format_args,
    ),
    "ruff": Tool(
        command="ruff",
        args=_get_ruff_check_args,
    ),
    "mypy": Tool(
        command="mypy",
        args=lambda: ["--config-file", str(CONFIG_DIR / "mypy.toml")],
    ),
    "pylint": Tool(
        command="pylint",
        args=lambda: ["--rcfile", str(CONFIG_DIR / "pylint.toml")],
    ),
    "bandit": Tool(
        command="bandit",
        args=lambda: ["-c", str(CONFIG_DIR / "bandit.toml")],
    ),
    "semgrep": Tool(
        command="semgrep",
        args=lambda: ["scan", "--error", "--config", "p/python"],
    ),
    "vulture": Tool(
        command="vulture",
        args=lambda: ["--config", str(CONFIG_DIR / "vulture.toml")],
    ),
}
