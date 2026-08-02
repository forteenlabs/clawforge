from __future__ import annotations

import argparse
from collections.abc import Sequence

from clawforge.state import run_state


def build_parser() -> argparse.ArgumentParser:
    """Create the ClawForge command-line parser."""

    parser = argparse.ArgumentParser(
        prog="clawforge",
        description="ClawForge command-line interface.",
    )

    subcommands = parser.add_subparsers(dest="command")

    subcommands.add_parser(
        "state",
        help="Report observable repository state.",
    )

    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Route a ClawForge command to its capability."""

    parser = build_parser()
    parsed = parser.parse_args(arguments)

    if parsed.command == "state":
        return run_state()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())