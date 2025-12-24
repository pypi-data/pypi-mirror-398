"""Tests for the CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from sleap_share import __version__
from sleap_share.cli import app
from sleap_share.exceptions import AuthenticationError, NotFoundError, SleapShareError
from sleap_share.models import FileInfo, Metadata, UploadResult, URLs, User

runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version(self):
        """Test version command shows version."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert __version__ in result.output


class TestLoginCommand:
    """Tests for the login command."""

    def test_login_success(self):
        """Test successful login flow."""
        with patch("sleap_share.cli.run_device_auth_flow") as mock_auth:
            mock_auth.return_value = ("token123", "testuser")

            result = runner.invoke(app, ["login"])

            assert result.exit_code == 0
            mock_auth.assert_called_once()

    def test_login_error(self):
        """Test login with authentication error."""
        with patch("sleap_share.cli.run_device_auth_flow") as mock_auth:
            mock_auth.side_effect = AuthenticationError("Auth failed")

            result = runner.invoke(app, ["login"])

            assert result.exit_code == 1
            assert "Auth failed" in result.output

    def test_login_keyboard_interrupt(self):
        """Test login cancelled by user."""
        with patch("sleap_share.cli.run_device_auth_flow") as mock_auth:
            mock_auth.side_effect = KeyboardInterrupt()

            result = runner.invoke(app, ["login"])

            assert result.exit_code == 1
            assert "cancelled" in result.output.lower()


class TestLogoutCommand:
    """Tests for the logout command."""

    def test_logout_success(self):
        """Test successful logout."""
        with patch("sleap_share.cli.clear_token") as mock_clear:
            mock_clear.return_value = True

            result = runner.invoke(app, ["logout"])

            assert result.exit_code == 0
            assert "Logged out" in result.output

    def test_logout_no_credentials(self):
        """Test logout when no credentials exist."""
        with patch("sleap_share.cli.clear_token") as mock_clear:
            mock_clear.return_value = False

            result = runner.invoke(app, ["logout"])

            assert result.exit_code == 0
            assert "No credentials" in result.output


class TestWhoamiCommand:
    """Tests for the whoami command."""

    def test_whoami_not_logged_in(self):
        """Test whoami when not logged in."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = None

            result = runner.invoke(app, ["whoami"])

            assert result.exit_code == 1
            assert "Not logged in" in result.output

    def test_whoami_success(self):
        """Test successful whoami."""
        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            avatar_url="https://example.com/avatar.png",
            total_files=10,
            total_storage=1024 * 1024 * 50,  # 50 MB
        )

        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = "token123"

            with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.whoami.return_value = mock_user
                mock_client_cls.return_value = mock_client

                result = runner.invoke(app, ["whoami"])

                assert result.exit_code == 0
                assert "testuser" in result.output
                assert "test@example.com" in result.output
                assert "10" in result.output

    def test_whoami_error(self):
        """Test whoami with API error."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = "token123"

            with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.whoami.side_effect = SleapShareError("API error")
                mock_client_cls.return_value = mock_client

                result = runner.invoke(app, ["whoami"])

                assert result.exit_code == 1
                assert "API error" in result.output


