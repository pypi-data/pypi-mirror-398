from argparse import ArgumentParser
from importlib import metadata

from ts_cli.commands.config_cmd import add_config_parser
from ts_cli.commands.init_cmd import add_init_parser
from ts_cli.commands.publish_cmd import add_publish_parser
from ts_cli.commands.unpublish_cmd import add_unpublish_parser

version = metadata.version("tetrascience-cli")


parser = ArgumentParser(
    prog="ts-cli", description="TetraScience Command Line Interface"
)

parser.add_argument("--version", action="version", version=version)

subparsers = parser.add_subparsers(title="commands", required=True, dest="command")

add_init_parser(subparsers)
add_publish_parser(subparsers)
add_unpublish_parser(subparsers)
add_config_parser(subparsers)
