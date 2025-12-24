"""Data models for sleap-share client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def _parse_datetime(value: str | int | datetime | None) -> datetime | None:
    """Parse a datetime from ISO format string, Unix timestamp, or return as-is."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Handle Unix timestamp in milliseconds
    if isinstance(value, int):
        try:
            return datetime.fromtimestamp(value / 1000)
        except (ValueError, OSError):
            return None
    # Handle ISO format with or without timezone
    try:
        # Try with timezone (Z suffix)
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@dataclass
class URLs:
    """All URLs for a shortcode.

    Attributes:
        share_url: Landing page URL (https://slp.sh/{shortcode}).
        download_url: Direct file download URL (https://slp.sh/{shortcode}/labels.slp).
        metadata_url: Metadata JSON URL (https://slp.sh/{shortcode}/metadata.json).
        preview_url: Preview image URL (https://slp.sh/{shortcode}/preview.png).
    """

    share_url: str
    download_url: str
    metadata_url: str
    preview_url: str

    @classmethod
    def from_shortcode(cls, shortcode: str, base_url: str = "https://slp.sh") -> URLs:
        """Create URLs from a shortcode.

        Args:
            shortcode: The file shortcode.
            base_url: Base URL for the environment.

        Returns:
            URLs object with all URLs populated.
        """
        base = base_url.rstrip("/")
        return cls(
            share_url=f"{base}/{shortcode}",
            download_url=f"{base}/{shortcode}/labels.slp",
            metadata_url=f"{base}/{shortcode}/metadata.json",
            preview_url=f"{base}/{shortcode}/preview.png",
        )


@dataclass
class UploadResult:
    """Result of a successful file upload.

    Attributes:
        shortcode: The unique shortcode for the file.
        share_url: The shareable URL for the file.
        data_url: Direct download URL for the file.
        expires_at: When the file will expire (None if permanent).
        is_permanent: Whether the file is permanently stored.
        validation_status: Status of file validation ("valid", "invalid", "pending").
        metadata: Optional metadata extracted from the file.
    """

    shortcode: str
    share_url: str
    data_url: str
    expires_at: datetime | None
    is_permanent: bool
    validation_status: str
    metadata: Metadata | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any], base_url: str) -> UploadResult:
        """Create from API response data.

        Args:
            data: Response data from /api/upload/complete endpoint.
            base_url: Base URL for the environment.

        Returns:
            UploadResult object.
        """
        # Extract shortcode from shareUrl (API returns camelCase)
        share_url = data.get("shareUrl", "")
        shortcode = share_url.rstrip("/").split("/")[-1] if share_url else ""

        metadata = None
        if "metadata" in data and data["metadata"]:
            # Map camelCase API response to snake_case for Metadata
            meta_data = data["metadata"]
            mapped_metadata = {
                "labeled_frames_count": meta_data.get("labeledFramesCount"),
                "user_instances_count": meta_data.get("userInstancesCount"),
                "predicted_instances_count": meta_data.get("predictedInstancesCount"),
                "tracks_count": meta_data.get("tracksCount"),
                "videos_count": meta_data.get("videosCount"),
            }
            metadata = Metadata.from_dict(mapped_metadata)

        return cls(
            shortcode=shortcode,
            share_url=share_url,
            data_url=data.get("dataUrl", f"{base_url}/{shortcode}/labels.slp"),
            expires_at=_parse_datetime(data.get("expiresAt")),
            is_permanent=data.get("isPermanent", False),
            validation_status=data.get("validationStatus", "unknown"),
            metadata=metadata,
        )