class TestUploadCommand:
    """Tests for the upload command."""

    def test_upload_file_not_found(self, tmp_path: Path):
        """Test upload with non-existent file."""
        result = runner.invoke(app, ["upload", str(tmp_path / "nonexistent.slp")])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_upload_invalid_extension(self, tmp_path: Path):
        """Test upload with non-.slp file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a slp file")

        result = runner.invoke(app, ["upload", str(txt_file)])

        assert result.exit_code == 1
        assert ".slp" in result.output

    def test_upload_success(self, temp_slp_file: Path):
        """Test successful upload."""
        mock_result = UploadResult(
            shortcode="aBcDeF",
            share_url="https://slp.sh/aBcDeF",
            data_url="https://slp.sh/aBcDeF/labels.slp",
            expires_at=None,
            is_permanent=True,
            validation_status="valid",
            metadata=None,
        )

        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.upload.return_value = mock_result
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["upload", str(temp_slp_file)])

            assert result.exit_code == 0
            assert "Upload complete" in result.output
            assert "https://slp.sh/aBcDeF" in result.output

    def test_upload_with_metadata(self, temp_slp_file: Path):
        """Test upload that shows metadata."""
        mock_metadata = Metadata(
            shortcode="aBcDeF",
            original_filename="labels.slp",
            file_size=1000,
            upload_timestamp=None,
            expires_at=None,
            validation_status="valid",
            labeled_frames_count=100,
            user_instances_count=50,
            predicted_instances_count=200,
            tracks_count=5,
            videos_count=2,
        )

        mock_result = UploadResult(
            shortcode="aBcDeF",
            share_url="https://slp.sh/aBcDeF",
            data_url="https://slp.sh/aBcDeF/labels.slp",
            expires_at=None,
            is_permanent=True,
            validation_status="valid",
            metadata=mock_metadata,
        )

        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.upload.return_value = mock_result
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["upload", str(temp_slp_file)])

            assert result.exit_code == 0
            assert "100 labeled frames" in result.output
            assert "2 videos" in result.output

    def test_upload_error(self, temp_slp_file: Path):
        """Test upload with API error."""
        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.upload.side_effect = SleapShareError("Upload failed")
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["upload", str(temp_slp_file)])

            assert result.exit_code == 1
            assert "Upload failed" in result.output


class TestDownloadCommand:
    """Tests for the download command."""

    def test_download_success(self, tmp_path: Path):
        """Test successful download."""
        mock_info = FileInfo(
            shortcode="aBcDeF",
            filename="labels.slp",
            file_size=1000,
            created_at=None,
            expires_at=None,
            share_url="https://slp.sh/aBcDeF",
            data_url="https://slp.sh/aBcDeF/labels.slp",
        )

        output_file = tmp_path / "labels.slp"

        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_info.return_value = mock_info
            mock_client.download.return_value = output_file
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["download", "aBcDeF", "-o", str(tmp_path)])

            assert result.exit_code == 0
            assert "Downloaded" in result.output

    def test_download_not_found(self):
        """Test download with non-existent file."""
        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_info.side_effect = NotFoundError("Not found")
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["download", "aBcDeF"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()


class TestListCommand:
    """Tests for the list command."""

    def test_list_not_logged_in(self):
        """Test list when not logged in."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = None

            result = runner.invoke(app, ["list"])

            assert result.exit_code == 1
            assert "Not logged in" in result.output

    def test_list_no_files(self):
        """Test list with no files."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = "token123"

            with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.list_files.return_value = []
                mock_client_cls.return_value = mock_client

                result = runner.invoke(app, ["list"])

                assert result.exit_code == 0
                assert "No files" in result.output

    def test_list_success(self):
        """Test successful file listing."""
        mock_files = [
            FileInfo(
                shortcode="aBcDeF",
                filename="test1.slp",
                file_size=1000,
                created_at=None,
                expires_at=None,
                share_url="https://slp.sh/aBcDeF",
                data_url="https://slp.sh/aBcDeF/labels.slp",
            ),
            FileInfo(
                shortcode="gHiJkL",
                filename="test2.slp",
                file_size=2000,
                created_at=None,
                expires_at=None,
                share_url="https://slp.sh/gHiJkL",
                data_url="https://slp.sh/gHiJkL/labels.slp",
            ),
        ]

        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = "token123"

            with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.list_files.return_value = mock_files
                mock_client_cls.return_value = mock_client

                result = runner.invoke(app, ["list"])

                assert result.exit_code == 0
                assert "aBcDeF" in result.output
                assert "test1.slp" in result.output
                assert "gHiJkL" in result.output


class TestInfoCommand:
    """Tests for the info command."""

    def test_info_success(self):
        """Test successful info display."""
        mock_metadata = Metadata(
            shortcode="aBcDeF",
            original_filename="labels.slp",
            file_size=1000,
            upload_timestamp=None,
            expires_at=None,
            validation_status="valid",
            labeled_frames_count=100,
            user_instances_count=50,
            predicted_instances_count=None,
            tracks_count=None,
            videos_count=1,
        )

        mock_urls = URLs(
            share_url="https://slp.sh/aBcDeF",
            download_url="https://slp.sh/aBcDeF/labels.slp",
            metadata_url="https://slp.sh/aBcDeF/metadata.json",
            preview_url="https://slp.sh/aBcDeF/preview.png",
        )

        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_metadata.return_value = mock_metadata
            mock_client.get_urls.return_value = mock_urls
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["info", "aBcDeF"])

            assert result.exit_code == 0
            assert "aBcDeF" in result.output
            assert "labels.slp" in result.output
            assert "100" in result.output  # labeled_frames_count

    def test_info_json_output(self):
        """Test info with JSON output."""
        from datetime import datetime

        mock_metadata = Metadata(
            shortcode="aBcDeF",
            original_filename="labels.slp",
            file_size=1000,
            upload_timestamp=datetime.now(),
            expires_at=None,
            validation_status="valid",
            labeled_frames_count=100,
            user_instances_count=50,
            predicted_instances_count=None,
            tracks_count=None,
            videos_count=1,
        )

        mock_urls = URLs(
            share_url="https://slp.sh/aBcDeF",
            download_url="https://slp.sh/aBcDeF/labels.slp",
            metadata_url="https://slp.sh/aBcDeF/metadata.json",
            preview_url="https://slp.sh/aBcDeF/preview.png",
        )

        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_metadata.return_value = mock_metadata
            mock_client.get_urls.return_value = mock_urls
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["info", "aBcDeF", "--json"])

            assert result.exit_code == 0
            # Should be valid JSON
            data = json.loads(result.output)
            assert data["shortcode"] == "aBcDeF"

    def test_info_not_found(self):
        """Test info with non-existent file."""
        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_metadata.side_effect = NotFoundError("Not found")
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["info", "aBcDeF"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()


class TestPreviewCommand:
    """Tests for the preview command."""

    def test_preview_success(self, tmp_path: Path):
        """Test successful preview download."""
        output_file = tmp_path / "preview.png"

        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_preview.return_value = output_file
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["preview", "aBcDeF", "-o", str(output_file)])

            assert result.exit_code == 0
            assert "Preview saved" in result.output

    def test_preview_not_found(self):
        """Test preview with non-existent file."""
        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_preview.side_effect = NotFoundError("Not found")
            mock_client_cls.return_value = mock_client

            result = runner.invoke(app, ["preview", "aBcDeF"])

            assert result.exit_code == 1
            assert "not available" in result.output.lower()


class TestDeleteCommand:
    """Tests for the delete command."""

    def test_delete_not_logged_in(self):
        """Test delete when not logged in."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = None

            result = runner.invoke(app, ["delete", "aBcDeF"])

            assert result.exit_code == 1
            assert "Not logged in" in result.output

    def test_delete_cancelled(self):
        """Test delete cancelled by user."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = "token123"

            result = runner.invoke(app, ["delete", "aBcDeF"], input="n\n")

            assert result.exit_code == 0
            assert "Cancelled" in result.output

    def test_delete_success(self):
        """Test successful delete."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = "token123"

            with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.delete.return_value = True
                mock_client_cls.return_value = mock_client

                result = runner.invoke(app, ["delete", "aBcDeF", "--yes"])

                assert result.exit_code == 0
                assert "Deleted" in result.output

    def test_delete_not_found(self):
        """Test delete with non-existent file."""
        with patch("sleap_share.cli.load_token") as mock_load:
            mock_load.return_value = "token123"

            with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.delete.side_effect = NotFoundError("Not found")
                mock_client_cls.return_value = mock_client

                result = runner.invoke(app, ["delete", "aBcDeF", "--yes"])

                assert result.exit_code == 1
                assert "not found" in result.output.lower()


class TestEnvironmentFlag:
    """Tests for the --env flag across commands."""

    def test_upload_with_env(self, temp_slp_file: Path):
        """Test upload with staging environment."""
        mock_result = UploadResult(
            shortcode="aBcDeF",
            share_url="https://staging.slp.sh/aBcDeF",
            data_url="https://staging.slp.sh/aBcDeF/labels.slp",
            expires_at=None,
            is_permanent=False,
            validation_status="valid",
            metadata=None,
        )

        with patch("sleap_share.cli.SleapShareClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.upload.return_value = mock_result
            mock_client_cls.return_value = mock_client

            # --env option comes after the command in Typer
            result = runner.invoke(
                app, ["upload", str(temp_slp_file), "--env", "staging"]
            )

            assert result.exit_code == 0
            # Verify client was created with staging env
            mock_client_cls.assert_called_once()
            call_kwargs = mock_client_cls.call_args[1]
            assert call_kwargs.get("env") == "staging"
