from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import sys

from funcy_bear.constants.exit_code import ExitCode

from ._versioning import VALID_BUMP_TYPES, BumpType, cli_bump
from .debug import METADATA, _print_debug_info


@dataclass(slots=True, frozen=True)
class _ReturnedArgs:
    cmd: str
    bump_type: BumpType
    no_color: bool


def _get_args(args: list[str]) -> _ReturnedArgs:
    """Parse command-line arguments."""
    parser = ArgumentParser(description="Pack Int CLI", add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("version", help="Get the version of the package.")
    bump_parser: ArgumentParser = subparsers.add_parser("bump", help="Bump the version of the package.")
    bump_parser.add_argument("bump_type", type=str, choices=VALID_BUMP_TYPES, help="(major, minor, patch).")
    debug_parser: ArgumentParser = subparsers.add_parser("debug", help="Print debug information.")
    debug_parser.add_argument("--no-color", "-n", action="store_true", help="Disable colored output.")
    parsed: Namespace = parser.parse_args(args)
    return _ReturnedArgs(
        cmd=parsed.command,
        bump_type=getattr(parsed, "bump_type", "patch"),
        no_color=getattr(parsed, "no_color", False),
    )


def _debug_info() -> ExitCode:  # pragma: no cover
    """CLI command to print debug information."""
    _print_debug_info()
    return ExitCode.SUCCESS


def _bump(bump_type: BumpType) -> ExitCode:  # pragma: no cover
    """CLI command to bump the version of the package."""
    return cli_bump(bump_type, METADATA.version_tuple)


def _version(name: bool = False) -> ExitCode:  # pragma: no cover
    """CLI command to get the current version of the package."""
    print(f"{METADATA.name} {METADATA.version}" if name else METADATA.version)
    return ExitCode.SUCCESS


def main(args: list[str] | None = None) -> ExitCode:
    """Entry point for the CLI application.

    This function is executed when you type `codec_cub` or `python -m codec_cub`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    if args is None:
        args = sys.argv[1:]

    arguments: _ReturnedArgs = _get_args(args)
    cmd: str = arguments.cmd

    match cmd:
        case "version":
            return _version()
        case "bump":
            return _bump(arguments.bump_type)
        case "debug":
            return _debug_info()
        case _:
            print(f"Unknown command: {cmd}")
            return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
