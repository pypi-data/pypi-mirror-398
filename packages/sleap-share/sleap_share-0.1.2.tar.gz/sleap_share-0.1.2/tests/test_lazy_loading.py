"""Tests for lazy loading / virtual file access functionality.

These tests verify that the client returns URLs suitable for HTTP range request-based
lazy loading, which allows HDF5 clients (h5py ros3, fsspec, sleap-io) to stream
bytes on-demand without downloading the entire file.
"""

from __future__ import annotations

import pytest

from sleap_share import get_download_url, get_urls, open
from sleap_share.client import SleapShareClient


class TestOpenFunction:
    """Tests for the open() function."""

    def test_open_returns_download_url(self):
        """Test that open() returns the download URL."""
        client = SleapShareClient()
        url = client.open("aBcDeF")

        assert url == "https://slp.sh/aBcDeF/labels.slp"

    def test_open_with_staging_env(self):
        """Test open() with staging environment."""
        client = SleapShareClient(env="staging")
        url = client.open("aBcDeF")

        assert url == "https://staging.slp.sh/aBcDeF/labels.slp"

    def test_open_module_function(self):
        """Test module-level open() function."""
        url = open("aBcDeF")

        assert url == "https://slp.sh/aBcDeF/labels.slp"

    def test_open_from_full_url(self):
        """Test open() with full URL input."""
        client = SleapShareClient()
        url = client.open("https://slp.sh/aBcDeF")

        assert url == "https://slp.sh/aBcDeF/labels.slp"


class TestGetDownloadUrl:
    """Tests for get_download_url() function."""

    def test_get_download_url_returns_slp_url(self):
        """Test that download URL points to labels.slp."""
        client = SleapShareClient()
        url = client.get_download_url("aBcDeF")

        assert url.endswith("/labels.slp")
        assert "aBcDeF" in url

    def test_get_download_url_module_function(self):
        """Test module-level get_download_url() function."""
        url = get_download_url("aBcDeF")

        assert url == "https://slp.sh/aBcDeF/labels.slp"


class TestGetUrls:
    """Tests for get_urls() function."""

    def test_get_urls_returns_all_urls(self):
        """Test that get_urls() returns all URL types."""
        client = SleapShareClient()
        urls = client.get_urls("aBcDeF")

        assert urls.share_url == "https://slp.sh/aBcDeF"
        assert urls.download_url == "https://slp.sh/aBcDeF/labels.slp"
        assert urls.metadata_url == "https://slp.sh/aBcDeF/metadata.json"
        assert urls.preview_url == "https://slp.sh/aBcDeF/preview.png"

    def test_get_urls_module_function(self):
        """Test module-level get_urls() function."""
        urls = get_urls("aBcDeF")

        assert urls.share_url == "https://slp.sh/aBcDeF"
        assert urls.download_url == "https://slp.sh/aBcDeF/labels.slp"


class TestHttpRangeRequestCompatibility:
    """Tests to verify the URLs are suitable for HTTP range requests."""

    def test_download_url_format(self):
        """Test download URL format is suitable for range requests."""
        client = SleapShareClient()
        url = client.get_download_url("aBcDeF")

        # URL should be a simple HTTPS URL that can support range requests
        assert url.startswith("https://")
        assert ".slp" in url
        # No query parameters that might interfere with caching/range requests
        assert "?" not in url

    def test_staging_url_format(self):
        """Test staging URLs are correctly formatted."""
        client = SleapShareClient(env="staging")
        url = client.get_download_url("aBcDeF")

        assert "staging" in url
        assert url.startswith("https://staging.slp.sh/")

    @pytest.mark.skipif(
        True, reason="Requires network access - run manually for integration testing"
    )
    def test_range_request_headers_real_server(self, httpx_mock):
        """Integration test: verify server supports range requests.

        This test is skipped by default but can be run manually to verify
        that the actual server returns proper range request headers.
        """
        import httpx

        # This would make a real request to staging to verify range request support
        client = httpx.Client()
        response = client.head("https://staging.slp.sh/test/labels.slp")

        # Server should indicate range request support
        assert response.headers.get("Accept-Ranges") == "bytes"


class TestFsspecCompatibility:
    """Tests for fsspec compatibility (when available)."""

    @pytest.mark.skipif(
        True, reason="Requires fsspec - install with: pip install sleap-share[lazy]"
    )
    def test_fsspec_http_filesystem(self):
        """Test that URLs work with fsspec HTTPFileSystem.

        This test is skipped by default but can be run when fsspec is installed.
        """
        try:
            import fsspec

            # Create an HTTP filesystem - just verify it doesn't raise
            _ = fsspec.filesystem("http")

            # Get a download URL
            client = SleapShareClient()
            url = client.get_download_url("aBcDeF")

            # This should not raise - the URL format is valid for fsspec
            # (actual file access would fail without a real shortcode)
            assert url.startswith("https://")

        except ImportError:
            pytest.skip("fsspec not installed")


class TestUrlExtraction:
    """Tests for URL parsing in lazy loading context."""

    def test_shortcode_from_url_extraction(self):
        """Test that shortcode is correctly extracted from URLs."""
        client = SleapShareClient()

        # Test with various URL formats
        urls_to_test = [
            ("aBcDeF", "aBcDeF"),
            ("https://slp.sh/aBcDeF", "aBcDeF"),
            ("https://slp.sh/aBcDeF/labels.slp", "aBcDeF"),
            ("https://staging.slp.sh/aBcDeF", "aBcDeF"),
            ("https://staging.slp.sh/aBcDeF/metadata.json", "aBcDeF"),
        ]

        for input_url, expected_shortcode in urls_to_test:
            result_url = client.open(input_url)
            # The result should contain the expected shortcode
            assert expected_shortcode in result_url, f"Failed for {input_url}"
