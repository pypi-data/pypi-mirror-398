"""Tests for data models."""

from datetime import datetime

from sleap_share.models import FileInfo, Metadata, UploadResult, URLs, User


class TestURLs:
    """Tests for URLs dataclass."""

    def test_from_shortcode(self):
        """Test creating URLs from shortcode."""
        urls = URLs.from_shortcode("aBcDeF")

        assert urls.share_url == "https://slp.sh/aBcDeF"
        assert urls.download_url == "https://slp.sh/aBcDeF/labels.slp"
        assert urls.metadata_url == "https://slp.sh/aBcDeF/metadata.json"
        assert urls.preview_url == "https://slp.sh/aBcDeF/preview.png"

    def test_from_shortcode_custom_base(self):
        """Test creating URLs with custom base URL."""
        urls = URLs.from_shortcode("aBcDeF", "https://staging.slp.sh")

        assert urls.share_url == "https://staging.slp.sh/aBcDeF"
        assert urls.download_url == "https://staging.slp.sh/aBcDeF/labels.slp"

    def test_from_shortcode_strips_trailing_slash(self):
        """Test that trailing slashes are stripped from base URL."""
        urls = URLs.from_shortcode("aBcDeF", "https://slp.sh/")

        assert urls.share_url == "https://slp.sh/aBcDeF"


class TestMetadata:
    """Tests for Metadata dataclass."""

    def test_from_dict(self, sample_metadata_dict):
        """Test creating Metadata from dictionary."""
        metadata = Metadata.from_dict(sample_metadata_dict)

        assert metadata.shortcode == "aBcDeF"
        assert metadata.original_filename == "test_labels.slp"
        assert metadata.file_size == 3000
        assert metadata.validation_status == "valid"
        assert metadata.labeled_frames_count == 100
        assert metadata.user_instances_count == 50
        assert metadata.predicted_instances_count == 200
        assert metadata.tracks_count == 5
        assert metadata.videos_count == 1

    def test_from_dict_missing_optional_fields(self):
        """Test that missing optional fields are None."""
        data = {
            "shortcode": "aBcDeF",
            "original_filename": "test.slp",
            "file_size": 1000,
            "upload_timestamp": datetime.now().isoformat(),
            "validation_status": "invalid",
        }
        metadata = Metadata.from_dict(data)

        assert metadata.labeled_frames_count is None
        assert metadata.videos_count is None

    def test_to_dict(self, sample_metadata_dict):
        """Test converting Metadata to dictionary."""
        metadata = Metadata.from_dict(sample_metadata_dict)
        result = metadata.to_dict()

        assert result["shortcode"] == "aBcDeF"
        assert result["original_filename"] == "test_labels.slp"
        assert "upload_timestamp" in result


class TestUploadResult:
    """Tests for UploadResult dataclass."""

    def test_from_api_response(self, sample_upload_complete_response):
        """Test creating UploadResult from API response."""
        result = UploadResult.from_api_response(
            sample_upload_complete_response, "https://slp.sh"
        )

        assert result.shortcode == "aBcDeF"
        assert result.share_url == "https://slp.sh/aBcDeF"
        assert result.data_url == "https://slp.sh/aBcDeF/labels.slp"
        assert result.is_permanent is False
        assert result.validation_status == "valid"
        assert result.metadata is not None
        assert result.metadata.labeled_frames_count == 100


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_from_api_response(self):
        """Test creating FileInfo from API response."""
        data = {
            "shortcode": "aBcDeF",
            "filename": "test.slp",
            "file_size": 1000,
            "created_at": datetime.now().isoformat() + "Z",
            "expires_at": datetime.now().isoformat() + "Z",
        }
        info = FileInfo.from_api_response(data, "https://slp.sh")

        assert info.shortcode == "aBcDeF"
        assert info.filename == "test.slp"
        assert info.file_size == 1000
        assert info.share_url == "https://slp.sh/aBcDeF"


class TestUser:
    """Tests for User dataclass."""

    def test_from_api_response(self, sample_user_response):
        """Test creating User from API response."""
        user = User.from_api_response(sample_user_response)

        assert user.id == 123
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.total_files == 10
        assert user.total_storage == 1024 * 1024 * 100
