from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._exit_code import ExitCode


def main(args: list[str] | None = None) -> ExitCode:
    """Entry point for the CLI application.

    This function is executed when you type `profiler_cub` or `python -m profiler_cub`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    from ._cmds import _ReturnedArgs, bump_version, debug_info, get_args, get_version  # noqa: PLC0415
    from ._exit_code import ExitCode  # noqa: PLC0415

    if args is None:
        args = sys.argv[1:]

    parsed_args: _ReturnedArgs = get_args(args)
    try:
        match parsed_args.cmd:
            case "version":
                return get_version()
            case "bump":
                return bump_version(parsed_args.bump_type)
            case "debug":
                return debug_info(no_color=parsed_args.no_color)
            case _:
                return ExitCode.FAILURE
    except Exception:
        return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
