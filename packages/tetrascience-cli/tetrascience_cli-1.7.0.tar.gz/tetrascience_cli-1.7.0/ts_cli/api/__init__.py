import re
from io import BytesIO
from typing import Optional, Tuple

import httpx
import requests
from tqdm import tqdm

from ts_cli.config.api_config import ApiConfig
from ts_cli.config.publish_artifact_config import PublishArtifactConfig
from ts_cli.config.update_artifact_config import UpdateArtifactConfig
from ts_cli.errors.critical_error import CriticalError
from ts_cli.util.emit import emit_error, emit_info

REQUEST_TIMEOUT_SECONDS = 60
DEFAULT_CHUNK_SIZE = 8192


class ProgressTracker:
    """
    A wrapper around bytes content that tracks upload progress
    """

    def __init__(self, content: bytes, description: str = "Uploading"):
        self.content = content
        self.total_size = len(content)
        self.description = description
        self.progress_bar = None
        self.bytes_read = 0
        self._stream = None
        self._progress_bar_closed = False

    def __len__(self):
        return self.total_size

    def _ensure_progress_bar(self):
        """Initialize progress bar if not already created."""
        if self.progress_bar is None:
            self.progress_bar = tqdm(
                total=self.total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=self.description,
                leave=True,
            )

    def __iter__(self):
        """Iterator interface for streaming."""
        self.bytes_read = 0
        self._progress_bar_closed = False

        self.progress_bar = tqdm(
            total=self.total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=self.description,
            leave=True,
        )

        stream = BytesIO(self.content)
        while True:
            chunk = stream.read(DEFAULT_CHUNK_SIZE)
            if not chunk:
                break

            self.bytes_read += len(chunk)
            self.progress_bar.update(len(chunk))
            yield chunk

        self._close_progress_bar_if_not_closed()

    def read(self, size=-1):
        """Read method for file-like interface."""
        if self._stream is None:
            self._stream = BytesIO(self.content)
            self._ensure_progress_bar()

        if size == -1:
            # Read all remaining data
            chunk = self._stream.read()
            if chunk:
                self.bytes_read += len(chunk)
                self.progress_bar.update(len(chunk))
            self._close_progress_bar_if_complete()
            return chunk
        else:
            # Read specified amount
            chunk = self._stream.read(size)
            if chunk:
                self.bytes_read += len(chunk)
                self.progress_bar.update(len(chunk))
            self._close_progress_bar_if_complete()
            return chunk

    def _close_progress_bar_if_complete(self):
        """Close progress bar if all data has been read and bar hasn't been closed yet."""
        if self.bytes_read >= self.total_size:
            self._close_progress_bar_if_not_closed()

    def _close_progress_bar_if_not_closed(self):
        """Close progress bar if it exists and hasn't been closed yet."""
        if self.progress_bar and not self._progress_bar_closed:
            self.progress_bar.close()
            self._progress_bar_closed = True


class TsApiError(Exception):
    """
    For TsApi Failures
    """


