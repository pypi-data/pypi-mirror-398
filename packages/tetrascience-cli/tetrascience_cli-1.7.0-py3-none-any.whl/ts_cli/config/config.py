from typing import List

from ts_cli.config.provider import Provider
from ts_cli.errors.critical_error import CriticalError
from ts_cli.util.emit import emit_info, emit_success


class Config:
    """
    Abstract Config class
    """

    _type: str
    _provider: "Provider"

    def get(self, key: str):
        return self._provider.get(key)

    def get_pretty(self, key: str):
        return self.get(key)

    @staticmethod
    def _print_config_key(config: "Config", key: str):
        value = config.get_pretty(key)
        if value is not None:
            emit_success(f"{key}: '{value}'")
        else:
            emit_info(f"{key}: <unset>")

    @staticmethod
    def _print_config_keys(config: "Config", keys: List[str], config_type: str):
        if len(keys) > 0:
            print(f"Using the following {config_type} configuration:")
            for key in keys:
                Config._print_config_key(config, key)

    @staticmethod
    def _validate_config_keys(config: "Config", keys: List[str], config_type: str):
        valid = True
        for key in keys:
            valid &= config.get_pretty(key) is not None
        if not valid:
            raise CriticalError(
                f"Exiting due to incomplete {config_type} configuration"
            )

    def validate(self, requirements: List[str]):
        Config._validate_config_keys(self, requirements, self._type)
