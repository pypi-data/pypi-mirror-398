from argparse import ArgumentParser, Namespace
from typing import NamedTuple

from frozen_cub._internal.debug import _print_debug_info

from ._exit_code import ExitCode
from ._versioning import VALID_BUMP_TYPES, BumpType, cli_bump


class _ReturnedArgs(NamedTuple):
    cmd: str
    bump_type: BumpType
    no_color: bool


def get_version() -> ExitCode:
    """CLI command to get the version of the package."""
    from ._info import METADATA  # noqa: PLC0415

    print(METADATA.version)
    return ExitCode.SUCCESS


def bump_version(bump_type: BumpType) -> ExitCode:
    """CLI command to bump the version of the package."""
    from ._info import METADATA  # noqa: PLC0415

    return cli_bump(bump_type, METADATA.version_tuple)


def debug_info(no_color: bool = False) -> ExitCode:
    """CLI command to print debug information."""
    _print_debug_info(no_color=no_color)  # pyright: ignore[reportCallIssue]
    return ExitCode.SUCCESS


def get_args(args: list[str]) -> _ReturnedArgs:
    """Parse command-line arguments."""
    from ._info import METADATA  # noqa: PLC0415

    parser = ArgumentParser(description=METADATA.description)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("version", help="Get the version of the package.")
    bump_parser: ArgumentParser = subparsers.add_parser("bump", help="Bump the version of the package.")
    bump_parser.add_argument(
        "bump_type",
        type=str,
        choices=VALID_BUMP_TYPES,
        help="Type of version bump (major, minor, patch).",
    )
    debug_parser: ArgumentParser = subparsers.add_parser("debug", help="Print debug information.")
    debug_parser.add_argument(
        "--no-color",
        "-n",
        action="store_true",
        help="Disable colored output.",
    )
    parsed: Namespace = parser.parse_args(args)
    return _ReturnedArgs(
        cmd=parsed.command,
        bump_type=getattr(parsed, "bump_type", "patch"),
        no_color=getattr(parsed, "no_color", False),
    )
