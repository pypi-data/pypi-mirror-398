"""Command-line interface for PyEnforce.

This module serves as the main entry point for the pyenforce CLI application.
It is responsible for parsing command-line arguments, dispatching execution to
the appropriate quality assurance tool, and injecting the corresponding
configuration files.

The CLI supports running various QA tools (like ruff, mypy, pylint, bandit,
semgrep, vulture) with centralized configuration management, ensuring
consistent code quality checks across the project.
"""

import argparse
import sys
from typing import NoReturn

from pyenforce.runner import Tool, run
from pyenforce.tools import TOOLS


def _parse_args() -> tuple[Tool, list[str]]:
    """Parse and validate command-line arguments.

    Uses argparse to interpret command-line inputs, determining which QA tool
    to run and what additional arguments to pass to it.

    Returns:
        tuple[Tool, list[str]]: A tuple containing the selected Tool object
            and a list of additional arguments to be passed to the tool.

    """
    parser = argparse.ArgumentParser(
        description="Run QA tools with predefined configurations.",
        prog="pyenforce",
    )
    parser.add_argument(
        "tool",
        choices=TOOLS.keys(),
        help="The QA tool to run.",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the tool.",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    return TOOLS[args.tool], args.args


def _execute_tool(tool: Tool, args: list[str]) -> NoReturn:
    """Execute the specified QA tool with error handling.

    Runs the command associated with the tool, passing along any additional
    arguments. Handles common execution errors such as missing executables
    or permission issues, providing user-friendly error messages.

    Args:
        tool: The tool configuration object containing the command to run.
        args: Additional arguments to pass to the command.

    """
    try:
        sys.exit(run(tool, args))
    except FileNotFoundError:
        sys.stderr.write(
            f"Error: Command '{tool.command}' not found.\n"
            "Please ensure it is installed (e.g., "
            f"'pip install pyenforce[{tool.command}]').\n"
            "If using pre-commit and you've overridden "
            "'additional_dependencies', make sure to include "
            f"'.[{tool.command}]' in the list.\n",
        )
        sys.exit(127)  # command not found
    except PermissionError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(126)  # command invoked cannot execute
    except OSError as e:
        sys.stderr.write(f"Error running {tool.command}: {e}\n")
        sys.exit(1)


def main() -> NoReturn:
    """Run the pyenforce CLI.

    Orchestrates the CLI execution flow:
    1. Parses command-line arguments to select the target tool.
    2. Executes the selected tool with the provided arguments.
    3. Handles KeyboardInterrupt for graceful shutdown.

    The function ensures that the underlying QA tool is executed with the
    correct configuration and arguments, and propagates its exit code.
    """
    tool, args = _parse_args()
    try:
        _execute_tool(tool, args)
    except KeyboardInterrupt:
        sys.exit(130)  # script terminated by Control-C
