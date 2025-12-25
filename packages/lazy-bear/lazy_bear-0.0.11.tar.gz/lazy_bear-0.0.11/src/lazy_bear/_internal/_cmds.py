from __future__ import annotations

from argparse import ArgumentParser, Namespace
from typing import Literal, NamedTuple

from ._exit_code import ExitCode
from ._info import Version, VersionParts
from .debug import _print_debug_info

type BumpType = Literal["major", "minor", "patch"]


VALID_BUMP_TYPES: list[str] = VersionParts.choices()  # pragma: no cover
ALL_PARTS: int = VersionParts.parts()  # pragma: no cover


class _ReturnedArgs(NamedTuple):
    cmd: str
    bump_type: BumpType
    version_name: bool
    no_color: bool


def cli_bump(b: BumpType, v: Version) -> ExitCode:  # pragma: no cover
    """Bump the version of the current package.

    Args:
        b: The type of bump ("major", "minor", or "patch").
        v: A Version instance representing the current version.

    Returns:
        An ExitCode indicating success or failure.
    """
    if b not in VALID_BUMP_TYPES:
        print(f"Invalid argument '{b}'. Use one of: {', '.join(VALID_BUMP_TYPES)}.")
        return ExitCode.FAILURE
    try:
        new_version: Version = v.new_version(b)
        print(str(new_version))
        return ExitCode.SUCCESS
    except ValueError:
        print(f"Invalid version tuple: {v}")
        return ExitCode.FAILURE


def debug_info(no_color: bool = False) -> ExitCode:  # pragma: no cover
    """CLI command to print debug information."""
    _print_debug_info(no_color=no_color)
    return ExitCode.SUCCESS


def bump_version(bump_type: BumpType) -> ExitCode:  # pragma: no cover
    """CLI command to bump the version of the package."""
    from lazy_bear._internal._info import METADATA

    return cli_bump(bump_type, METADATA.version_tuple)


def get_version(name: bool = False) -> ExitCode:  # pragma: no cover
    """CLI command to get the current version of the package."""
    from lazy_bear._internal._info import METADATA

    print(f"{METADATA.name} {METADATA.version}" if name else METADATA.version)
    return ExitCode.SUCCESS


def to_args(args: list[str]) -> _ReturnedArgs:  # pragma: no cover
    """Convert a list of arguments into a Namespace object."""
    from lazy_bear._internal._info import METADATA

    parser = ArgumentParser(prog=METADATA.name, description="Lazy Bear CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    debug: ArgumentParser = subparsers.add_parser("debug", help="Print debug information")
    debug.add_argument("--no-color", action="store_true", help="Disable colored output")
    version_parser: ArgumentParser = subparsers.add_parser("version", help="Get the current version")
    version_parser.add_argument("--name", action="store_true", help="Include the package name in the output")
    bump_parser: ArgumentParser = subparsers.add_parser("bump", help="Bump the version of the package")
    bump_parser.add_argument("bump_type", choices=["major", "minor", "patch"], help="Type of version bump")
    parsed: Namespace = parser.parse_args(args)
    return _ReturnedArgs(
        cmd=parsed.command,
        version_name=getattr(parsed, "name", False),
        bump_type=getattr(parsed, "bump_type", "patch"),
        no_color=getattr(parsed, "no_color", False),
    )


# ruff: noqa: PLC0415
