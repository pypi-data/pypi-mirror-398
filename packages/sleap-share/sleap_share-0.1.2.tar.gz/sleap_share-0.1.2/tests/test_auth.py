"""Tests for authentication."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sleap_share.auth import (
    _load_token_from_file,
    _save_token_to_file,
    clear_token,
    load_token,
    save_token,
)

if TYPE_CHECKING:
    from sleap_share.config import Environment


@dataclass
class MockConfig:
    """Mock config with customizable paths."""

    config_dir: Path
    env: Environment = "production"
    base_url: str | None = None

    @property
    def credentials_path(self) -> Path:
        return self.config_dir / "credentials"

    @property
    def url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")
        return "https://slp.sh"


class TestFileTokenStorage:
    """Tests for file-based token storage."""

    def test_save_and_load_token(self, tmp_path: Path):
        """Test saving and loading token from file."""
        config = MockConfig(config_dir=tmp_path)

        result = _save_token_to_file("test_token_123", config)
        assert "credentials" in result

        token = _load_token_from_file(config)
        assert token == "test_token_123"

    def test_file_permissions(self, tmp_path: Path):
        """Test that credentials file has secure permissions."""
        config = MockConfig(config_dir=tmp_path)
        _save_token_to_file("secret_token", config)

        cred_path = tmp_path / "credentials"
        mode = cred_path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Test loading when no credentials file exists."""
        config = MockConfig(config_dir=tmp_path / "nonexistent")
        token = _load_token_from_file(config)
        assert token is None

    def test_creates_parent_directory(self, tmp_path: Path):
        """Test that parent directories are created."""
        nested_dir = tmp_path / "nested" / "dir"
        config = MockConfig(config_dir=nested_dir)

        _save_token_to_file("token", config)

        assert nested_dir.exists()
        assert (nested_dir / "credentials").exists()


class TestTokenStorageWithKeyringFallback:
    """Tests for token storage with keyring fallback."""

    def test_save_uses_file_when_keyring_unavailable(
        self, tmp_path: Path, mock_keyring_unavailable
    ):
        """Test falling back to file when keyring unavailable."""
        config = MockConfig(config_dir=tmp_path)

        location = save_token("token123", config)
        assert "credentials" in location

        token = load_token(config)
        assert token == "token123"

    def test_load_returns_none_when_no_token(
        self, tmp_path: Path, mock_keyring_unavailable
    ):
        """Test loading when no token stored."""
        config = MockConfig(config_dir=tmp_path / "empty")
        token = load_token(config)
        assert token is None


class TestClearToken:
    """Tests for clearing tokens."""

    def test_clear_file_token(self, tmp_path: Path, mock_keyring_unavailable):
        """Test clearing token from file."""
        config = MockConfig(config_dir=tmp_path)
        cred_path = tmp_path / "credentials"
        cred_path.write_text("token_to_clear")

        result = clear_token(config)

        assert result is True
        assert not cred_path.exists()

    def test_clear_when_no_token(self, tmp_path: Path, mock_keyring_unavailable):
        """Test clearing when no token exists."""
        config = MockConfig(config_dir=tmp_path / "nonexistent")

        result = clear_token(config)
        assert result is False
