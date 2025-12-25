import argparse
import sys
import textwrap

from ts_cli.config.cli_config import VALID_KEYS, CliConfig, write_config_file
from ts_cli.config.util import load_from_yaml_or_json_if_present
from ts_cli.errors.critical_error import CriticalError
from ts_cli.util.emit import emit_warning


def add_config_parser(subparsers):
    """
    Adds the `config` subparser
    :param subparsers:
    :return:
    """
    parser = subparsers.add_parser(
        "config",
        help="Get and set user options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Get, update or delete options with this command.
            """
        ),
    )
    actions_parser = parser.add_subparsers(
        title="actions", required=True, dest="action"
    )
    add_config_get_parser(actions_parser)
    add_config_set_parser(actions_parser)
    add_config_unset_parser(actions_parser)
    add_config_save_parser(actions_parser)


def shared_cmd_args(parser: argparse.ArgumentParser):
    location_group = parser.add_argument_group("Config location")
    location_group = location_group.add_mutually_exclusive_group()
    location_group.add_argument(
        "--global", "-g", action="store_true", help="option applies to all profiles"
    )
    location_group.add_argument(
        "--profile", help="option applies to a single profile", type=str
    )


def add_config_get_parser(subparsers):
    parser = subparsers.add_parser(
        "get",
        help="Display a config value",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Retrieves the currently set configuration option

            If there is no option set for the specified profile,
            the get command will reach out into the global scope
            to look for a configuration option.
            """
        ),
    )
    shared_cmd_args(parser)
    add_key_argument(parser)
    parser.set_defaults(func=config_get)


def add_key_argument(parser):
    parser.add_argument("key", help="the config name", type=str, choices=VALID_KEYS)


def add_config_unset_parser(subparsers):
    parser = subparsers.add_parser(
        "unset",
        help="Remove a config value",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Removes the currently set configuration option

            If there is no option set for the specified profile,
            the unset command will *not* unset the global scope,
            and will instead exit unsuccessfully with a warning
            """
        ),
    )
    shared_cmd_args(parser)
    add_key_argument(parser)
    parser.set_defaults(func=config_unset)


def add_config_set_parser(subparsers):
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "set",
        help="Save a new config value",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Saves a new configuration option at the specified key

                ts-cli config set profile development

            Use the --global flag to make the option apply to all
            profiles by default

            Use the the `--false` or `--true` flags in place of
            the `value` positional argument to pass a boolean
            instead of a string. For example:

              ts-cli config set ignore-ssl --true
            """
        ),
    )
    shared_cmd_args(parser)
    add_key_argument(parser)
    value_group = parser.add_argument_group("Value")
    value_group = value_group.add_mutually_exclusive_group(required=True)
    value_group.add_argument(
        "value", help="the new config value as a string", nargs="?"
    )
    value_group.add_argument(
        "--string",
        help="the new config value as a string",
        dest="value",
    )
    value_group.add_argument(
        "--true, -t",
        help="the new config value as the value true",
        action="store_true",
        dest="value",
    )
    value_group.add_argument(
        "--false, -f",
        help="the new config value as the value false",
        action="store_false",
        dest="value",
    )
    parser.set_defaults(func=config_set)


def add_config_save_parser(subparsers):
    parser = subparsers.add_parser(
        "save",
        help="Save an entire config file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Copies an entire configuration file
             Example: ts-cli config save ./config.json
            """
        ),
    )
    shared_cmd_args(parser)
    parser.add_argument(
        "file",
        help="yaml or json formatted file with an API configuration",
        type=argparse.FileType("r"),
    )
    parser.set_defaults(func=config_save)


def config_get(args):
    cli_config = CliConfig(args)
    value = cli_config.get_pretty(args.key)
    if value is None:
        sys.exit(1)
    else:
        print(value)


def config_set(args):
    cli_config = CliConfig(args)
    if cli_config.profile is not None and args.key == "profile":
        raise CriticalError(
            f"Cannot set profile config inside profile {cli_config.profile}"
        )
    if not write_config_file(cli_config.profile, {args.key: args.value}):
        sys.exit(1)


def config_unset(args):
    cli_config = CliConfig(args)
    if cli_config.get(args.key) is None:
        sys.exit(1)
    elif cli_config.get_profile().get(args.key) is None:
        emit_warning(
            f"Config key '{args.key}' is already unset for profile '{cli_config.profile}', but is still bound globally"
        )
        sys.exit(1)
    elif not write_config_file(cli_config.profile, {args.key: None}):
        sys.exit(1)


def config_save(args):
    cli_config = CliConfig(args)
    loaded_config = load_from_yaml_or_json_if_present(args.file.name)
    if not write_config_file(cli_config.profile, loaded_config):
        sys.exit(1)
