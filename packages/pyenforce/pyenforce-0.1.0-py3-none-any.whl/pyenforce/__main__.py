"""Entry point for the pyenforce module.

This module allows the package to be executed directly using the
`python -m pyenforce` command. It invokes the main CLI entry point.
"""

from pyenforce.cli import main

if __name__ == "__main__":
    main()
