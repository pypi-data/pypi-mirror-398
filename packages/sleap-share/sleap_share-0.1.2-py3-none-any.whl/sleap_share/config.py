"""Configuration and constants for sleap-share client."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from platformdirs import user_config_dir

# Environment type
Environment = Literal["production", "staging"]

# Base URLs for each environment
URLS = {
    "production": "https://slp.sh",
    "staging": "https://staging.slp.sh",
}

# Default environment
DEFAULT_ENV: Environment = "production"

# Environment variable for overriding default environment
ENV_VAR = "SLEAP_SHARE_ENV"

# App name for config/credential paths
APP_NAME = "sleap-share"

# Keyring service name
KEYRING_SERVICE = "sleap-share"
KEYRING_USERNAME = "api_token"

# Credentials file name (fallback when keyring unavailable)
CREDENTIALS_FILE = "credentials"

# HTTP client settings
DEFAULT_TIMEOUT = 30.0  # seconds
UPLOAD_TIMEOUT = 600.0  # 10 minutes for large uploads
DOWNLOAD_CHUNK_SIZE = 8192  # 8KB chunks for streaming

# Allowed file extensions
ALLOWED_EXTENSIONS = {".slp"}


@dataclass
class Config:
    """Runtime configuration for the sleap-share client."""

    env: Environment = DEFAULT_ENV
    base_url: str | None = None  # If set, overrides env-based URL

    @property
    def url(self) -> str:
        """Get the base URL for the current environment."""
        if self.base_url:
            return self.base_url.rstrip("/")
        return URLS[self.env]

    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return Path(user_config_dir(APP_NAME))

    @property
    def credentials_path(self) -> Path:
        """Get the path to the credentials file (fallback storage)."""
        return self.config_dir / CREDENTIALS_FILE


def get_env_from_environment() -> Environment:
    """Get environment from environment variable, or default."""
    env_value = os.environ.get(ENV_VAR, "").lower()
    if env_value in ("staging", "stg"):
        return "staging"
    return DEFAULT_ENV


def _validate_env(env: str | None) -> Environment | None:
    """Validate and convert env string to Environment type."""
    if env is None:
        return None
    if env in ("production", "staging"):
        return env  # type: ignore[return-value]
    return None


def get_config(
    env: str | None = None,
    base_url: str | None = None,
) -> Config:
    """Create a configuration object.

    Args:
        env: Target environment (production or staging).
            If not specified, uses SLEAP_SHARE_ENV or defaults to production.
        base_url: Override base URL directly (ignores env setting).

    Returns:
        Config object with the resolved settings.
    """
    validated_env = _validate_env(env)
    if validated_env is None:
        validated_env = get_env_from_environment()
    return Config(env=validated_env, base_url=base_url)
