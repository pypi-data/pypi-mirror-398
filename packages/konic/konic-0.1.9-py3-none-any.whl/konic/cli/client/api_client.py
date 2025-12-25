import functools
import hashlib
import json
import os
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, TypeVar

import httpx
from dotenv import load_dotenv
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from konic.cli.env_keys import KonicCLIEnvVars
from konic.common.errors import KonicEnvironmentError, KonicHTTPError

F = TypeVar("F", bound=Callable[..., Any])


def handle_http_errors[F: Callable[..., Any]](func: F) -> F:
    """
    Decorator to handle HTTP errors for API client methods.
    Converts httpx.HTTPStatusError into KonicHTTPError with detailed information.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        try:
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            try:
                error_detail = response.json().get("detail", str(e))
            except Exception:
                error_detail = response.text or str(e)

            raise KonicHTTPError(
                message=error_detail,
                status_code=response.status_code,
                endpoint=str(response.url),
                response_body=response.text[:500] if response.text else None,
            )

    return wrapper  # type: ignore


class KonicAPIClient:
    def __init__(self):
        load_dotenv()

        headers = {"Accept": "application/json", "User-Agent": "konic-cli/0.1.0"}

        self.BASE_URL = os.environ.get(KonicCLIEnvVars.KONIC_HOST.value, "")
        if self.BASE_URL is None or self.BASE_URL == "":
            raise KonicEnvironmentError(
                env_var=KonicCLIEnvVars.KONIC_HOST.value,
                suggestion=f"export {KonicCLIEnvVars.KONIC_HOST.value}=<host-url>",
            )

        self.APIKEY = None  # TODO: not-implemented yet

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=httpx.Timeout(600.0, connect=30.0),  # 10 min read, 30s connect
        )

    @handle_http_errors
    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform a GET request.

        Args:
            endpoint: The API endpoint to call
            params: Optional query parameters
            headers: Optional additional headers

        Returns:
            httpx.Response: The response object

        Raises:
            KonicHTTPError: If the request fails
        """
        return self.client.get(endpoint, params=params, headers=headers)

    @handle_http_errors
    def post(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform a POST request.

        Args:
            endpoint: The API endpoint to call
            json: Optional JSON body
            data: Optional form data
            headers: Optional additional headers

        Returns:
            httpx.Response: The response object

        Raises:
            KonicHTTPError: If the request fails
        """
        return self.client.post(endpoint, json=json, data=data, headers=headers)

    @handle_http_errors
    def put(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform a PUT request.

        Args:
            endpoint: The API endpoint to call
            json: Optional JSON body
            data: Optional form data
            headers: Optional additional headers

        Returns:
            httpx.Response: The response object

        Raises:
            KonicHTTPError: If the request fails
        """
        return self.client.put(endpoint, json=json, data=data, headers=headers)

    @handle_http_errors
    def patch(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform a PATCH request.

        Args:
            endpoint: The API endpoint to call
            json: Optional JSON body
            data: Optional form data
            headers: Optional additional headers

        Returns:
            httpx.Response: The response object

        Raises:
            KonicHTTPError: If the request fails
        """
        return self.client.patch(endpoint, json=json, data=data, headers=headers)

    @handle_http_errors
    def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Perform a DELETE request.

        Args:
            endpoint: The API endpoint to call
            params: Optional query parameters
            headers: Optional additional headers

        Returns:
            httpx.Response: The response object

        Raises:
            KonicHTTPError: If the request fails
        """
        return self.client.delete(endpoint, params=params, headers=headers)

    def get_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Perform a GET request and return JSON response.

        Args:
            endpoint: The API endpoint to call
            params: Optional query parameters
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        response = self.get(endpoint, params=params, headers=headers)
        return response.json()

    def post_json(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Perform a POST request and return JSON response.

        Args:
            endpoint: The API endpoint to call
            json: Optional JSON body
            data: Optional form data
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        response = self.post(endpoint, json=json, data=data, headers=headers)
        return response.json()

    def put_json(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Perform a PUT request and return JSON response.

        Args:
            endpoint: The API endpoint to call
            json: Optional JSON body
            data: Optional form data
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        response = self.put(endpoint, json=json, data=data, headers=headers)
        return response.json()

    def patch_json(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Perform a PATCH request and return JSON response.

        Args:
            endpoint: The API endpoint to call
            json: Optional JSON body
            data: Optional form data
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        response = self.patch(endpoint, json=json, data=data, headers=headers)
        return response.json()

    def delete_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Perform a DELETE request and return JSON response.

        Args:
            endpoint: The API endpoint to call
            params: Optional query parameters
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        response = self.delete(endpoint, params=params, headers=headers)
        return response.json()

    def stream_sse(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 300.0,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Stream Server-Sent Events from an endpoint.

        Args:
            endpoint: The API endpoint to stream from
            params: Optional query parameters
            headers: Optional additional headers
            timeout: Timeout in seconds (default: 300)

        Yields:
            dict: Parsed event data with 'event' and 'data' keys

        Raises:
            KonicHTTPError: If the request fails
        """
        stream_headers = {"Accept": "text/event-stream"}
        if headers:
            stream_headers.update(headers)

        with httpx.Client(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(timeout, connect=10.0),
        ) as stream_client:
            with stream_client.stream(
                "GET",
                endpoint,
                params=params,
                headers=stream_headers,
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    try:
                        error_detail = response.read().decode()
                    except Exception:
                        error_detail = str(response.status_code)

                    raise KonicHTTPError(
                        message=error_detail,
                        status_code=response.status_code,
                        endpoint=str(response.url),
                    )

                event_type = None
                for line in response.iter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str) if data_str else {}
                        except json.JSONDecodeError:
                            data = {"raw": data_str}

                        yield {"event": event_type or "message", "data": data}
                        event_type = None

    def close(self):
        """Close the HTTP client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def set_base_url(self, base_url: str) -> None:
        """
        Update the base URL for the client.

        Args:
            base_url: The new base URL to use for requests
        """
        self.BASE_URL = base_url
        headers = {"Accept": "application/json", "User-Agent": "konic-cli/0.1.0"}

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=httpx.Timeout(600.0, connect=30.0),  # 10 min read, 30s connect
        )

    @handle_http_errors
    def upload_file(
        self,
        endpoint: str,
        file_path: Path,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Upload a file via multipart/form-data POST request.

        Args:
            endpoint: The API endpoint to call
            file_path: Path to the file to upload
            headers: Optional additional headers

        Returns:
            httpx.Response: The response object

        Raises:
            KonicHTTPError: If the request fails
            FileNotFoundError: If the file does not exist
        """
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            return self.client.post(endpoint, files=files, headers=headers)

    def upload_file_json(
        self,
        endpoint: str,
        file_path: Path,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Upload a file and return JSON response.

        Args:
            endpoint: The API endpoint to call
            file_path: Path to the file to upload
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        response = self.upload_file(endpoint, file_path, headers=headers)
        return response.json()

    def download_file(
        self,
        endpoint: str,
        output_path: Path,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Path:
        """
        Download a file from the API and save it to disk.

        Args:
            endpoint: The API endpoint to call
            output_path: Path where the file should be saved
            params: Optional query parameters
            headers: Optional additional headers

        Returns:
            Path: The path to the downloaded file

        Raises:
            KonicHTTPError: If the request fails
        """
        with self.client.stream("GET", endpoint, params=params, headers=headers) as response:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                try:
                    error_detail = response.json().get("detail", str(response.status_code))
                except Exception:
                    error_detail = response.text or str(response.status_code)

                raise KonicHTTPError(
                    message=error_detail,
                    status_code=response.status_code,
                    endpoint=str(response.url),
                    response_body=response.text[:500] if response.text else None,
                )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        return output_path

    @handle_http_errors
    def upload_file_with_form_data(
        self,
        endpoint: str,
        file_path: Path,
        form_data: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Upload a file with additional form data via multipart/form-data POST.

        Args:
            endpoint: The API endpoint to call
            file_path: Path to the file to upload
            form_data: Additional form fields to include (e.g., name, version)
            headers: Optional additional headers

        Returns:
            httpx.Response: The response object

        Raises:
            KonicHTTPError: If the request fails
            FileNotFoundError: If the file does not exist
        """
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            return self.client.post(
                endpoint,
                files=files,
                data=form_data,
                headers=headers,
            )

    def upload_file_with_form_data_json(
        self,
        endpoint: str,
        file_path: Path,
        form_data: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Upload a file with form data and return JSON response.

        Args:
            endpoint: The API endpoint to call
            file_path: Path to the file to upload
            form_data: Additional form fields to include
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        response = self.upload_file_with_form_data(endpoint, file_path, form_data, headers=headers)
        return response.json()

    def upload_file_with_progress(
        self,
        endpoint: str,
        file_path: Path,
        form_data: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Upload a file with progress bar and return JSON response.

        Args:
            endpoint: The API endpoint to call
            file_path: Path to the file to upload
            form_data: Additional form fields to include
            headers: Optional additional headers

        Returns:
            Any: The parsed JSON response

        Raises:
            KonicHTTPError: If the request fails
        """
        file_size = file_path.stat().st_size

        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(f"Uploading {file_path.name}", total=file_size)

            with open(file_path, "rb") as f:
                content = f.read()
                progress.update(task, completed=file_size)

            files = {"file": (file_path.name, content, "application/octet-stream")}
            response = self.client.post(
                endpoint,
                files=files,
                data=form_data,
                headers=headers,
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                try:
                    error_detail = response.json().get("detail", str(response))
                except Exception:
                    error_detail = response.text or str(response.status_code)

                raise KonicHTTPError(
                    message=error_detail,
                    status_code=response.status_code,
                    endpoint=str(response.url),
                    response_body=response.text[:500] if response.text else None,
                )

        return response.json()

    def download_file_with_progress(
        self,
        url: str,
        output_path: Path,
        expected_size: int | None = None,
        expected_checksum: str | None = None,
        verify_checksum: bool = True,
    ) -> tuple[Path, str]:
        """
        Download a file from a URL with progress bar and optional checksum verification.

        Args:
            url: The full URL to download from (e.g., presigned S3 URL)
            output_path: Path where the file should be saved
            expected_size: Expected file size in bytes for progress bar
            expected_checksum: Expected SHA256 checksum for verification
            verify_checksum: Whether to verify the checksum after download

        Returns:
            tuple[Path, str]: The path to the downloaded file and its SHA256 checksum

        Raises:
            KonicHTTPError: If the request fails
            ValueError: If checksum verification fails
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sha256_hash = hashlib.sha256()

        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            with httpx.Client(timeout=httpx.Timeout(300.0, connect=10.0)) as download_client:
                with download_client.stream("GET", url) as response:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError:
                        raise KonicHTTPError(
                            message=f"Failed to download file: {response.status_code}",
                            status_code=response.status_code,
                            endpoint=url,
                        )

                    total_size = expected_size
                    if total_size is None:
                        content_length = response.headers.get("content-length")
                        if content_length:
                            total_size = int(content_length)

                    task = progress.add_task(
                        f"Downloading {output_path.name}",
                        total=total_size,
                    )

                    with open(output_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            sha256_hash.update(chunk)
                            progress.update(task, advance=len(chunk))

        actual_checksum = sha256_hash.hexdigest()

        if verify_checksum and expected_checksum:
            if actual_checksum != expected_checksum:
                output_path.unlink(missing_ok=True)
                raise ValueError(
                    f"Checksum verification failed!\n"
                    f"Expected: {expected_checksum}\n"
                    f"Actual:   {actual_checksum}"
                )

        return output_path, actual_checksum
