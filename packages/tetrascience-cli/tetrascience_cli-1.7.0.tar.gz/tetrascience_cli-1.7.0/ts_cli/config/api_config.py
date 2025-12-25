from url_normalize import url_normalize

from ts_cli.config.cli_config import CliConfig
from ts_cli.errors.critical_error import CriticalError


class ApiConfig(CliConfig):
    """
    API configuration.
    Loads API configuration in the following order:
    1. Command line arguments
    2. Config file (from command line arguments)
    3. From the process's environment
    4. From the configuration in the user's home directory
    """

    def __init__(self, args):
        super().__init__(args)
        self._type = "API"
        self.org: str = self.get("org")
        self.auth_token: str = self.get("auth_token")
        self.ignore_ssl: str = self.get("ignore_ssl")
        self.keys = ["org", "api_url", "auth_token", "ignore_ssl"]
        self.api_url: str = self.normalize_api_url(self.get("api_url"))
        self._print_config_keys(self, self.keys, self._type)
        self.validate(self.keys)

    def normalize_api_url(self, url: str) -> str:
        if not url or not url.strip():
            raise CriticalError(f"Invalid API URL format: {url}")
        try:
            normalized_url = url_normalize(url, default_scheme="https")
            # Ensure the trailing slash is removed
            return normalized_url.rstrip("/")
        except Exception as e:
            raise CriticalError(f"Invalid API URL format: {url}") from e

    def get_pretty(self, key: str):
        if key == "api_url":
            # Return the normalized url instead of the original raw version
            return self.api_url
        return super().get_pretty(key)

    def to_dict(self) -> dict:
        return {
            key: self.api_url if key == "api_url" else self.get(key)
            for key in self.keys
        }
