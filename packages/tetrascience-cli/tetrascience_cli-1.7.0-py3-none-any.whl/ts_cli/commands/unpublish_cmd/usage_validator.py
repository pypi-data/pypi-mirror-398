import textwrap

from ts_cli.api import TsApi
from ts_cli.commands.publish_cmd.validation.validator import Validator
from ts_cli.config.update_artifact_config import UpdateArtifactConfig
from ts_cli.errors.critical_error import CriticalError
from ts_cli.util.emit import emit_warning


def validate_unused(*, ts_api: TsApi, artifact_config: UpdateArtifactConfig) -> None:
    get_usage_validator(ts_api=ts_api, artifact_config=artifact_config).validate()


def get_usage_validator(
    *, ts_api: TsApi, artifact_config: UpdateArtifactConfig
) -> "UsageValidator":
    if (artifact_config.type == "protocol") or (artifact_config.type == "tetraflow"):
        return PipelineArtifactValidator(
            ts_api=ts_api, artifact_config=artifact_config, exiting=False
        )
    if artifact_config.type == "task-script":
        return TaskScriptValidator(
            ts_api=ts_api, artifact_config=artifact_config, exiting=False
        )
    if artifact_config.type == "ids":
        return IdsValidator(
            ts_api=ts_api, artifact_config=artifact_config, exiting=False
        )
    if artifact_config.type == "data-app":
        return DataAppValidator(
            ts_api=ts_api, artifact_config=artifact_config, exiting=False
        )
    if artifact_config.type == "connector":
        return AlwaysPassing(
            ts_api=ts_api, artifact_config=artifact_config, exiting=False
        )
    if artifact_config.type == "schema":
        return AlwaysPassing(
            ts_api=ts_api, artifact_config=artifact_config, exiting=False
        )
    raise CriticalError(f"Invalid type provided: {artifact_config.type}")


class UsageValidator(Validator):
    """
    Abstract class
    """

    user: str = "user"

    def __init__(
        self, *, ts_api: TsApi, artifact_config: UpdateArtifactConfig, exiting: bool
    ):
        self._ts_api = ts_api
        self._artifact_config = artifact_config
        super().__init__(exiting=exiting)

    def get_warning_message(self, count: int) -> str:
        object_word = self.user if count == 1 else f"{self.user}s"
        return f"This {self._artifact_config.type} artifact is used by at least {count} {object_word}:"

    def get_dependents(self) -> list[str]:
        return []

    def validate(self):
        dependents = self.get_dependents()
        count = len(dependents)
        if count > 0:
            dependents = [f"• {dependent}" for dependent in dependents]
            dependents_string = textwrap.indent("\n".join(dependents), "  ")
            emit_warning(f"{self.get_warning_message(count)}\n{dependents_string}")


class AlwaysPassing(UsageValidator):
    def get_warning_message(self, count: int) -> str:
        return f"This {self._artifact_config.type} artifact is not being used"

    def get_dependents(self) -> list[str]:
        return []


class PipelineArtifactValidator(UsageValidator):
    user = "pipeline"

    def artifact_matches(self, pipeline: dict) -> bool:
        namespace = pipeline.get("masterScriptNamespace", None)
        slug = pipeline.get("masterScriptSlug", None)
        version = pipeline.get("masterScriptVersion", None)
        return (
            self._artifact_config.namespace == namespace
            and self._artifact_config.slug == slug
            and self._artifact_config.version == version
        )

    def get_dependents(self) -> list[str]:
        pipelines = []
        next_page = 0
        while next_page is not None:
            page, next_page = self._ts_api.get_pipelines_with_artifact(
                namespace=self._artifact_config.namespace,
                slug=self._artifact_config.slug,
                version=self._artifact_config.version,
                artifact_type=self._artifact_config.type,
                page=next_page,
            )
            pipelines = pipelines + page
        pipelines = filter(self.artifact_matches, pipelines)
        return [f"pipeline: {pipeline.get('name')}" for pipeline in pipelines]


class TaskScriptValidator(UsageValidator):
    user = "protocol"

    def get_dependents(self) -> list[str]:
        protocols = self._ts_api.get_protocols_with_task_script(
            namespace=self._artifact_config.namespace,
            slug=self._artifact_config.slug,
            version=self._artifact_config.version,
        )
        return [
            f"protocol: {protocol.get('namespace')}/{protocol.get('slug')}:{protocol.get('version')}"
            for protocol in protocols
        ]


class IdsValidator(UsageValidator):
    user = "task-script"

    def get_dependents(self) -> list[str]:
        task_scripts = self._ts_api.get_task_scripts_with_ids(
            namespace=self._artifact_config.namespace,
            slug=self._artifact_config.slug,
            version=self._artifact_config.version,
        )
        return [
            f"task-script: {task_script.get('namespace')}/{task_script.get('slug')}:{task_script.get('version')}"
            for task_script in task_scripts
        ]


class DataAppValidator(UsageValidator):
    user = "data-app"

    def data_app_matches(self, data_app: dict) -> bool:
        """
        Check if a data app matches the artifact being unpublished.
        Data apps have scope (namespace), version, and slug fields.
        """
        scope = data_app.get("scope", None)
        slug = data_app.get("slug", None)
        version = data_app.get("version", None)
        return (
            self._artifact_config.namespace == scope
            and self._artifact_config.slug == slug
            and self._artifact_config.version == version
        )

    def get_dependents(self) -> list[str]:
        data_apps = []
        next_page = 1
        while next_page is not None:
            page, next_page = self._ts_api.get_data_apps(page=next_page)
            data_apps = data_apps + page

        matching_apps = filter(self.data_app_matches, data_apps)
        return [f"data app: {app.get('name', 'Unknown')}" for app in matching_apps]
