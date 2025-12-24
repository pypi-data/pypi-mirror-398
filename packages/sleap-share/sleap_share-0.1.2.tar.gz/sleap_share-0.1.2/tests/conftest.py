"""Test fixtures for sleap-share client."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_slp_file(tmp_path: Path) -> Path:
    """Create a temporary .slp file for testing."""
    slp_file = tmp_path / "test_labels.slp"
    # Create a minimal HDF5-like file (just random bytes for testing)
    slp_file.write_bytes(b"HDF5 fake content for testing" * 100)
    return slp_file


@pytest.fixture
def sample_upload_init_response() -> dict[str, Any]:
    """Sample response from /api/upload/init (camelCase from API)."""
    return {
        "shortcode": "aBcDeF",
        "uploadUrl": "https://r2.example.com/presigned-upload-url",
    }


@pytest.fixture
def sample_upload_complete_response() -> dict[str, Any]:
    """Sample response from /api/upload/complete (camelCase from API)."""
    expires_at = int((datetime.now() + timedelta(days=30)).timestamp() * 1000)
    return {
        "success": True,
        "shareUrl": "https://slp.sh/aBcDeF",
        "dataUrl": "https://slp.sh/aBcDeF/labels.slp",
        "expiresAt": expires_at,
        "isPermanent": False,
        "validationStatus": "valid",
        "metadata": {
            "labeledFramesCount": 100,
            "userInstancesCount": 50,
            "predictedInstancesCount": 200,
            "tracksCount": 5,
            "videosCount": 1,
        },
    }


@pytest.fixture
def sample_metadata_response() -> dict[str, Any]:
    """Sample /api/metadata/{shortcode} response (camelCase from API)."""
    now = int(datetime.now().timestamp() * 1000)
    expires = int((datetime.now() + timedelta(days=30)).timestamp() * 1000)
    return {
        "shortcode": "aBcDeF",
        "originalFilename": "test_labels.slp",
        "fileSize": 3000,
        "uploadedAt": now,
        "expiresAt": expires,
        "status": "active",
        "shareUrl": "https://slp.sh/aBcDeF",
        "dataUrl": "https://slp.sh/aBcDeF/labels.slp",
        "userId": "github:123",
        "viewCount": 0,
        "validationStatus": "valid",
        "metadata": {
            "labeledFramesCount": 100,
            "userInstancesCount": 50,
            "predictedInstancesCount": 200,
            "tracksCount": 5,
            "videosCount": 1,
            "suggestionsCount": 0,
            "hasEmbeddedImages": True,
            "formatVersion": "1.1",
        },
    }


@pytest.fixture
def sample_metadata_dict() -> dict[str, Any]:
    """Sample metadata in snake_case for Metadata.from_dict() tests."""
    return {
        "shortcode": "aBcDeF",
        "original_filename": "test_labels.slp",
        "file_size": 3000,
        "upload_timestamp": datetime.now().isoformat() + "Z",
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat() + "Z",
        "validation_status": "valid",
        "labeled_frames_count": 100,
        "user_instances_count": 50,
        "predicted_instances_count": 200,
        "tracks_count": 5,
        "videos_count": 1,
    }


@pytest.fixture
def sample_user_response() -> dict[str, Any]:
    """Sample response from /api/v1/user/me."""
    return {
        "id": 123,
        "username": "testuser",
        "email": "test@example.com",
        "avatar_url": "https://github.com/testuser.png",
        "total_files": 10,
        "total_storage": 1024 * 1024 * 100,  # 100 MB
    }


@pytest.fixture
def sample_files_response() -> dict[str, Any]:
    """Sample response from /api/v1/user/files."""
    return {
        "files": [
            {
                "shortcode": "aBcDeF",
                "filename": "test1.slp",
                "file_size": 1000,
                "created_at": datetime.now().isoformat() + "Z",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat() + "Z",
            },
            {
                "shortcode": "gHiJkL",
                "filename": "test2.slp",
                "file_size": 2000,
                "created_at": datetime.now().isoformat() + "Z",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat() + "Z",
            },
        ]
    }


@pytest.fixture
def sample_device_auth_start_response() -> dict[str, Any]:
    """Sample response from /api/auth/cli/start."""
    return {
        "device_code": "device123",
        "user_code": "ABC-123",
        "verification_url": "https://slp.sh/device",
        "interval": 5,
        "expires_in": 600,
    }


@pytest.fixture
def sample_device_auth_poll_success_response() -> dict[str, Any]:
    """Sample success response from /api/auth/cli/poll."""
    return {
        "status": "success",
        "token": "slpsh_live_testtoken123",
        "username": "testuser",
    }


@pytest.fixture
def mock_keyring_unavailable():
    """Mock keyring as unavailable."""
    with patch("sleap_share.auth._try_keyring_available", return_value=False):
        yield


@pytest.fixture
def mock_token_storage(tmp_path: Path):
    """Mock token storage to use temp directory."""
    config_dir = tmp_path / ".config" / "sleap-share"

    with patch("sleap_share.config.user_config_dir", return_value=str(config_dir)):
        yield config_dir
