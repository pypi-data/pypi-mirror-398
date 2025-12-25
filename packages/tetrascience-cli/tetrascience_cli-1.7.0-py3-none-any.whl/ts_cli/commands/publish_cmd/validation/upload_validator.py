import os

from ts_cli.errors.critical_error import CriticalError
from ts_cli.util.emit import emit_error

from .validator import Validator


def bytes_as_human_readable_string(num_bytes: float, decimals: int = 1) -> str:
    """Return the file size as a human-readable string."""
    for unit in ["", "Ki", "Mi", "Gi", "Ti"]:
        if abs(num_bytes) < 1024.0:
            return f"{round(num_bytes, ndigits=decimals):.{decimals}f} {unit}B"
        num_bytes /= 1024.0
    return f"{round(num_bytes, ndigits=decimals):.{decimals}f} YiB"


class UploadValidator(Validator):
    """
    Check whether given file(s) or other data may be uploaded to Tetra Data Platform.
    """

    def __init__(
        self,
        *,
        artifact_type: str,
        upload_content: bytes = None,
        exiting: bool = False,
    ) -> None:
        self.artifact_type = artifact_type
        self.upload_content = upload_content
        super().__init__(exiting=exiting)

    def validate(self) -> bool:
        if self.artifact_type == "connector" or self.artifact_type == "data-app":
            return True

        max_upload_size = 50 * 1024 * 1024
        file_size = len(self.upload_content)
        if file_size > max_upload_size:
            friendly_file_size = bytes_as_human_readable_string(file_size)
            friendly_max_file_size = bytes_as_human_readable_string(max_upload_size)
            friendly_excess = bytes_as_human_readable_string(
                file_size - max_upload_size
            )

            emit_error(
                f"File exceeded upload limit of ~{friendly_max_file_size} "
                + f"by ~{friendly_excess}. Actual file size: {friendly_file_size}"
            )

            if self._exiting:
                raise CriticalError("Exiting")
            return False
        return True
