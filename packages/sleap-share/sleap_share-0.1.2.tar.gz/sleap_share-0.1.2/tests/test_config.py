"""Tests for configuration."""

import os
from unittest.mock import patch

from sleap_share.config import (
    Config,
    get_config,
    get_env_from_environment,
)


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()

        assert config.env == "production"
        assert config.url == "https://slp.sh"

    def test_staging_config(self):
        """Test staging configuration."""
        config = Config(env="staging")

        assert config.env == "staging"
        assert config.url == "https://staging.slp.sh"

    def test_custom_base_url(self):
        """Test custom base URL overrides env."""
        config = Config(env="production", base_url="http://localhost:8787")

        assert config.url == "http://localhost:8787"

    def test_base_url_strips_trailing_slash(self):
        """Test trailing slashes are stripped."""
        config = Config(base_url="http://localhost:8787/")

        assert config.url == "http://localhost:8787"

    def test_config_dir(self):
        """Test config directory path."""
        config = Config()

        assert "sleap-share" in str(config.config_dir)

    def test_credentials_path(self):
        """Test credentials file path."""
        config = Config()

        assert config.credentials_path.name == "credentials"
        assert "sleap-share" in str(config.credentials_path)


class TestGetEnvFromEnvironment:
    """Tests for environment variable handling."""

    def test_no_env_var(self):
        """Test default when no env var set."""
        with patch.dict(os.environ, {}, clear=True):
            env = get_env_from_environment()
            assert env == "production"

    def test_staging_env_var(self):
        """Test staging from env var."""
        with patch.dict(os.environ, {"SLEAP_SHARE_ENV": "staging"}):
            env = get_env_from_environment()
            assert env == "staging"

    def test_stg_shorthand(self):
        """Test stg shorthand."""
        with patch.dict(os.environ, {"SLEAP_SHARE_ENV": "stg"}):
            env = get_env_from_environment()
            assert env == "staging"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        with patch.dict(os.environ, {"SLEAP_SHARE_ENV": "STAGING"}):
            env = get_env_from_environment()
            assert env == "staging"

    def test_invalid_falls_back_to_production(self):
        """Test invalid values fall back to production."""
        with patch.dict(os.environ, {"SLEAP_SHARE_ENV": "invalid"}):
            env = get_env_from_environment()
            assert env == "production"


class TestGetConfig:
    """Tests for get_config function."""

    def test_explicit_env(self):
        """Test explicit env parameter."""
        config = get_config(env="staging")

        assert config.env == "staging"

    def test_env_from_environment(self):
        """Test env from environment variable."""
        with patch.dict(os.environ, {"SLEAP_SHARE_ENV": "staging"}):
            config = get_config()
            assert config.env == "staging"

    def test_explicit_overrides_env_var(self):
        """Test explicit parameter overrides env var."""
        with patch.dict(os.environ, {"SLEAP_SHARE_ENV": "staging"}):
            config = get_config(env="production")
            assert config.env == "production"

    def test_base_url_parameter(self):
        """Test base_url parameter."""
        config = get_config(base_url="http://localhost:8787")

        assert config.url == "http://localhost:8787"
