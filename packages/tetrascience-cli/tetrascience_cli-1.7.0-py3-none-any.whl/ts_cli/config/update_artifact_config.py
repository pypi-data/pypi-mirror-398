from pathlib import Path
from typing import List

import inquirer

from ts_cli.commands.init_cmd.kinds import KINDS
from ts_cli.config.artifact_config import ArtifactConfig
from ts_cli.config.provider import Provider
from ts_cli.config.util import (
    assert_is_artifact_version,
    assert_is_non_empty,
    assert_is_private_namespace,
    load_from_json_file_if_present,
    load_from_toml_file_if_present,
    load_from_yaml_file_if_present,
    to_version,
)


def map_ids_schema_to_manifest(schema: dict) -> dict:
    properties = schema.get("properties", {})
    namespace = properties.get("@idsNamespace", {}).get("const", None)
    slug = properties.get("@idsType", {}).get("const", None)
    version = properties.get("@idsVersion", {}).get("const", None)
    return {"namespace": namespace, "slug": slug, "version": version}


def map_pyproject_to_manifest(pyproject: dict) -> dict:
    version = pyproject.get("tool", {}).get("poetry", {}).get("version")
    return {"version": to_version(version) if version is not None else None}


class UpdateArtifactConfig(ArtifactConfig):
    def __init__(self, args, *, interactive: bool):
        super().__init__(args, interactive=interactive)
        self._type: str = "artifact"
        non_interactive_provider = Provider.pipe(
            lambda: args.__dict__,
            lambda: load_from_json_file_if_present(Path(args.source, "manifest.json")),
            lambda: load_from_yaml_file_if_present(Path(args.source, "protocol.yml")),
            lambda: load_from_yaml_file_if_present(Path(args.source, "protocol.yaml")),
            lambda: load_from_json_file_if_present(Path(args.source, "protocol.json")),
            lambda: map_ids_schema_to_manifest(
                load_from_json_file_if_present(Path(args.source, "schema.json"))
            ),
            lambda: map_pyproject_to_manifest(
                load_from_toml_file_if_present(Path(args.source, "pyproject.toml"))
            ),
            lambda: {
                "namespace": self._cli_config.get("org")
                and f"private-{self._cli_config.get('org')}"
            },
        )
        values = self._resolve(non_interactive_provider)
        self._provider = Provider(lambda: values)
        self.type: str = values.get("type")
        self.namespace: str = values.get("namespace")
        self.slug: str = values.get("slug")
        self.version: str = values.get("version")
        print("Using the following artifact configuration:")
        self.print()
        self.validate(self._get_keys())

    def _get_keys(self) -> List[str]:
        return ["type", "namespace", "slug", "version"]

    def _get_correct_message(self, answers: dict) -> str:
        # Use values from answers, but fall back to self values if answers has None or empty string
        # This ensures that the version from manifest.json is displayed even when not provided via --version flag
        display_values = {
            "type": answers.get("type") or self.type,
            "namespace": answers.get("namespace") or self.namespace,
            "slug": answers.get("slug") or self.slug,
            "version": answers.get("version") or self.version,
        }
        return f"Correct? [{self.format(display_values)}]"

    def _get_inquiry(self, existing_values: dict):
        """
        Returns a list of inquirer questions, using existing values as defaults
        :param existing_values:
        :return:
        """

        return [
            inquirer.List(
                "type",
                message="Artifact Type",
                choices=KINDS,
                default=existing_values.get("type"),
            ),
            inquirer.Text(
                "namespace",
                message="Artifact Namespace",
                default=existing_values.get("namespace"),
                validate=assert_is_private_namespace,
            ),
            inquirer.Text(
                "slug",
                message="Artifact Slug",
                default=existing_values.get("slug"),
                validate=assert_is_non_empty,
            ),
            inquirer.Text(
                "version",
                message="Artifact Version",
                default=existing_values.get("version"),
                validate=assert_is_artifact_version,
            ),
        ]
