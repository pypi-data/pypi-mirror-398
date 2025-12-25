# -*- coding: utf-8 -*-


# =============================================================================
# Docstring
# =============================================================================

"""
Command-line interface for Sturnus library.
Provides a simple CLI to greet users using the sturnus library.
Examples:
    Basic usage::

        $ python -m sturnus --version
        sturnus 0.1.0

        $ python -m sturnus Alice
        Hello, Alice! Welcome to the sturnus library.

    With verbose output::

        $ python -m sturnus Bob --verbose
        Hello, Bob! Welcome to the sturnus library.

        [Sturnus v0.1.0]

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Standard Library
import argparse
import sys
from typing import Optional, Sequence

# Import | Local
from sturnus import __version__, hello

# =============================================================================
# Functions
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sturnus",
        description="Sturnus - A Python library for demonstration and publishing to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit",
    )

    parser.add_argument(
        "name",
        nargs="?",
        default="World",
        help="Name to greet (default: World)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        greeting = hello(args.name)
        print(greeting)

        if args.verbose:
            print(f"\n[Sturnus v{__version__}]")

        return 0

    except (ValueError, TypeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
