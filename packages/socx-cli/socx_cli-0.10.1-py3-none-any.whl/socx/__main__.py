"""Console script entry point for the SoCX command line interface."""

import sys
from socx import cli as cli


def main() -> int:
    """Invoke the SoCX CLI using Click's callable interface."""
    return cli(obj={})


if __name__ == "__main__":
    sys.exit(main())
