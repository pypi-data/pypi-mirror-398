"""Tests for the HTTP client."""

from pathlib import Path
from unittest.mock import patch

import pytest

from sleap_share.client import SleapShareClient, _extract_shortcode, _get_unique_path
from sleap_share.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestGetUniquePath:
    """Tests for unique path generation."""

    def test_returns_original_if_not_exists(self, tmp_path):
        """Test that original path is returned if file doesn't exist."""
        path = tmp_path / "labels.slp"
        assert _get_unique_path(path) == path

    def test_appends_1_if_exists(self, tmp_path):
        """Test that (1) is appended if file exists."""
        path = tmp_path / "labels.slp"
        path.touch()
        result = _get_unique_path(path)
        assert result == tmp_path / "labels (1).slp"

    def test_increments_counter(self, tmp_path):
        """Test that counter increments for multiple existing files."""
        path = tmp_path / "labels.slp"
        path.touch()
        (tmp_path / "labels (1).slp").touch()
        (tmp_path / "labels (2).slp").touch()
        result = _get_unique_path(path)
        assert result == tmp_path / "labels (3).slp"

    def test_preserves_extension(self, tmp_path):
        """Test that file extension is preserved."""
        path = tmp_path / "data.tar.gz"
        path.touch()
        result = _get_unique_path(path)
        # Note: .stem gives "data.tar", .suffix gives ".gz"
        assert result.name == "data.tar (1).gz"


class TestExtractShortcode:
    """Tests for shortcode extraction."""

    def test_shortcode_passthrough(self):
        """Test that bare shortcodes are returned as-is."""
        assert _extract_shortcode("aBcDeF") == "aBcDeF"

    def test_url_extraction(self):
        """Test extracting shortcode from URLs."""
        assert _extract_shortcode("https://slp.sh/aBcDeF") == "aBcDeF"
        assert _extract_shortcode("https://staging.slp.sh/aBcDeF") == "aBcDeF"
        assert _extract_shortcode("http://localhost:8787/aBcDeF") == "aBcDeF"

    def test_url_with_path(self):
        """Test extracting shortcode from URLs with paths."""
        assert _extract_shortcode("https://slp.sh/aBcDeF/labels.slp") == "aBcDeF"
        assert _extract_shortcode("https://slp.sh/aBcDeF/metadata.json") == "aBcDeF"

    def test_url_without_protocol(self):
        """Test extracting shortcode from URLs without http(s):// prefix."""
        assert _extract_shortcode("slp.sh/aBcDeF") == "aBcDeF"
        assert _extract_shortcode("staging.slp.sh/aBcDeF") == "aBcDeF"
        assert _extract_shortcode("slp.sh/aBcDeF/labels.slp") == "aBcDeF"


class TestSleapShareClient:
    """Tests for SleapShareClient class."""

    def test_init_no_token(self):
        """Test client initialization without token."""
        with patch("sleap_share.client.load_token", return_value=None):
            client = SleapShareClient()
            assert client.is_authenticated is False

    def test_init_with_token(self):
        """Test client initialization with explicit token."""
        client = SleapShareClient(token="test_token")
        assert client.is_authenticated is True

    def test_init_with_env(self):
        """Test client initialization with environment."""
        client = SleapShareClient(env="staging")
        assert client.config.env == "staging"
        assert "staging" in client.config.url

    def test_get_urls(self):
        """Test getting URLs for a shortcode."""
        client = SleapShareClient()
        urls = client.get_urls("aBcDeF")

        assert urls.share_url == "https://slp.sh/aBcDeF"
        assert urls.download_url == "https://slp.sh/aBcDeF/labels.slp"

    def test_get_download_url(self):
        """Test getting download URL."""
        client = SleapShareClient()
        url = client.get_download_url("aBcDeF")

        assert url == "https://slp.sh/aBcDeF/labels.slp"

    def test_open(self):
        """Test open() returns download URL."""
        client = SleapShareClient()
        url = client.open("aBcDeF")

        assert url == "https://slp.sh/aBcDeF/labels.slp"


class TestUploadValidation:
    """Tests for upload validation."""

    def test_upload_file_not_found(self, tmp_path: Path):
        """Test upload with non-existent file raises error."""
        client = SleapShareClient()
        non_existent = tmp_path / "does_not_exist.slp"

        with pytest.raises(FileNotFoundError):
            client.upload(non_existent)

    def test_upload_invalid_extension(self, tmp_path: Path):
        """Test upload with non-.slp file raises error."""
        client = SleapShareClient()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a slp file")

        with pytest.raises(ValidationError) as exc_info:
            client.upload(txt_file)

        assert "Only .slp files are supported" in str(exc_info.value)