class TsApi:
    """
    A simple adapter for the Tetrascience public api
    At the moment, only artifact endpoints are supported
    """

    def __init__(self, config: ApiConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose

    @property
    def _api_url(self):
        return self.config.api_url

    @property
    def _request_defaults(self):
        return {
            "verify": self.config.ignore_ssl is not True,
            "headers": self._get_headers(),
        }

    def _get_headers(self):
        headers = {"x-org-slug": self.config.org}
        ts_auth = self.config.auth_token
        if re.compile(r"^([a-z0-9]+-)+[a-z0-9]+$").match(ts_auth, re.IGNORECASE):
            headers["x-api-key"] = ts_auth
        else:
            headers["ts-auth-token"] = ts_auth
        return headers

    def _log_request(self, method: str, url: str, headers: dict, params: dict = None):
        """Log HTTP request details when verbose mode is enabled"""
        if self.verbose:
            emit_info(f"HTTP Request: {method} {url}")
            if params:
                emit_info(f"Request params: {params}")
            emit_info(f"Request headers: {headers}")

    def _log_response(self, response):
        """Log HTTP response details when verbose mode is enabled"""
        if self.verbose:
            emit_info(f"HTTP Response: {response.status_code}")
            emit_info(f"Response headers: {dict(response.headers)}")
            if hasattr(response, "text"):
                emit_info(f"Response body: {response.text}")

    def _api_error(self, response, operation_context=None):
        """
        Enhanced error handling with verbose logging and timeout detection

        :param response: HTTP response object
        :param operation_context: Context about the operation (e.g., "upload", "delete", "get")
        """
        # Always show debug info in verbose mode first
        if self.verbose:
            emit_error(f"DEBUG: HTTP Status: {response.status_code}")
            emit_error(f"DEBUG: Response headers: {dict(response.headers)}")
            emit_error(f"DEBUG: Response text: {response.text}")

        try:
            body = response.json()
            message = body.get("message", "Unknown")
        except (ValueError, TypeError):
            # Handle non-JSON responses
            body = {}
            message = response.text if hasattr(response, "text") else "Unknown error"

        # Platform limitation (<TDP 4.4.0): Generic "Bad Request" responses often mask timeout errors
        # This is a known issue where the backend wraps timeout/connection errors
        # ONLY apply timeout detection for upload operations to avoid false positives
        is_masked_timeout = False
        if response.status_code == 400 and operation_context == "upload":
            # Check if this looks like a masked timeout error
            is_generic_bad_request = (
                message == "Bad Request"
                and body.get("error") == "Bad Request"
                and body.get("statusCode") == 400
            )

            # Treat generic bad requests as likely timeout errors during uploads
            if is_generic_bad_request:
                is_masked_timeout = True
                if self.verbose:
                    emit_error("DEBUG: Detected likely timeout error")

        if is_masked_timeout:
            emit_error("Response from platform: Upload timeout or connection error")
            emit_error("This typically occurs when:")
            emit_error("  • Large files take longer than the server timeout limit")
            emit_error("  • Network connectivity issues during upload")
            emit_error("  • Server-side processing timeout")
            emit_error("Suggestions:")
            emit_error("  • Try uploading smaller files or splitting large uploads")
            emit_error("  • Check your network connection stability")
            emit_error("  • Retry the upload after a few minutes")
            if self.verbose:
                emit_error(f"Detailed error: {message}")
                emit_error(f"HTTP Status: {response.status_code}")
                emit_error(f"Response body: {response.text}")
        else:
            emit_error(f"Response from platform: {message}")
            if self.verbose:
                emit_error(f"HTTP Status: {response.status_code}")
                emit_error(f"URL: {response.url}")
                emit_error(f"Response headers: {dict(response.headers)}")
                emit_error(f"Full response body: {response.text}")

        raise CriticalError("Exiting")

    def artifact_url(self, config: UpdateArtifactConfig) -> str:
        type_to_url = {
            "connector": "connectors",
            "data-app": "connectors",
            "ids": "ids",
            "protocol": "master-scripts",
            "task-script": "task-scripts",
            "tetraflow": "tetraflows",
            "schema": "schemas",
        }
        return f"{self._api_url}/artifact/{type_to_url[config.type]}/{config.namespace}/{config.slug}/{config.version}"

    def upload_artifact(self, config: PublishArtifactConfig, artifact_bytes):
        """
        :param config: Artifact configuration
        :param artifact_bytes: ZIP file bytes
        :return: API response body
        """
        params = {"force": "true"} if config.force else {}
        request_defaults = self._request_defaults

        progress_tracker = ProgressTracker(
            artifact_bytes, description=f"Uploading {config.type} artifact"
        )

        url = self.artifact_url(config)
        self._log_request("POST", url, request_defaults["headers"], params)

        with httpx.Client(verify=request_defaults["verify"], timeout=600) as client:
            response = client.post(
                url,
                headers=request_defaults["headers"],
                params=params,
                content=progress_tracker,
            )

        self._log_response(response)

        if response.status_code < 400:
            return response.json()
        self._api_error(response, operation_context="upload")

    def delete_artifact(self, config: UpdateArtifactConfig):
        """
        :param config:
        :return: API response body
        """
        response = requests.delete(
            self.artifact_url(config),
            **self._request_defaults,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code < 400:
            return response.json()
        self._api_error(response)

    def get_task_script_build_info(self, task_id: str):
        """
        :param task_id: ID of the task build information to retrieve
        :return: API response body
        """
        url = f"{self._api_url}/artifact/builds/{task_id}"
        response = requests.get(
            url, **self._request_defaults, timeout=REQUEST_TIMEOUT_SECONDS
        )
        if response.status_code < 400:
            return response.json()
        self._api_error(response)

    def get_task_script_build_logs(self, task_id: str, next_token: Optional[str]):
        """
        :param task_id:
        :param next_token:
        :return:
        """
        url = f"{self._api_url}/artifact/build-logs/{task_id}"
        response = requests.get(
            url,
            **self._request_defaults,
            params={"nextToken": next_token} if next_token is not None else {},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code < 400:
            payload = response.json()
            events = payload.get("events", [])
            next_token = payload.get("nextToken", None)
            return events, next_token
        self._api_error(response)

    def get_pipelines_with_artifact(
        self,
        *,
        namespace: str,
        slug: str,
        version: str,
        artifact_type: str,
        page: Optional[int] = None,
    ) -> Tuple[list[dict], Optional[int]]:
        """
        :param page:
        :param namespace:
        :param slug:
        :param version:
        :param artifact_type:
        :return:
        """
        response = requests.get(
            f"{self._api_url}/pipeline/search",
            **self._request_defaults,
            params={
                "protocolNamespace": namespace,
                "protocolName": slug,
                "protocolVersion": version,
                "artifactType": artifact_type,
                **({"from": page} if page is not None else {}),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code < 400:
            payload = response.json()
            hits = payload.get("hits", [])
            next_page = (
                payload.get("from", None) if payload.get("hasNext", False) else None
            )
            return hits, next_page
        self._api_error(response)

    def get_protocols_with_task_script(
        self, *, namespace: str, slug: str, version: str
    ) -> list[dict]:
        """
        :param namespace:
        :param slug:
        :param version:
        :return:
        """
        return self.get_directional_relationships(
            artifact_type="task-scripts",
            namespace=namespace,
            slug=slug,
            version=version,
            other_type="protocols",
        )

    def get_task_scripts_with_ids(
        self, *, namespace: str, slug: str, version: str
    ) -> list[dict]:
        return self.get_directional_relationships(
            artifact_type="ids",
            namespace=namespace,
            slug=slug,
            version=version,
            other_type="task-scripts",
        )

    def get_directional_relationships(
        self,
        *,
        namespace: str,
        slug: str,
        version: str,
        artifact_type: str,
        other_type: str,
    ) -> list[dict]:
        response = requests.get(
            f"{self._api_url}/artifacts/{artifact_type}/{namespace}/{slug}/{version}/relationships",
            **self._request_defaults,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code < 400:
            payload = response.json()
            return payload.get(other_type, [])
        self._api_error(response)

    def get_data_apps(
        self, *, limit: int = 100, page: int = 1
    ) -> Tuple[list[dict], Optional[int]]:
        """
        Get data apps from the /dataapps/apps endpoint

        :param limit: Maximum number of results per page
        :param page: Page number
        :return: Tuple of (data_apps_list, next_page_number_or_none)
        """
        response = requests.get(
            f"{self._api_url}/dataapps/apps",
            **self._request_defaults,
            params={
                "limit": limit,
                "page": page,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code < 400:
            payload = response.json()
            data_apps = payload.get("dataApps", [])
            # Filter to only CONTAINER type data apps
            container_apps = [
                app for app in data_apps if app.get("type") == "CONTAINER"
            ]

            total = payload.get("count", 0)
            current_page_size = len(data_apps)
            next_page = (
                page + 1
                if (page + 1) * limit < total and current_page_size == limit
                else None
            )

            return container_apps, next_page
        self._api_error(response)
