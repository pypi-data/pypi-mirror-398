"""HTTP client for SLEAP Share API."""

import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, BinaryIO, Self

import httpx

from .auth import load_token
from .config import (
    ALLOWED_EXTENSIONS,
    DEFAULT_TIMEOUT,
    DOWNLOAD_CHUNK_SIZE,
    UPLOAD_TIMEOUT,
    get_config,
)
from .exceptions import (
    AuthenticationError,
    NetworkError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    SleapShareError,
    UploadError,
    ValidationError,
)
from .models import FileInfo, Metadata, UploadResult, URLs, User

# Type aliases for callbacks
ProgressCallback = Callable[[int, int], None]
StatusCallback = Callable[[str], None]


def _get_unique_path(path: Path) -> Path:
    """Get a unique file path by appending (1), (2), etc. if file exists.

    Args:
        path: The desired file path.

    Returns:
        A path that doesn't exist. If the original path doesn't exist,
        returns it unchanged. Otherwise returns path with (N) suffix.

    Example:
        >>> _get_unique_path(Path("labels.slp"))
        Path("labels.slp")  # if doesn't exist
        >>> _get_unique_path(Path("labels.slp"))
        Path("labels (1).slp")  # if labels.slp exists
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def _extract_shortcode(shortcode_or_url: str) -> str:
    """Extract shortcode from URL or return as-is.

    Args:
        shortcode_or_url: Either a shortcode or full URL.
            Supported formats:
            - aBcDeF (shortcode only)
            - https://slp.sh/aBcDeF
            - http://slp.sh/aBcDeF
            - slp.sh/aBcDeF (no protocol)
            - staging.slp.sh/aBcDeF

    Returns:
        The extracted shortcode.
    """
    # Match URLs with protocol: https://slp.sh/aBcDeF or https://staging.slp.sh/aBcDeF
    url_pattern = r"https?://[^/]+/([a-zA-Z0-9]+)(?:/.*)?$"
    match = re.match(url_pattern, shortcode_or_url)
    if match:
        return match.group(1)

    # Match URLs without protocol: slp.sh/aBcDeF or staging.slp.sh/aBcDeF
    no_protocol_pattern = r"^(?:[\w.-]+\.)?slp\.sh/([a-zA-Z0-9]+)(?:/.*)?$"
    match = re.match(no_protocol_pattern, shortcode_or_url)
    if match:
        return match.group(1)

    return shortcode_or_url


def _handle_response_error(response: httpx.Response) -> None:
    """Handle HTTP error responses by raising appropriate exceptions.

    Args:
        response: The HTTP response to check.

    Raises:
        Various SleapShareError subclasses based on status code.
    """
    if response.is_success:
        return

    status = response.status_code
    try:
        data = response.json()
        message = data.get("error", data.get("message", response.text))
    except Exception:
        message = response.text

    if status == 401:
        raise AuthenticationError(message)
    elif status == 403:
        raise PermissionError(message)
    elif status == 404:
        raise NotFoundError(message)
    elif status == 429:
        retry_after = response.headers.get("Retry-After")
        retry_seconds = int(retry_after) if retry_after else None
        raise RateLimitError(message, retry_after=retry_seconds)
    elif status == 400:
        raise ValidationError(message)
    else:
        raise SleapShareError(message, code="api_error", status_code=status)


class SleapShareClient:
    """Client for interacting with the SLEAP Share API.

    This client handles authentication, file uploads/downloads, and all
    API operations. It can be used directly or through the module-level
    convenience functions.

    Args:
        token: API token for authenticated operations. If not provided,
            attempts to load from storage.
        env: Target environment ("production" or "staging").
        base_url: Override base URL directly (ignores env).

    Example:
        >>> client = SleapShareClient()  # Uses stored token
        >>> result = client.upload("labels.slp")
        >>> print(result.share_url)
        https://slp.sh/aBcDeF

        >>> client = SleapShareClient(env="staging")
        >>> files = client.list_files()
    """

    def __init__(
        self,
        token: str | None = None,
        env: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.config = get_config(env=env, base_url=base_url)

        # Load token if not provided
        if token is None:
            token = load_token(self.config)
        self._token = token

        # Create HTTP client
        self._client = httpx.Client(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
        )

    @property
    def is_authenticated(self) -> bool:
        """Check if the client has a valid token."""
        return self._token is not None

    def _get_headers(self, authenticated: bool = False) -> dict[str, str]:
        """Get headers for API requests.

        Args:
            authenticated: Whether to include auth token.

        Returns:
            Headers dictionary.
        """
        headers = {"Content-Type": "application/json"}
        if authenticated and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def upload(
        self,
        file_path: str | Path,
        permanent: bool = False,
        progress_callback: ProgressCallback | None = None,
        status_callback: StatusCallback | None = None,
    ) -> UploadResult:
        """Upload a .slp file to SLEAP Share.

        Args:
            file_path: Path to the .slp file to upload.
            permanent: Request permanent storage (requires superuser).
            progress_callback: Optional callback for upload progress.
                Called with (bytes_sent, total_bytes).
            status_callback: Optional callback for status updates.
                Called with status strings: "uploading", "validating".

        Returns:
            UploadResult with shortcode, URLs, and metadata.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValidationError: If the file is not a .slp file.
            UploadError: If the upload fails.
        """
        path = Path(file_path)

        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Validate extension
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Only .slp files are supported. Got: {path.suffix}",
                code="invalid_file_type",
            )

        file_size = path.stat().st_size
        filename = path.name

        try:
            # Step 1: Initialize upload
            init_response = self._client.post(
                f"{self.config.url}/api/upload/init",
                json={
                    "filename": filename,
                    "fileSize": file_size,
                    "permanent": permanent,
                },
                headers=self._get_headers(authenticated=self.is_authenticated),
            )
            _handle_response_error(init_response)
            init_data = init_response.json()

            upload_url = init_data["uploadUrl"]
            shortcode = init_data["shortcode"]

            # Step 2: Upload file to presigned URL
            if status_callback:
                status_callback("uploading")

            # Use explicit timeout with long read timeout for R2 response
            upload_timeout = httpx.Timeout(
                connect=30.0,
                read=UPLOAD_TIMEOUT,
                write=UPLOAD_TIMEOUT,
                pool=30.0,
            )

            with open(path, "rb") as f:
                if progress_callback:
                    # Use iterator for progress tracking
                    upload_content: BinaryIO | _ProgressIterator = _ProgressIterator(
                        f, file_size, progress_callback
                    )
                else:
                    upload_content = f

                upload_response = self._client.put(
                    upload_url,
                    content=upload_content,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "Content-Length": str(file_size),
                    },
                    timeout=upload_timeout,
                )

            if not upload_response.is_success:
                raise UploadError(
                    f"Failed to upload file: {upload_response.text}",
                    status_code=upload_response.status_code,
                )

            # Step 3: Complete upload (may take time for metadata extraction)
            if status_callback:
                status_callback("validating")
            complete_response = self._client.post(
                f"{self.config.url}/api/upload/complete",
                json={"shortcode": shortcode},
                headers=self._get_headers(authenticated=self.is_authenticated),
                timeout=UPLOAD_TIMEOUT,  # Longer timeout for metadata extraction
            )
            _handle_response_error(complete_response)
            complete_data = complete_response.json()

            return UploadResult.from_api_response(complete_data, self.config.url)

        except httpx.RequestError as e:
            raise NetworkError(f"Network error during upload: {e}") from e

    def download(
        self,
        shortcode_or_url: str,
        output: str | Path | None = None,
        progress_callback: ProgressCallback | None = None,
        overwrite: bool | None = None,
    ) -> Path:
        """Download a file from SLEAP Share.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.
            output: Output path. Can be a directory or file path.
                If None, saves to current directory.
            progress_callback: Optional callback for download progress.
                Called with (bytes_received, total_bytes).
            overwrite: Whether to overwrite existing files.
                If None (default), overwrites when output is an explicit file path,
                but appends (1), (2), etc. when output is None or a directory.

        Returns:
            Path to the downloaded file.

        Raises:
            NotFoundError: If the file does not exist.
            DownloadError: If the download fails.
        """
        shortcode = _extract_shortcode(shortcode_or_url)
        download_url = f"{self.config.url}/{shortcode}/labels.slp"

        try:
            # Get file info for filename
            metadata = self.get_metadata(shortcode)
            filename = metadata.original_filename

            # Determine output path and whether to allow overwrite
            if output is None:
                output_path = Path.cwd() / filename
                # Default: don't overwrite when using auto filename
                should_overwrite = overwrite if overwrite is not None else False
            else:
                output_path = Path(output)
                if output_path.is_dir():
                    output_path = output_path / filename
                    # Default: don't overwrite when output is a directory
                    should_overwrite = overwrite if overwrite is not None else False
                else:
                    # Default: overwrite when explicit filename given
                    should_overwrite = overwrite if overwrite is not None else True

            # Avoid overwriting existing files (unless explicitly allowed)
            if not should_overwrite:
                output_path = _get_unique_path(output_path)

            # Stream download
            with self._client.stream("GET", download_url) as response:
                _handle_response_error(response)

                total_size = int(response.headers.get("Content-Length", 0))
                bytes_received = 0

                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=DOWNLOAD_CHUNK_SIZE):
                        f.write(chunk)
                        bytes_received += len(chunk)
                        if progress_callback:
                            progress_callback(bytes_received, total_size)

            return output_path

        except httpx.RequestError as e:
            raise NetworkError(f"Network error during download: {e}") from e

    def get_info(self, shortcode_or_url: str) -> FileInfo:
        """Get basic file information.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.

        Returns:
            FileInfo with basic file details.

        Raises:
            NotFoundError: If the file does not exist.
        """
        metadata = self.get_metadata(shortcode_or_url)
        shortcode = _extract_shortcode(shortcode_or_url)
        urls = URLs.from_shortcode(shortcode, self.config.url)

        return FileInfo(
            shortcode=shortcode,
            filename=metadata.original_filename,
            file_size=metadata.file_size,
            created_at=metadata.upload_timestamp,
            expires_at=metadata.expires_at,
            share_url=urls.share_url,
            data_url=urls.download_url,
        )

    def get_metadata(self, shortcode_or_url: str) -> Metadata:
        """Get full metadata for a file.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.

        Returns:
            Metadata with all available fields.

        Raises:
            NotFoundError: If the file does not exist.
        """
        shortcode = _extract_shortcode(shortcode_or_url)
        # Use the API endpoint which returns both file-level and SLP metadata
        metadata_url = f"{self.config.url}/api/metadata/{shortcode}"

        try:
            response = self._client.get(metadata_url)
            _handle_response_error(response)
            data = response.json()

            # Map API response (camelCase) to client model (snake_case)
            mapped_data: dict[str, Any] = {
                "shortcode": data.get("shortcode", shortcode),
                "original_filename": data.get("originalFilename", "unknown"),
                "file_size": data.get("fileSize", 0),
                "upload_timestamp": data.get("uploadedAt"),
                "expires_at": data.get("expiresAt"),
                "validation_status": data.get("validationStatus", "unknown"),
            }

            # Extract SLP-specific metadata if present
            slp_metadata = data.get("metadata", {})
            if slp_metadata:
                mapped_data["labeled_frames_count"] = slp_metadata.get(
                    "labeledFramesCount"
                )
                mapped_data["user_instances_count"] = slp_metadata.get(
                    "userInstancesCount"
                )
                mapped_data["predicted_instances_count"] = slp_metadata.get(
                    "predictedInstancesCount"
                )
                mapped_data["tracks_count"] = slp_metadata.get("tracksCount")
                mapped_data["videos_count"] = slp_metadata.get("videosCount")

            return Metadata.from_dict(mapped_data)

        except httpx.RequestError as e:
            raise NetworkError(f"Network error fetching metadata: {e}") from e

    def get_preview(
        self,
        shortcode_or_url: str,
        output: str | Path | None = None,
    ) -> bytes | Path:
        """Get preview image for a file.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.
            output: Optional path to save the image to.

        Returns:
            Image bytes if output is None, otherwise path to saved file.

        Raises:
            NotFoundError: If the file or preview does not exist.
        """
        shortcode = _extract_shortcode(shortcode_or_url)
        preview_url = f"{self.config.url}/{shortcode}/preview.png"

        try:
            response = self._client.get(preview_url)
            _handle_response_error(response)

            if output is None:
                return response.content

            output_path = Path(output)
            output_path.write_bytes(response.content)
            return output_path

        except httpx.RequestError as e:
            raise NetworkError(f"Network error fetching preview: {e}") from e

    def get_urls(self, shortcode_or_url: str) -> URLs:
        """Get all URLs for a shortcode.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.

        Returns:
            URLs object with share, download, metadata, and preview URLs.
        """
        shortcode = _extract_shortcode(shortcode_or_url)
        return URLs.from_shortcode(shortcode, self.config.url)

    def get_download_url(self, shortcode_or_url: str) -> str:
        """Get the direct download URL for a file.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.

        Returns:
            Direct download URL.
        """
        return self.get_urls(shortcode_or_url).download_url

    def get_preview_url(self, shortcode_or_url: str) -> str:
        """Get the preview image URL for a file.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.

        Returns:
            Preview image URL.
        """
        return self.get_urls(shortcode_or_url).preview_url

    def open(self, shortcode_or_url: str) -> str:
        """Get a URL suitable for lazy loading / virtual file access.

        This returns the download URL which supports HTTP range requests,
        allowing HDF5 clients (h5py ros3, fsspec) to stream bytes on-demand.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.

        Returns:
            URL for lazy loading with HTTP range request support.

        Example:
            >>> url = client.open("aBcDeF")
            >>> import sleap_io
            >>> labels = sleap_io.load_slp(url)  # Streams on-demand!
        """
        return self.get_download_url(shortcode_or_url)

    def whoami(self) -> User:
        """Get the current authenticated user's profile.

        Returns:
            User object with profile information.

        Raises:
            AuthenticationError: If not authenticated.
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated. Run 'sleap-share login' first."
            )

        try:
            response = self._client.get(
                f"{self.config.url}/api/v1/user/me",
                headers=self._get_headers(authenticated=True),
            )
            _handle_response_error(response)
            return User.from_api_response(response.json())

        except httpx.RequestError as e:
            raise NetworkError(f"Network error fetching user info: {e}") from e

    def list_files(self, limit: int = 50) -> list[FileInfo]:
        """List the authenticated user's uploaded files.

        Args:
            limit: Maximum number of files to return.

        Returns:
            List of FileInfo objects.

        Raises:
            AuthenticationError: If not authenticated.
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated. Run 'sleap-share login' first."
            )

        try:
            response = self._client.get(
                f"{self.config.url}/api/v1/user/files",
                params={"limit": limit},
                headers=self._get_headers(authenticated=True),
            )
            _handle_response_error(response)
            data = response.json()

            return [
                FileInfo.from_api_response(item, self.config.url)
                for item in data.get("files", [])
            ]

        except httpx.RequestError as e:
            raise NetworkError(f"Network error fetching files: {e}") from e

    def delete(self, shortcode_or_url: str) -> bool:
        """Delete a file owned by the authenticated user.

        Args:
            shortcode_or_url: Shortcode or full URL of the file.

        Returns:
            True if deletion was successful.

        Raises:
            AuthenticationError: If not authenticated.
            PermissionError: If the file is not owned by the user.
            NotFoundError: If the file does not exist.
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated. Run 'sleap-share login' first."
            )

        shortcode = _extract_shortcode(shortcode_or_url)

        try:
            response = self._client.delete(
                f"{self.config.url}/api/v1/files/{shortcode}",
                headers=self._get_headers(authenticated=True),
            )
            _handle_response_error(response)
            return True

        except httpx.RequestError as e:
            raise NetworkError(f"Network error deleting file: {e}") from e

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class _ProgressIterator:
    """Iterator that yields file chunks while reporting progress.

    This provides an iterator interface that httpx can use for streaming
    uploads while calling a callback to report progress.
    """

    def __init__(
        self,
        file: BinaryIO,
        total_size: int,
        callback: ProgressCallback,
        chunk_size: int = 64 * 1024,  # 64KB chunks
    ) -> None:
        self._file = file
        self._total_size = total_size
        self._callback = callback
        self._chunk_size = chunk_size
        self._bytes_read = 0

    def __iter__(self) -> Iterator[bytes]:
        """Iterate over file chunks."""
        return self

    def __next__(self) -> bytes:
        """Read next chunk and report progress."""
        chunk = self._file.read(self._chunk_size)
        if not chunk:
            raise StopIteration
        self._bytes_read += len(chunk)
        self._callback(self._bytes_read, self._total_size)
        return chunk

    def __len__(self) -> int:
        """Return the total size for httpx content-length detection."""
        return self._total_size
