import json
from pathlib import Path

import yaml

from ts_cli.config.util import (
    load_from_json_file_if_present,
    load_from_yaml_file_if_present,
)


def update_protocol_json(path: Path, manifest: dict) -> dict:
    """
    Adds all manifest fields to the protocol.json
    :param path:
    :param manifest:
    :return:
    """
    protocol = load_from_json_file_if_present(path)
    for key, value in manifest.items():
        if key in protocol:
            protocol[key] = value
    with open(path, "w", encoding="utf-8") as file:
        file.write(json.dumps(protocol))
    return protocol


def update_protocol_yaml(path: Path, manifest: dict) -> dict:
    """
    Adds all manifest fields to the protocol.{yml,yaml}
    :param path:
    :param manifest:
    :return:
    """
    protocol = load_from_yaml_file_if_present(path)
    for key, value in manifest.items():
        if key in protocol:
            protocol[key] = value
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(protocol, file)
    return protocol


def update_protocol(path: str, manifest: dict) -> None:
    """
    Updates the protocol if it exists, and writes it back to the artifact directory
    :param path:
    :param manifest:
    :return:
    """
    if Path(path, "protocol.json").exists():
        update_protocol_json(Path(path, "protocol.json"), manifest)
    if Path(path, "protocol.yml").exists():
        update_protocol_yaml(Path(path, "protocol.yml"), manifest)
    if Path(path, "protocol.yaml").exists():
        update_protocol_yaml(Path(path, "protocol.yaml"), manifest)
