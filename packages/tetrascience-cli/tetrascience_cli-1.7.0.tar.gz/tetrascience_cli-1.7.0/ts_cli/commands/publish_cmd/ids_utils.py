import json
from pathlib import Path
from typing import List

from ts_cli.config.util import load_from_json_file_if_present


def update_expected_json(path: Path, manifest: dict) -> dict:
    """
    Adds namespace/slug:version to the expected.json
    :param path:
    :param manifest:
    :return:
    """
    expected = load_from_json_file_if_present(path)
    if "@idsNamespace" in expected:
        expected["@idsNamespace"] = manifest.get("namespace")
    if "@idsType" in expected:
        expected["@idsType"] = manifest.get("slug")
    if "@idsVersion" in expected:
        expected["@idsVersion"] = manifest.get("version")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(expected, file)
    return expected


def get(container: dict, keys: List[str]) -> object:
    try:
        if len(keys) == 0:
            raise ValueError("Must provide non-empty list of keys")
        if len(keys) == 1:
            return container[keys[0]]
        return get(container[keys[0]], keys[1:])
    except KeyError:
        return None


def update_schema_json(path: Path, manifest: dict) -> dict:
    """
    Adds namespace/slug:version fields to the schema.json
    :param path:
    :param manifest:
    :return:
    """
    namespace = manifest.get("namespace")
    slug = manifest.get("slug")
    version = manifest.get("version")
    schema = load_from_json_file_if_present(path)
    if isinstance(get(schema, ["properties", "@idsNamespace", "const"]), str):
        schema["properties"]["@idsNamespace"]["const"] = namespace
    if isinstance(get(schema, ["properties", "@idsType", "const"]), str):
        schema["properties"]["@idsType"]["const"] = slug
    if isinstance(get(schema, ["properties", "@idsVersion", "const"]), str):
        schema["properties"]["@idsVersion"]["const"] = version
    if isinstance(get(schema, ["$id"]), str):
        schema["$id"] = (
            f"https://ids.tetrascience.com/{namespace}/{slug}/{version}/schema.json"
        )
    with open(path, "w", encoding="utf-8") as file:
        json.dump(schema, file)
    return schema


def update_ids(path: str, manifest: dict) -> None:
    """
    Updates existing IDS files, and writes them back to the artifact directory
    :param path:
    :param manifest:
    :return:
    """
    if Path(path, "schema.json").exists():
        update_schema_json(Path(path, "schema.json"), manifest)
    if Path(path, "expected.json").exists():
        update_expected_json(Path(path, "expected.json"), manifest)
