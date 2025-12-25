from typing import List, Optional

import inquirer

from ts_cli.config.cli_config import CliConfig
from ts_cli.config.config import Config
from ts_cli.config.provider import Provider
from ts_cli.errors.critical_error import CriticalError


class InteractiveConfig(Config):
    def __init__(self, args, *, interactive: bool):
        super().__init__()
        self._cli_config = CliConfig(args)
        self._interactive = interactive
        self.type = None
        self.namespace = None
        self.slug = None
        self.version = None

    def _resolve(self, provider: Provider, skip_confirmation: bool = False) -> dict:
        values: dict = {key: provider.get(key) or None for key in self._get_keys()}
        if not self._interactive:
            return values
        return self._interactive_resolve_values_and_confirm(values, skip_confirmation)

    def _get_keys(self) -> List[str]:
        return []

    def _interactive_resolve_values(
        self, values: dict, confirmation: Optional[inquirer.Confirm] = None
    ) -> Optional[dict]:
        inquiry = self._get_inquiry(values)
        if confirmation:
            inquiry.append(confirmation)
        return inquirer.prompt(inquiry)

    def _interactive_resolve_values_and_confirm(
        self, values: dict, skip_confirmation: bool = False
    ) -> dict:
        if skip_confirmation:
            confirmation = None
        else:
            confirmation = inquirer.Confirm(
                "confirmed",
                message=self._get_correct_message,
                default=False,
            )

        values["confirmed"] = False
        while values.get("confirmed", False) is not True:
            values = self._interactive_resolve_values(values, confirmation)
            if values is None:
                raise CriticalError("Configuration interrupted")
            if skip_confirmation:
                values["confirmed"] = True
        return self._parse(values)

    def _parse(self, values: dict) -> dict:
        return values

    def _get_correct_message(self, answers: dict) -> str:
        return "Correct?"

    def _get_inquiry(self, existing_values: dict) -> list:
        """
        Returns a list of inquirer questions, using existing values as defaults
        :param existing_values:
        :return:
        """
        raise NotImplemented()
