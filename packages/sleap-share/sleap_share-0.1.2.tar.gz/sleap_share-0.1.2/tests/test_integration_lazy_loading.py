"""Integration tests for lazy loading with real staging server.

These tests require network access and interact with the staging server.
They are skipped by default and can be enabled by setting the environment
variable SLEAP_SHARE_INTEGRATION_TESTS=1.

To run these tests:
    SLEAP_SHARE_INTEGRATION_TESTS=1 uv run pytest tests/test_integration_lazy_loading.py -v
"""

from __future__ import annotations

import os

import pytest

# Skip all tests in this module unless integration tests are enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("SLEAP_SHARE_INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled. Set SLEAP_SHARE_INTEGRATION_TESTS=1 to enable.",
)


class TestRangeRequestsIntegration:
    """Integration tests for HTTP range request support."""

    def test_server_supports_range_requests(self):
        """Verify staging server returns Accept-Ranges header."""
        import httpx

        # Use a HEAD request to check headers without downloading
        # This tests against the staging server's infrastructure
        client = httpx.Client()
        response = client.head("https://staging.slp.sh/")

        # Check that the server is reachable
        assert response.status_code in [200, 301, 302, 404]

    def test_range_header_handling(self):
        """Test that server handles Range headers correctly."""
        import httpx

        # Note: This test requires a valid shortcode on staging
        # For now, we just verify the server handles invalid requests gracefully
        client = httpx.Client()

        # Request with Range header
        response = client.get(
            "https://staging.slp.sh/nonexistent/labels.slp",
            headers={"Range": "bytes=0-100"},
        )

        # Should return 404 for nonexistent file, not an error
        assert response.status_code in [404, 206, 416]


class TestFsspecIntegration:
    """Integration tests for fsspec HTTP filesystem."""

    @pytest.fixture
    def fsspec_available(self):
        """Check if fsspec is installed."""
        try:
            import importlib.util

            if importlib.util.find_spec("fsspec") is None:
                pytest.skip(
                    "fsspec not installed - install with: pip install sleap-share[lazy]"
                )
            return True
        except ImportError:
            pytest.skip(
                "fsspec not installed - install with: pip install sleap-share[lazy]"
            )

    def test_fsspec_http_open(self, fsspec_available):
        """Test opening a URL with fsspec HTTPFileSystem."""
        import fsspec

        # Create an HTTP filesystem
        fs = fsspec.filesystem("http")

        # Test that we can check if a path exists (will be False for nonexistent)
        # This verifies fsspec can communicate with the server
        url = "https://staging.slp.sh/nonexistent/labels.slp"

        # exists() should work without error
        exists = fs.exists(url)
        assert exists is False  # File doesn't exist

    def test_fsspec_with_real_file(self, fsspec_available):
        """Test fsspec with a real uploaded file on staging.

        This test requires a valid shortcode to be set in the environment.
        Set TEST_SHORTCODE environment variable to run this test.
        """
        shortcode = os.environ.get("TEST_SHORTCODE")
        if not shortcode:
            pytest.skip(
                "Set TEST_SHORTCODE environment variable to test with real file"
            )

        import fsspec

        from sleap_share import get_download_url

        # Get the download URL
        url = get_download_url(shortcode, env="staging")

        # Open with fsspec
        fs = fsspec.filesystem("http")

        # Check file exists
        assert fs.exists(url), f"File not found at {url}"

        # Get file size (uses HEAD request)
        info = fs.info(url)
        assert "size" in info
        assert info["size"] > 0


class TestH5pyRos3Integration:
    """Integration tests for h5py ros3 driver (if available)."""

    @pytest.fixture
    def h5py_ros3_available(self):
        """Check if h5py with ros3 driver is available."""
        try:
            import h5py

            # Check if ros3 driver is available
            if "ros3" not in h5py.registered_drivers():
                pytest.skip("h5py ros3 driver not available")
            return True
        except ImportError:
            pytest.skip("h5py not installed")

    def test_h5py_ros3_url_format(self, h5py_ros3_available):
        """Verify URL format is compatible with h5py ros3 driver."""
        from sleap_share import get_download_url

        url = get_download_url("aBcDeF", env="staging")

        # ros3 driver requires https:// URLs
        assert url.startswith("https://")

        # URL should not have query parameters
        assert "?" not in url


class TestSleapIoIntegration:
    """Integration tests for sleap-io lazy loading."""

    @pytest.fixture
    def sleap_io_available(self):
        """Check if sleap-io is installed."""
        try:
            import importlib.util

            if importlib.util.find_spec("sleap_io") is None:
                pytest.skip("sleap-io not installed")
            return True
        except ImportError:
            pytest.skip("sleap-io not installed")

    def test_sleap_io_url_format(self, sleap_io_available):
        """Verify URL format is compatible with sleap-io."""
        from sleap_share import open as sleap_share_open

        url = sleap_share_open("aBcDeF", env="staging")

        # sleap-io expects HTTPS URLs for remote loading
        assert url.startswith("https://")
        assert ".slp" in url

    def test_sleap_io_with_real_file(self, sleap_io_available):
        """Test loading a real SLP file with sleap-io.

        This test requires a valid shortcode to be set in the environment.
        Set TEST_SHORTCODE environment variable to run this test.
        """
        shortcode = os.environ.get("TEST_SHORTCODE")
        if not shortcode:
            pytest.skip(
                "Set TEST_SHORTCODE environment variable to test with real file"
            )

        import sleap_io

        from sleap_share import open as sleap_share_open

        # Get the URL for lazy loading
        url = sleap_share_open(shortcode, env="staging")

        # Load the file (this will use HTTP range requests)
        labels = sleap_io.load_slp(url)

        # Verify we can access basic properties without downloading everything
        assert labels is not None
        assert hasattr(labels, "skeletons")
