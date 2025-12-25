"""Entry point for CVE Report Aggregator CLI."""

import sys

from .cli import display_logo, main


def run() -> None:
    """Entry point for the CLI."""
    # Skip logo if --version flag is present
    if "--version" not in sys.argv:
        display_logo()
    main()


if __name__ == "__main__":
    run()
