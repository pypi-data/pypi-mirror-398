from typing import Callable, Iterator, List, Optional, Tuple

import inquirer

from ts_cli.commands.init_cmd.kinds import KIND_DEFAULTS, KIND_TEMPLATES, KINDS
from ts_cli.config.artifact_config import ArtifactConfig
from ts_cli.config.interactive_config import InteractiveConfig
from ts_cli.config.provider import Provider
from ts_cli.config.util import assert_is_any_namespace
from ts_cli.errors.critical_error import CriticalError


def map_args_prefix(args: dict, prefix: str) -> dict:
    return {
        "namespace": args.get(f"{prefix}_namespace"),
        "slug": args.get(f"{prefix}_slug"),
        "version": args.get(f"{prefix}_version"),
        "function": args.get(f"{prefix}_function"),
    }


def map_updates(
    argument: Optional[dict], *functions: Callable[[dict], Optional[dict]]
) -> Optional[dict]:
    value = argument
    for function in functions:
        if value is not None:
            updates = function(value)
            value = {**value, **updates} if updates is not None else None
    return value


class InitTemplateConfig(InteractiveConfig):
    def __init__(
        self,
        args,
        *,
        interactive: bool,
    ):
        super().__init__(args, interactive=interactive)
        self._type: str = "Template"
        default_template = (
            KIND_DEFAULTS[args.kind]
            if (args.kind and args.kind in KIND_DEFAULTS)
            else None
        )
        values = self._resolve(
            Provider.pipe(
                lambda: args.__dict__, lambda: {"template": default_template}
            ),
            skip_confirmation=True,
        )
        self._provider = Provider(lambda: values)
        self.kind: str = self._provider.get("kind")
        self.template: str = self._provider.get("template")
        self._print_config_keys(self, self._get_keys(), self._type)
        self.validate(self._get_keys())

    def _get_keys(self) -> List[str]:
        return ["kind", "template"]

    def validate(self, requirements: List[str]):
        super().validate(requirements)
        if self.kind not in KIND_TEMPLATES:
            raise CriticalError(f"Unrecognized kind: '{self.kind}'")
        if self.template not in KIND_TEMPLATES[self.kind]:
            raise CriticalError(
                f"Invalid template '{self.template}' for kind '{self.kind}'. "
                f"Must be one of {KIND_TEMPLATES[self.kind]}"
            )

    @staticmethod
    def _interactive_get_kind(values: dict) -> Optional[dict]:
        return inquirer.prompt(
            [
                inquirer.List(
                    "kind",
                    message="Kind",
                    choices=KINDS,
                    default=values.get("kind"),
                )
            ]
        )

    @staticmethod
    def _interactive_get_template(values: dict) -> Optional[dict]:
        selected_kind = values.get("kind")

        if len(KIND_TEMPLATES[selected_kind]) == 1:
            return {"template": KIND_TEMPLATES[selected_kind][0]}

        default_template = None
        # Set selected template as default if it's valid for the selected kind
        current_template = values.get("template")
        if current_template and current_template in KIND_TEMPLATES[selected_kind]:
            default_template = current_template

        return inquirer.prompt(
            [
                inquirer.List(
                    "template",
                    message="Template",
                    choices=KIND_TEMPLATES[selected_kind],
                    default=default_template,
                )
            ]
        )

    def _interactive_resolve_values(
        self, values: dict, confirmation: Optional[inquirer.Confirm] = None
    ) -> Optional[dict]:
        return map_updates(
            values,
            self._interactive_get_kind,
            self._interactive_get_template,
            lambda _: inquirer.prompt(confirmation) if confirmation else {},
        )


class InitArtifactConfig(ArtifactConfig):
    def __init__(
        self,
        args,
        *,
        interactive: bool,
        artifact_type: str,
        type_pretty: str,
        defaults: dict,
    ):
        super().__init__(args, interactive=interactive)
        self._type: str = type_pretty
        self.type = artifact_type
        self.prefix: str = artifact_type.replace("-", "_")
        args = args.__dict__
        non_interactive_provider = Provider.pipe(
            lambda: {"type": artifact_type},
            lambda: map_args_prefix(args, self.prefix),
            lambda: args,
            lambda: {
                "namespace": self._cli_config.get("org")
                and f"private-{self._cli_config.get('org')}"
            },
        )
        values = self._resolve(non_interactive_provider)
        self._provider = Provider.pipe(lambda: values, lambda: defaults)

    def _get_keys(self) -> List[str]:
        return ["type", "namespace", "slug", "version"]

    def _get_correct_message(self, answers: dict) -> str:
        """
        :param answers:
        :return:
        """
        return f"Correct? [{self.format({**answers, 'type': self.type})}]"

    def _get_inquiry(self, existing_values: dict):
        """
        Returns a list of inquirer questions, using existing values as defaults
        :param existing_values:
        :return:
        """
        return [
            inquirer.Text(
                "namespace",
                message=f"{self._type} Namespace",
                default=existing_values.get("namespace"),
                validate=assert_is_any_namespace,
            ),
            inquirer.Text(
                "slug",
                message=f"{self._type} Slug",
                default=existing_values.get("slug"),
            ),
            inquirer.Text(
                "version",
                message=f"{self._type} Version",
                default=existing_values.get("version"),
            ),
        ]

    def _parse(self, values: dict) -> dict:
        return super()._parse({**values, "type": self.type})

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        for key in self._get_keys():
            yield key, self.get(key)


class InitTaskScriptReferenceConfig(InitArtifactConfig):
    def __init__(
        self,
        args,
        *,
        defaults: dict,
        interactive: bool,
    ):
        super().__init__(
            args,
            interactive=interactive,
            artifact_type="task-script",
            type_pretty="Task Script",
            defaults={
                **defaults,
                "function": "main",
            },
        )

    def _get_inquiry(self, existing_values: dict):
        return super()._get_inquiry(existing_values) + [
            inquirer.Text(
                "function",
                message=f"{self._type} Function",
                default=existing_values.get("function"),
            )
        ]

    def _get_keys(self) -> List[str]:
        return super()._get_keys() + ["function"]

    def _parse(self, values: dict) -> dict:
        return {
            **super()._parse(values),
            "function": values.get("function") or None,
        }

    def format(self, values, colour=True) -> str:
        artifact_string = super().format(values, colour=colour)
        function_name = self._format_string(values.get("function"), colour=colour)
        return f"{artifact_string}@{function_name}"


class InitDataAppConfig(InitArtifactConfig):
    def __init__(
        self,
        args,
        *,
        interactive: bool,
    ):
        super().__init__(
            args,
            interactive=interactive,
            artifact_type="data-app",
            type_pretty="Data App",
            defaults={
                "namespace": "common",
                "slug": "example",
                "version": "v0.1.0",
            },
        )

    @staticmethod
    def data_app_package_dir(namespace: str, slug: str) -> str:
        """Create the package directory name for data apps."""
        slug_clean = slug.replace("-", "_")
        if namespace == "common":
            return f"ts_data_app_{slug_clean}"
        namespace_clean = namespace.replace("-", "_")
        return f"ts_{namespace_clean}_data_app_{slug_clean}"

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        slug: str = self.get("slug")
        namespace: str = self.get("namespace")
        for items in super().__iter__():
            yield items

        package_directory = InitDataAppConfig.data_app_package_dir(namespace, slug)
        yield "artifact_title", slug.replace("-", " ").title()
        yield "package_dir", package_directory
        yield "package_name", package_directory.replace("_", "-")
