from importlib import metadata

import colorama

from ts_cli.decorators.exit_on_critical import exit_on_critical
from ts_cli.parser import parser
from ts_cli.util.version import check_update_required

version = metadata.version("tetrascience-cli")


@exit_on_critical
def main():
    colorama.init()
    check_update_required(version)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
