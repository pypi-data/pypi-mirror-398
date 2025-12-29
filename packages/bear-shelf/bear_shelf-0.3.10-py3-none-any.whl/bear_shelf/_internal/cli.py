from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from lazy_bear import lazy

from bear_shelf._internal._info import METADATA

from ._versioning import ExitCode, cli_bump

if TYPE_CHECKING:
    from ._cmds import _ReturnedArgs, debug_info, get_args, get_version
else:
    _ReturnedArgs, debug_info, get_args, get_version = lazy("bear_shelf._internal._cmds").to(
        "_ReturnedArgs", "debug_info", "get_args", "get_version"
    )


def main(arguments: list[str] | None = None) -> ExitCode:
    """Entry point for the CLI application.

    This function is executed when you type `bear-shelf` or `python -m bear-shelf`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    args: _ReturnedArgs = get_args(arguments or sys.argv[1:])

    match args.cmd:
        case "version":
            return get_version()
        case "bump":
            return cli_bump(args.bump_type, METADATA.version_tuple)
        case "debug":
            return debug_info(no_color=args.no_color)
        case "sync-storage":
            # TODO: Will return this after hotfix later.
            # generate_storage_file()
            return ExitCode.SUCCESS
        case _:
            print("Unknown command.", file=sys.stderr)
            return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
