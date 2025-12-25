import argparse
import os

from ts_cli.config.util import (
    any_namespace_error,
    is_any_or_empty_namespace,
    is_platform_version,
    is_private_namespace,
    private_namespace_error,
    to_version,
)


def existing_folder_type(arg_value):
    if os.path.isdir(arg_value):
        return arg_value
    raise argparse.ArgumentTypeError(f"Invalid directory provided: {arg_value}")


def private_namespace_type(arg_value: str) -> str:
    """
    Namespace validation function. Namespace must start with 'private-' and
    only contains alphanumeric characters and hyphens. A hyphen cannot
    succeed another hyphen. An exception is raised for invalid namespaces.

    Args:
        arg_value (str): namespace

     Returns:
         arg_value (str): validated namespace
    """

    # validate namespace
    if not is_private_namespace(arg_value):
        raise argparse.ArgumentTypeError(private_namespace_error(arg_value))

    return arg_value


def any_namespace_type(arg_value: str) -> str:
    """
    Namespace validation function. Namespace must start with 'private-' and
    only contains alphanumeric characters and hyphens. A hyphen cannot
    succeed another hyphen. An exception is raised for invalid namespaces.

    Also: 'common' is acceptable

    Args:
        arg_value (str): namespace

     Returns:
         arg_value (str): validated namespace
    """

    # validate namespace
    if not is_any_or_empty_namespace(arg_value):
        raise argparse.ArgumentTypeError(any_namespace_error(arg_value))

    return arg_value


def platform_version_type(version: str) -> str:
    version = to_version(version)
    if not is_platform_version(version):
        raise argparse.ArgumentTypeError(
            "Platform Version should be of the format 'v\\d.\\d'"
        )

    return version
