# sleap-share

Python client for [SLEAP Share](https://slp.sh) - upload and share SLEAP datasets.

## Installation

```bash
pip install sleap-share
```

Or use with `uvx` for one-off commands:

```bash
uvx sleap-share upload labels.slp
```

## Quick Start

### Command Line

```bash
# Upload a file (no account needed)
sleap-share upload labels.slp
# → https://slp.sh/aBcDeF

# Download a file
sleap-share download aBcDeF

# Get file info
sleap-share info aBcDeF

# Authenticate for more features
sleap-share login

# List your uploads
sleap-share list

# Delete a file
sleap-share delete aBcDeF
```

### Python API

```python
import sleap_share

# Upload (anonymous)
result = sleap_share.upload("labels.slp")
print(result.share_url)  # https://slp.sh/aBcDeF

# Download
sleap_share.download("aBcDeF", output="./data/")

# Get metadata
metadata = sleap_share.get_metadata("aBcDeF")
print(f"Labeled frames: {metadata.labeled_frames_count}")

# Lazy loading (stream data on-demand without full download)
import sleap_io
url = sleap_share.open("aBcDeF")
labels = sleap_io.load_slp(url)  # Only fetches accessed data!
```

### Authenticated Operations

```python
# Use stored credentials from `sleap-share login`
client = sleap_share.Client()

# Or provide token directly
client = sleap_share.Client(token="slpsh_live_...")

# List your files
files = client.list_files()

# Delete a file
client.delete("aBcDeF")

# Get user info
user = client.whoami()
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `login` | Authenticate via browser |
| `logout` | Clear stored credentials |
| `whoami` | Show current user |
| `upload <file>` | Upload a .slp file |
| `download <id>` | Download a file |
| `list` | List your uploads |
| `info <id>` | Show file metadata |
| `preview <id>` | Download preview image |
| `delete <id>` | Delete a file |
| `version` | Show version |

### Global Options

- `--env staging` - Target staging environment instead of production
- `--help` - Show help for any command

## Environment Variables

- `SLEAP_SHARE_ENV` - Default environment (`production` or `staging`)

## Token Storage

Credentials are stored securely using:
1. System keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service)
2. Fallback: `~/.config/sleap-share/credentials` with `0600` permissions

## Development

```bash
cd client

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy src/sleap_share
```

## Releasing

New versions are published to PyPI via GitHub Releases.

### Steps to Release

1. **Update version** in `pyproject.toml` and `src/sleap_share/__init__.py`

2. **Update CHANGELOG.md** with the new version and release notes

3. **Create a GitHub Release:**
   - Go to [Releases](https://github.com/talmolab/sleap-share/releases/new)
   - **Tag:** `client-v{version}` (e.g., `client-v0.2.0`)
   - **Title:** `Python Client v{version}`
   - **Description:** Copy from CHANGELOG.md
   - Click **Publish release**

4. The GitHub Action will automatically:
   - Run tests on Python 3.9-3.13
   - Run linting and type checks
   - Build the package
   - Publish to PyPI via OIDC trusted publishing

### Version Scheme

Tags must start with `client-v` to trigger publishing (e.g., `client-v0.1.0`, `client-v1.0.0`).

This prefix distinguishes Python client releases from other releases in the monorepo.

## License

MIT License - see [LICENSE](../LICENSE) for details.
