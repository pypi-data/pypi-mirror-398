"""Runner module for executing static analysis tools.

This module provides the core functionality for executing external quality
assurance tools. It defines the `Tool` data structure for configuring
tools and the `run` function for executing them as subprocesses.
"""

import subprocess  # nosec
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    """Configuration for a static analysis tool.

    Attributes:
        command: The command to execute (e.g., 'ruff', 'mypy').
        args: A callable that returns a list of arguments to pass to the
            command. This allows for lazy evaluation of arguments.

    """

    command: str
    args: Callable[[], list[str]]


def run(tool: Tool, extra_args: list[str]) -> int:
    """Execute a tool with its configuration and extra arguments.

    Args:
        tool: The tool configuration.
        extra_args: Additional arguments passed from the command line.

    Returns:
        int: The exit code of the process.

    Raises:
        OSError: If the tool fails to execute (e.g. command not found).

    """
    full_cmd = [tool.command, *tool.args(), *extra_args]
    result = subprocess.run(full_cmd, check=False)  # nosec  # noqa: S603
    return result.returncode
