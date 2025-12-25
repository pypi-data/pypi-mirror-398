import json
from pathlib import Path

from ts_cli.config.artifact_config import ArtifactConfig
from ts_cli.config.util import load_from_json_file_if_present


def update_manifest_fields(manifest: dict, artifact_config: ArtifactConfig):
    """
    Overwrites fields in the manifest dict with fields from the artifact configuration
    :param manifest:
    :param artifact_config:
    :return:
    """
    manifest_type = (
        "connector" if artifact_config.type == "data-app" else artifact_config.type
    )

    manifest["type"] = manifest_type
    manifest["namespace"] = artifact_config.namespace
    manifest["slug"] = artifact_config.slug
    manifest["version"] = artifact_config.version
    return manifest


def update_manifest(path: str, artifact_config: ArtifactConfig) -> dict:
    """
    Updates the manifest.json and writes it back to the artifact directory
    :param path:
    :param artifact_config:
    :return:
    """
    if Path(path, "manifest.json").exists():
        manifest = load_from_json_file_if_present(Path(path, "manifest.json"))
        manifest = update_manifest_fields(manifest, artifact_config)
        with open(Path(path, "manifest.json"), "w", encoding="utf-8") as file:
            file.write(json.dumps(manifest))
        return manifest
    return update_manifest_fields({}, artifact_config)
