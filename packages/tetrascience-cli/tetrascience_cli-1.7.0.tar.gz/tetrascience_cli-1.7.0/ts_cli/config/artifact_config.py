from typing import Optional

from ts_cli.config.cli_config import CliConfig
from ts_cli.config.interactive_config import InteractiveConfig
from ts_cli.config.util import to_version
from ts_cli.util.colour import blue, green


def _colour_string(string: Optional[str]):
    if string:
        return green(string)
    else:
        return blue("<unset>")


def _ensure_string(string: Optional[str]) -> str:
    if string:
        return string
    else:
        return "<unset>"


class ArtifactConfig(InteractiveConfig):
    """
    Artifact Configuration Abstract Class
    """

    def __init__(self, args, *, interactive: bool):
        super().__init__(args, interactive=interactive)
        self._cli_config = CliConfig(args)
        self._interactive = interactive
        self.type = None
        self.namespace = None
        self.slug = None
        self.version = None

    def _parse(self, values: dict) -> dict:
        return {
            "type": values.get("type") or None,
            "namespace": values.get("namespace") or None,
            "slug": str.lower(values.get("slug") or "") or None,
            "version": (
                to_version(values.get("version"))
                if (values.get("version") or None) is not None
                else None
            ),
        }

    def print(self):
        print(self.to_string(colour=True))

    def to_string(self, *, colour=False):
        return self.format(
            {key: self.get(key) for key in self._get_keys()}, colour=colour
        )

    def format(self, values: dict, colour=True):
        artifact_type = self._format_string(values.get("type"), colour=colour)
        namespace = self._format_string(values.get("namespace"), colour=colour)
        slug = self._format_string(values.get("slug"), colour=colour)
        version = self._format_string(values.get("version"), colour=colour)
        return f"{artifact_type}: {namespace}/{slug}:{version}"

    @staticmethod
    def _format_string(string: Optional[str], colour: bool):
        if colour:
            return _colour_string(string)
        return _ensure_string(string)