class TestUpload:
    """Tests for file upload."""

    def test_upload_success(
        self,
        httpx_mock,
        temp_slp_file,
        sample_upload_init_response,
        sample_upload_complete_response,
    ):
        """Test successful file upload."""
        # Mock init endpoint
        httpx_mock.add_response(
            method="POST",
            url="https://slp.sh/api/upload/init",
            json=sample_upload_init_response,
        )

        # Mock presigned URL upload
        httpx_mock.add_response(
            method="PUT",
            url=sample_upload_init_response["uploadUrl"],
            status_code=200,
        )

        # Mock complete endpoint
        httpx_mock.add_response(
            method="POST",
            url="https://slp.sh/api/upload/complete",
            json=sample_upload_complete_response,
        )

        client = SleapShareClient()
        result = client.upload(temp_slp_file)

        assert result.shortcode == "aBcDeF"
        assert result.share_url == "https://slp.sh/aBcDeF"
        assert result.metadata is not None

    def test_upload_with_progress_callback(
        self,
        httpx_mock,
        temp_slp_file,
        sample_upload_init_response,
        sample_upload_complete_response,
    ):
        """Test upload with progress callback."""
        httpx_mock.add_response(
            method="POST",
            url="https://slp.sh/api/upload/init",
            json=sample_upload_init_response,
        )
        httpx_mock.add_response(
            method="PUT",
            url=sample_upload_init_response["uploadUrl"],
            status_code=200,
        )
        httpx_mock.add_response(
            method="POST",
            url="https://slp.sh/api/upload/complete",
            json=sample_upload_complete_response,
        )

        progress_calls = []

        def callback(sent: int, total: int) -> None:
            progress_calls.append((sent, total))

        client = SleapShareClient()
        client.upload(temp_slp_file, progress_callback=callback)

        assert len(progress_calls) > 0
        assert progress_calls[-1][0] == progress_calls[-1][1]  # Final call shows 100%


class TestDownload:
    """Tests for file download."""

    def test_download_success(self, httpx_mock, tmp_path, sample_metadata_response):
        """Test successful file download."""
        # Mock metadata API
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/api/metadata/aBcDeF",
            json=sample_metadata_response,
        )

        # Mock file download
        file_content = b"fake slp content" * 100
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/aBcDeF/labels.slp",
            content=file_content,
            headers={"Content-Length": str(len(file_content))},
        )

        client = SleapShareClient()
        output_path = client.download("aBcDeF", output=tmp_path)

        assert output_path.exists()
        assert output_path.read_bytes() == file_content

    def test_download_from_url(self, httpx_mock, tmp_path, sample_metadata_response):
        """Test download using full URL."""
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/api/metadata/aBcDeF",
            json=sample_metadata_response,
        )
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/aBcDeF/labels.slp",
            content=b"content",
            headers={"Content-Length": "7"},
        )

        client = SleapShareClient()
        # Use full URL instead of shortcode
        client.download("https://slp.sh/aBcDeF", output=tmp_path)


class TestMetadata:
    """Tests for metadata retrieval."""

    def test_get_metadata_success(self, httpx_mock, sample_metadata_response):
        """Test successful metadata retrieval."""
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/api/metadata/aBcDeF",
            json=sample_metadata_response,
        )

        client = SleapShareClient()
        metadata = client.get_metadata("aBcDeF")

        assert metadata.shortcode == "aBcDeF"
        assert metadata.original_filename == "test_labels.slp"
        assert metadata.labeled_frames_count == 100

    def test_get_metadata_not_found(self, httpx_mock):
        """Test metadata retrieval for non-existent file."""
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/api/metadata/aBcDeF",
            status_code=404,
            json={"error": "Not found"},
        )

        client = SleapShareClient()
        with pytest.raises(NotFoundError):
            client.get_metadata("aBcDeF")


class TestAuthenticated:
    """Tests for authenticated operations."""

    def test_whoami_not_authenticated(self):
        """Test whoami raises error when not authenticated."""
        with patch("sleap_share.client.load_token", return_value=None):
            client = SleapShareClient()

            with pytest.raises(AuthenticationError):
                client.whoami()

    def test_whoami_success(self, httpx_mock, sample_user_response):
        """Test successful whoami."""
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/api/v1/user/me",
            json=sample_user_response,
        )

        client = SleapShareClient(token="test_token")
        user = client.whoami()

        assert user.username == "testuser"
        assert user.total_files == 10

    def test_list_files_success(self, httpx_mock, sample_files_response):
        """Test successful file listing."""
        import re

        httpx_mock.add_response(
            method="GET",
            url=re.compile(r"https://slp\.sh/api/v1/user/files.*"),
            json=sample_files_response,
        )

        client = SleapShareClient(token="test_token")
        files = client.list_files()

        assert len(files) == 2
        assert files[0].shortcode == "aBcDeF"

    def test_delete_success(self, httpx_mock):
        """Test successful file deletion."""
        httpx_mock.add_response(
            method="DELETE",
            url="https://slp.sh/api/v1/files/aBcDeF",
            json={"success": True},
        )

        client = SleapShareClient(token="test_token")
        result = client.delete("aBcDeF")

        assert result is True


class TestErrorHandling:
    """Tests for error handling."""

    def test_rate_limit_error(self, httpx_mock, temp_slp_file):
        """Test rate limit error handling."""
        httpx_mock.add_response(
            method="POST",
            url="https://slp.sh/api/upload/init",
            status_code=429,
            json={"error": "Rate limit exceeded"},
            headers={"Retry-After": "60"},
        )

        client = SleapShareClient()
        with pytest.raises(RateLimitError) as exc_info:
            client.upload(temp_slp_file)

        assert exc_info.value.retry_after == 60

    def test_authentication_error(self, httpx_mock):
        """Test authentication error handling."""
        httpx_mock.add_response(
            method="GET",
            url="https://slp.sh/api/v1/user/me",
            status_code=401,
            json={"error": "Invalid token"},
        )

        client = SleapShareClient(token="invalid_token")
        with pytest.raises(AuthenticationError):
            client.whoami()
