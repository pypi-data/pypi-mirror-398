"""sleap-share: Python client for SLEAP Share.

Upload and share SLEAP datasets with slp.sh.

Example:
    >>> import sleap_share
    >>> result = sleap_share.upload("labels.slp")
    >>> print(result.share_url)
    https://slp.sh/aBcDeF

    >>> sleap_share.download("aBcDeF", output="./")

    >>> client = sleap_share.Client()
    >>> files = client.list_files()
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .client import SleapShareClient
from .config import Environment
from .exceptions import (
    AuthenticationError,
    DownloadError,
    NetworkError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    SleapShareError,
    UploadError,
    ValidationError,
)
from .models import FileInfo, Metadata, UploadResult, URLs, User

if TYPE_CHECKING:
    from .client import ProgressCallback

__version__ = "0.1.2"

# Convenience alias
Client = SleapShareClient

__all__ = [
    # Version
    "__version__",
    # Main client
    "Client",
    "SleapShareClient",
    # Models
    "FileInfo",
    "Metadata",
    "UploadResult",
    "URLs",
    "User",
    # Exceptions
    "SleapShareError",
    "AuthenticationError",
    "DownloadError",
    "NetworkError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
    "UploadError",
    "ValidationError",
    # Module-level functions
    "upload",
    "download",
    "get_info",
    "get_metadata",
    "get_preview",
    "get_preview_url",
    "get_download_url",
    "get_urls",
    "open",
]


# Module-level convenience functions
# These create a temporary client for single operations


def upload(
    file_path: str | Path,
    *,
    permanent: bool = False,
    progress_callback: ProgressCallback | None = None,
    env: Environment | None = None,
) -> UploadResult:
    """Upload a .slp file to SLEAP Share.

    Args:
        file_path: Path to the .slp file to upload.
        permanent: Request permanent storage (requires superuser).
        progress_callback: Optional callback for upload progress.
            Called with (bytes_sent, total_bytes).
        env: Target environment ("production" or "staging").

    Returns:
        UploadResult with shortcode, URLs, and metadata.

    Example:
        >>> result = sleap_share.upload("labels.slp")
        >>> print(result.share_url)
        https://slp.sh/aBcDeF
    """
    with SleapShareClient(env=env) as client:
        return client.upload(
            file_path, permanent=permanent, progress_callback=progress_callback
        )


def download(
    shortcode_or_url: str,
    *,
    output: str | Path | None = None,
    progress_callback: ProgressCallback | None = None,
    env: Environment | None = None,
) -> Path:
    """Download a file from SLEAP Share.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        output: Output path. Can be a directory or file path.
        progress_callback: Optional callback for download progress.
        env: Target environment ("production" or "staging").

    Returns:
        Path to the downloaded file.

    Example:
        >>> sleap_share.download("aBcDeF", output="./data/")
    """
    with SleapShareClient(env=env) as client:
        return client.download(
            shortcode_or_url, output=output, progress_callback=progress_callback
        )


def get_info(
    shortcode_or_url: str,
    *,
    env: Environment | None = None,
) -> FileInfo:
    """Get basic file information.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        env: Target environment ("production" or "staging").

    Returns:
        FileInfo with basic file details.

    Example:
        >>> info = sleap_share.get_info("aBcDeF")
        >>> print(info.filename, info.file_size)
    """
    with SleapShareClient(env=env) as client:
        return client.get_info(shortcode_or_url)


def get_metadata(
    shortcode_or_url: str,
    *,
    env: Environment | None = None,
) -> Metadata:
    """Get full metadata for a file.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        env: Target environment ("production" or "staging").

    Returns:
        Metadata with all available fields including SLP statistics.

    Example:
        >>> metadata = sleap_share.get_metadata("aBcDeF")
        >>> print(metadata.labeled_frames_count)
    """
    with SleapShareClient(env=env) as client:
        return client.get_metadata(shortcode_or_url)


def get_preview(
    shortcode_or_url: str,
    *,
    output: str | Path | None = None,
    env: Environment | None = None,
) -> bytes | Path:
    """Get preview image for a file.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        output: Optional path to save the image to.
        env: Target environment ("production" or "staging").

    Returns:
        Image bytes if output is None, otherwise path to saved file.

    Example:
        >>> preview_bytes = sleap_share.get_preview("aBcDeF")
        >>> sleap_share.get_preview("aBcDeF", output="preview.png")
    """
    with SleapShareClient(env=env) as client:
        return client.get_preview(shortcode_or_url, output=output)


def get_preview_url(
    shortcode_or_url: str,
    *,
    env: Environment | None = None,
) -> str:
    """Get the preview image URL for a file.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        env: Target environment ("production" or "staging").

    Returns:
        Preview image URL.

    Example:
        >>> url = sleap_share.get_preview_url("aBcDeF")
        >>> print(url)
        https://slp.sh/aBcDeF/preview.png
    """
    with SleapShareClient(env=env) as client:
        return client.get_preview_url(shortcode_or_url)


def get_download_url(
    shortcode_or_url: str,
    *,
    env: Environment | None = None,
) -> str:
    """Get the direct download URL for a file.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        env: Target environment ("production" or "staging").

    Returns:
        Direct download URL with HTTP range request support.

    Example:
        >>> url = sleap_share.get_download_url("aBcDeF")
        >>> print(url)
        https://slp.sh/aBcDeF/labels.slp
    """
    with SleapShareClient(env=env) as client:
        return client.get_download_url(shortcode_or_url)


def get_urls(
    shortcode_or_url: str,
    *,
    env: Environment | None = None,
) -> URLs:
    """Get all URLs for a shortcode.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        env: Target environment ("production" or "staging").

    Returns:
        URLs object with share, download, metadata, and preview URLs.

    Example:
        >>> urls = sleap_share.get_urls("aBcDeF")
        >>> print(urls.share_url)
        https://slp.sh/aBcDeF
    """
    with SleapShareClient(env=env) as client:
        return client.get_urls(shortcode_or_url)


def open(
    shortcode_or_url: str,
    *,
    env: Environment | None = None,
) -> str:
    """Get a URL suitable for lazy loading / virtual file access.

    This returns the download URL which supports HTTP range requests,
    allowing HDF5 clients (h5py ros3, fsspec, sleap-io) to stream bytes
    on-demand without downloading the entire file.

    Args:
        shortcode_or_url: Shortcode or full URL of the file.
        env: Target environment ("production" or "staging").

    Returns:
        URL for lazy loading with HTTP range request support.

    Example:
        >>> import sleap_io
        >>> labels = sleap_io.load_slp(sleap_share.open("aBcDeF"))
        >>> print(labels.skeletons)  # Only fetches skeleton data
    """
    with SleapShareClient(env=env) as client:
        return client.open(shortcode_or_url)
