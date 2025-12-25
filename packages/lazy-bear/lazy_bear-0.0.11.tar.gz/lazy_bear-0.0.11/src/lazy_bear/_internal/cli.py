from __future__ import annotations

import sys

from ._exit_code import ExitCode


def main(args: list[str] | None = None) -> ExitCode:  # pragma: no cover
    """Entry point for the CLI application.

    This function is executed when you type `lazy_bear` or `python -m lazy_bear`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    from lazy_bear._internal._cmds import _ReturnedArgs, bump_version, debug_info, get_version, to_args  # noqa: PLC0415

    if args is None:
        args = sys.argv[1:]
    parsed_args: _ReturnedArgs = to_args(args)
    match parsed_args.cmd:
        case "debug":
            return debug_info(no_color=parsed_args.no_color)
        case "version":
            return get_version(name=parsed_args.version_name)
        case "bump":
            return bump_version(bump_type=parsed_args.bump_type)
        case _:  # pragma: no cover
            print(f"Unknown command: {parsed_args.cmd}")
            return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
