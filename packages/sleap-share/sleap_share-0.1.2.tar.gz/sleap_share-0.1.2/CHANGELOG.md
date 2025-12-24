# Changelog

All notable changes to the `sleap-share` Python client will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2025-12-19

### Fixed

- Fixed upload API compatibility (camelCase field names: `fileSize`, `uploadUrl`)
- Fixed missing `Content-Length` header for R2 presigned URL uploads
- Fixed httpx timeout configuration for large file uploads
- Fixed progress callback compatibility with httpx (use iterator protocol)
- Fixed timeout for `/api/upload/complete` endpoint (metadata extraction)
- Fixed `UploadResult` parsing to handle camelCase API response

### Added

- Added "Validating..." spinner after upload reaches 100% while waiting for metadata extraction
- Added `status_callback` parameter to `upload()` for tracking upload phases
- Added comprehensive rate limit reset documentation to DEVELOPMENT.md

## [0.1.1] - 2025-12-19

### Added

- CLI now accepts URLs without protocol prefix (e.g., `slp.sh/aBcDeF`, `staging.slp.sh/aBcDeF`)
- Downloads no longer overwrite existing files by default - automatically appends `(1)`, `(2)`, etc.
- Added `--overwrite`/`--no-overwrite` (`-f`) flag to control overwrite behavior
  - Default: overwrite if `-o` specifies an explicit filename, otherwise append numbers

### Fixed

- Fixed metadata retrieval to use `/api/metadata/{shortcode}` endpoint which returns complete file info (filename, size, upload time, expiry) instead of raw SLP metadata only
- Downloads now save with correct original filename instead of "unknown"
- `sleap-share info` now displays correct file information

### Changed

- Bumped minimum Python version to 3.11
- Removed `from __future__ import annotations` (not needed with Python 3.11+)
- Use `typing.Self` for context manager return type

## [0.1.0] - 2024-12-19

### Added

- Initial release of the `sleap-share` Python client
- **CLI Commands**
  - `sleap-share login` - Device authorization flow with browser authentication
  - `sleap-share logout` - Clear stored credentials
  - `sleap-share whoami` - Show current authenticated user
  - `sleap-share upload <file>` - Upload .slp files with progress bar
  - `sleap-share download <shortcode>` - Download files by shortcode or URL
  - `sleap-share list` - List your uploaded files in a table
  - `sleap-share info <shortcode>` - Show file metadata (with `--json` option)
  - `sleap-share preview <shortcode>` - Download preview image
  - `sleap-share delete <shortcode>` - Delete files you own
  - `sleap-share version` - Show version information
- **Python API**
  - `sleap_share.upload()` - Upload files programmatically
  - `sleap_share.download()` - Download files programmatically
  - `sleap_share.get_info()` - Get basic file information
  - `sleap_share.get_metadata()` - Get full metadata including SLP statistics
  - `sleap_share.get_preview()` - Download preview images
  - `sleap_share.get_urls()` - Get all URLs for a shortcode
  - `sleap_share.get_download_url()` - Get direct download URL
  - `sleap_share.get_preview_url()` - Get preview image URL
  - `sleap_share.open()` - Get URL for lazy loading with HTTP range requests
  - `sleap_share.Client` - Full-featured client class for authenticated operations
- **Authentication**
  - OAuth 2.0 Device Authorization Grant for CLI login
  - Secure token storage via system keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service)
  - File-based fallback with secure permissions (0600)
- **Environment Support**
  - Target production (`slp.sh`) or staging (`staging.slp.sh`) environments
  - Configure via `--env` flag or `SLEAP_SHARE_ENV` environment variable
- **Lazy Loading**
  - All download URLs support HTTP range requests
  - Compatible with h5py ros3 driver, fsspec, and sleap-io for streaming access
  - Access file contents without downloading the entire file

### Dependencies

- `httpx` - Modern HTTP client with streaming support
- `typer` - CLI framework with type hints
- `rich` - Terminal output with progress bars and tables
- `platformdirs` - Cross-platform configuration directories
- `keyring` (optional) - Secure credential storage
- `fsspec` (optional) - Lazy loading support

[Unreleased]: https://github.com/talmolab/sleap-share/compare/client-v0.1.2...HEAD
[0.1.2]: https://github.com/talmolab/sleap-share/compare/client-v0.1.1...client-v0.1.2
[0.1.1]: https://github.com/talmolab/sleap-share/compare/client-v0.1.0...client-v0.1.1
[0.1.0]: https://github.com/talmolab/sleap-share/releases/tag/client-v0.1.0
