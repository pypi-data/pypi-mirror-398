import json
import os
import re
from pathlib import Path
from typing import Any, Callable, TextIO, Union

import toml
import yaml
from inquirer import errors

from ts_cli.util.emit import emit_warning


def load_from_loader_if_present(
    *, loader: Callable[[TextIO], Any], name: str, path: Union[str, Path]
) -> dict:
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as file:
            result = loader(file)
        if isinstance(result, dict):
            return result
        emit_warning(
            f"{path} contained {name} that could not be read as a dictionary. It will be ignored"
        )
    return {}


def load_from_toml_file_if_present(path: Union[str, Path]) -> dict:
    """
    Loads a dict from a toml file.
    If the file is not present, returns {}
    :param path:
    :return:
    """
    return load_from_loader_if_present(path=path, name="toml", loader=toml.load)


def load_from_json_file_if_present(path: Union[str, Path]) -> dict:
    """
    Loads a dict from a json file.
    If the file is not present, returns {}
    :param path:
    :return:
    """
    return load_from_loader_if_present(path=path, name="json", loader=json.load)


def load_from_yaml_file_if_present(path: Union[str, Path]) -> dict:
    """
    Loads a dict from a yaml file.
    If the file is not present, returns {}
    :param path:
    :return:
    """
    return load_from_loader_if_present(path=path, name="yaml", loader=yaml.safe_load)


def load_from_yaml_or_json_if_present(path: Union[str, Path]) -> dict:
    """
    Loads a dict from a yaml OR json formatted file.
    If the file is not present, returns {}

    Attempt JSON first, as this is generally the stricter syntax, and a safer bet :)
    :param path:
    :return:
    """
    try:
        return load_from_json_file_if_present(path)
    except Exception:
        try:
            return load_from_yaml_file_if_present(path)
        except Exception:
            emit_warning(
                f"{path} could not be read as yaml or as json. It will be ignored."
            )
            return {}


def to_version(version: str) -> str:
    """
    :param version:
    :return:
    """
    if re.compile(r"^v").match(version):
        return version
    return f"v{version}"


def is_platform_version(version: str) -> bool:
    return bool(re.compile(r"^v\d\.\d$").match(version))


def is_private_namespace(namespace: str) -> bool:
    """
    :param namespace: the string to test
    :return:
    """
    ns_pattern = re.compile("^private-[0-9a-zA-Z-]+$")
    return (
        ns_pattern.match(namespace)
        and not namespace.endswith("-")
        and not re.search(r"--", namespace)
    )


def is_any_or_empty_namespace(namespace: str) -> bool:
    return namespace == "" or namespace == "common" or is_private_namespace(namespace)


def private_namespace_error(namespace: str) -> str:
    """
    Provides an error message for when a namespace isn't really a namespace
    :param namespace: the "namespace" that will be used in the error message
    :return:
    """
    return (
        f"Invalid namespace {namespace}. Namespace must start with "
        f"'private-' followed by alphanumeric characters or single "
        f"hyphens."
    )


def any_namespace_error(namespace: str) -> str:
    """
    Provides an error message for when a namespace isn't really a namespace
    :param namespace: the "namespace" that will be used in the error message
    :return:
    """
    return (
        f"Invalid namespace {namespace}. Namespace must start with "
        f"'private-' followed by alphanumeric characters or single "
        f"hyphens, or be equal to the string 'common'."
    )


def assert_is_non_empty(_, value):
    if value == "":
        raise errors.ValidationError("", reason="Value cannot be empty")
    return True


def assert_is_private_namespace(_, namespace):
    """
    Throws an error if the "namespace" isn't really a namespace
    Empty parameter to match the inquirer API
    :param _:
    :param namespace:
    :return:
    """
    if not is_private_namespace(namespace):
        raise errors.ValidationError("", reason=private_namespace_error(namespace))
    return True


def assert_is_any_namespace(_, namespace):
    if not is_any_or_empty_namespace(namespace):
        raise errors.ValidationError("", reason=any_namespace_error(namespace))
    return True


def assert_is_artifact_version(_, version):
    """
    Validates that an artifact version string is in the correct format.
    Version must start with 'v' followed by semantic version (e.g., v1.0.0).
    Empty parameter to match the inquirer API.
    :param _:
    :param version:
    :return:
    """
    if not version or version == "":
        raise errors.ValidationError("", reason="Version cannot be empty")

    # Check if version starts with 'v' followed by semantic version pattern
    version_pattern = re.compile(r"^v\d+\.\d+\.\d+$")
    if not version_pattern.match(version):
        raise errors.ValidationError(
            "", reason="Version must be in format 'vX.Y.Z' (e.g., v1.0.0)"
        )
    return True