@dataclass
class FileInfo:
    """Basic information about an uploaded file.

    Attributes:
        shortcode: The unique shortcode for the file.
        filename: Original filename.
        file_size: File size in bytes.
        created_at: When the file was uploaded.
        expires_at: When the file will expire (None if permanent).
        share_url: The shareable URL for the file.
        data_url: Direct download URL for the file.
    """

    shortcode: str
    filename: str
    file_size: int
    created_at: datetime
    expires_at: datetime | None
    share_url: str
    data_url: str

    @classmethod
    def from_api_response(cls, data: dict[str, Any], base_url: str) -> FileInfo:
        """Create from API response data.

        Args:
            data: Response data from file listing API.
            base_url: Base URL for the environment.

        Returns:
            FileInfo object.
        """
        shortcode = data["shortcode"]
        urls = URLs.from_shortcode(shortcode, base_url)

        created_at = _parse_datetime(data.get("created_at"))
        if created_at is None:
            created_at = datetime.now()

        return cls(
            shortcode=shortcode,
            filename=data.get("filename", data.get("original_filename", "unknown")),
            file_size=data.get("file_size", 0),
            created_at=created_at,
            expires_at=_parse_datetime(data.get("expires_at")),
            share_url=urls.share_url,
            data_url=urls.download_url,
        )


@dataclass
class Metadata:
    """Full metadata from /{shortcode}/metadata.json.

    Attributes:
        shortcode: The unique shortcode for the file.
        original_filename: Original filename at upload.
        file_size: File size in bytes.
        upload_timestamp: When the file was uploaded.
        expires_at: When the file will expire (None if permanent).
        validation_status: Status of file validation.
        labeled_frames_count: Number of labeled frames (SLP-specific).
        user_instances_count: Number of user instances (SLP-specific).
        predicted_instances_count: Number of predicted instances (SLP-specific).
        tracks_count: Number of tracks (SLP-specific).
        videos_count: Number of videos (SLP-specific).
    """

    shortcode: str
    original_filename: str
    file_size: int
    upload_timestamp: datetime
    expires_at: datetime | None
    validation_status: str
    # SLP-specific stats (may be None if validation failed)
    labeled_frames_count: int | None = None
    user_instances_count: int | None = None
    predicted_instances_count: int | None = None
    tracks_count: int | None = None
    videos_count: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Metadata:
        """Create from metadata dictionary.

        Args:
            data: Metadata dictionary.

        Returns:
            Metadata object.
        """
        upload_timestamp = _parse_datetime(data.get("upload_timestamp"))
        if upload_timestamp is None:
            upload_timestamp = datetime.now()

        return cls(
            shortcode=data.get("shortcode", ""),
            original_filename=data.get("original_filename", "unknown"),
            file_size=data.get("file_size", 0),
            upload_timestamp=upload_timestamp,
            expires_at=_parse_datetime(data.get("expires_at")),
            validation_status=data.get("validation_status", "unknown"),
            labeled_frames_count=data.get("labeled_frames_count"),
            user_instances_count=data.get("user_instances_count"),
            predicted_instances_count=data.get("predicted_instances_count"),
            tracks_count=data.get("tracks_count"),
            videos_count=data.get("videos_count"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "shortcode": self.shortcode,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "upload_timestamp": self.upload_timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "validation_status": self.validation_status,
            "labeled_frames_count": self.labeled_frames_count,
            "user_instances_count": self.user_instances_count,
            "predicted_instances_count": self.predicted_instances_count,
            "tracks_count": self.tracks_count,
            "videos_count": self.videos_count,
        }


@dataclass
class User:
    """Authenticated user profile.

    Attributes:
        id: User ID.
        username: GitHub username.
        email: User email.
        avatar_url: URL to user's avatar image.
        total_files: Total number of files uploaded.
        total_storage: Total storage used in bytes.
    """

    id: int
    username: str
    email: str
    avatar_url: str
    total_files: int
    total_storage: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> User:
        """Create from API response data.

        Args:
            data: Response data from /api/v1/user/me endpoint.

        Returns:
            User object.
        """
        return cls(
            id=data.get("id", 0),
            username=data.get("username", ""),
            email=data.get("email", ""),
            avatar_url=data.get("avatar_url", ""),
            total_files=data.get("total_files", 0),
            total_storage=data.get("total_storage", 0),
        )
