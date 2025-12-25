import json
import os
import re
from pathlib import Path
from typing import Callable, Optional, Union

import yaml

from ts_cli.config.config import Config
from ts_cli.config.provider import Provider
from ts_cli.config.util import load_from_yaml_or_json_if_present, to_version
from ts_cli.util.emit import emit_warning


def config_path():
    return Path.joinpath(Path.home(), ".config", "tetrascience", "config")


def load_home_config_file() -> dict:
    """
    Loads api config from a user's home directory
    :return:
    """
    return load_from_yaml_or_json_if_present(config_path())


def set_value_in_config(config: dict, key: str, value) -> None:
    if value is not None and value != {}:
        config[key] = value
    elif key in config:
        del config[key]


VALID_KEYS = {
    "ignore-ssl",
    "org",
    "auth-token",
    "api-url",
    "format",
    "profile",
    "platform-version",
}


def is_valid_record(key: str, raw_value, parsed_value) -> bool:
    if key not in VALID_KEYS:
        emit_warning(f"Config key '{key}' is not recognized and will be ignored")
        return False
    if raw_value is not None and parsed_value is None:
        emit_warning(
            f"Config key '{key}' was supplied with an invalid value and will be ignored"
        )
        return False
    return True


def parse_value(key: str, value):
    if value is None:
        return value
    elif key == "ignore_ssl":
        if str(value).lower() in {"true", "1", "t"}:
            return True
        if str(value).lower() in {"false", "0", "f"}:
            return False
        return None
    elif key == "format":
        value = str(value).lower()
        return value if value in {"json", "yaml"} else None
    elif key == "platform_version":
        value = to_version(value)
        return value if re.compile(r"^v\d\.\d$").match(value) else None
    else:
        return str(value)


def parse_valid_values(values: dict) -> dict:
    values = {key: (value, parse_value(key, value)) for key, value in values.items()}
    return {
        key.replace("-", "_"): parsed_value
        for key, (raw_value, parsed_value) in values.items()
        if is_valid_record(key.replace("_", "-"), raw_value, parsed_value)
    }


def open_config():
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, "w+", encoding="utf-8")


def write_config_file(profile: Optional[str], values: dict) -> bool:
    config = load_home_config_file()
    values = parse_valid_values(values)
    for key, value in values.items():
        if profile is None:
            set_value_in_config(config, key, value)
        else:
            profiles = _get_sub_dict(config, "profiles")
            profile_config = _get_sub_dict(profiles, profile)
            set_value_in_config(profile_config, key, value)
            set_value_in_config(profiles, profile, profile_config)
            set_value_in_config(config, "profiles", profiles)
    config_format = config.get("format", "json")
    with open_config() as file:
        if config_format == "yaml":
            yaml.dump(config, file)
        elif config_format == "json":
            json.dump(config, file)
        else:
            raise ValueError(f"Unrecognized format: {config_format}")
    return bool(values)


def load_env_config() -> dict:
    """
    Loads api config from process's environment
    :return:
    """
    config = {}
    prefix = "TS_"
    for environ_key, value in os.environ.items():
        if environ_key.startswith(prefix):
            key = environ_key.replace(prefix, "").lower()
            config[key] = value
    return config


def load_argument_provided_config(args):
    """
    Pulls the api config out of the file pointed to by the --config CLI argument
    :param args:
    :return:
    """

    def applicator():
        if getattr(args, "config", None) is not None:
            return load_from_yaml_or_json_if_present(args.config.name)
        return {}

    return applicator


def _get_sub_dict(parent: dict, key: str) -> dict:
    """
    Gets a value out of a dict, and ensures that the values is always a dict
    :param parent:
    :param key:
    :return:
    """
    value = parent.get(key, None)
    if isinstance(value, dict):
        return value
    return {}


def _decorate_initializer(
    initializer: Callable[[], dict],
    profile: Union[str, None] = None,
) -> Callable[[], dict]:
    """
    Decorates an initializer such that it will replace values from an "overwrites" sub-object
    if the respective profile name or org name is provided
    :param initializer:
    :param profile:
    :return:
    """

    def applicator() -> dict:
        values = initializer()
        if profile is not None:
            profiles = _get_sub_dict(values, "profiles")
            overwrites = _get_sub_dict(profiles, profile)
            values = {
                **values,
                **overwrites,
            }
        return values

    return applicator


class CliConfig(Config):
    def __init__(self, args):
        super().__init__()
        self._type = "Config"
        # First get the Profile name
        if args.__dict__.get("global"):
            self.profile = None
        else:
            self.profile = CliConfig._make_provider(args).get("profile")
        # Then get the remaining, because they can be set under the "profiles" header
        self._provider = CliConfig._make_provider(args, profile=self.profile)

    def get(self, key: str):
        return super().get(key.replace("-", "_"))

    def get_pretty(self, key: str):
        value = self.get(key)
        if key == "auth_token" and isinstance(value, str):
            short_value = value[0:7]
            if short_value != value:
                return f"{short_value}..."
        return value

    def get_profile(self):
        config = load_home_config_file()
        if self.profile is None:
            return config
        else:
            return _get_sub_dict(_get_sub_dict(config, "profiles"), self.profile)

    @staticmethod
    def _make_provider(args, profile=None):
        return Provider.pipe(
            lambda: args.__dict__,
            _decorate_initializer(load_argument_provided_config(args), profile=profile),
            load_env_config,
            _decorate_initializer(load_home_config_file, profile=profile),
        )
