"""Authentication and token storage for sleap-share client."""

import time
import webbrowser
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import KEYRING_SERVICE, KEYRING_USERNAME, Config, get_config
from .exceptions import AuthenticationError


def _try_keyring_available() -> bool:
    """Check if keyring is available and functional."""
    try:
        import keyring
        from keyring.errors import KeyringError

        # Try a test operation to see if keyring works
        try:
            keyring.get_password(KEYRING_SERVICE, "__test__")
            return True
        except KeyringError:
            return False
    except ImportError:
        return False


def save_token(token: str, config: Config | None = None) -> str:
    """Save API token securely.

    Attempts to use system keyring first, falls back to file storage.

    Args:
        token: The API token to save.
        config: Configuration object (uses default if not provided).

    Returns:
        Description of where the token was stored.
    """
    if config is None:
        config = get_config()

    # Try keyring first
    if _try_keyring_available():
        try:
            import keyring

            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
            return "system keyring"
        except Exception:
            pass  # Fall through to file storage

    # Fallback to file storage
    return _save_token_to_file(token, config)


def _save_token_to_file(token: str, config: Config) -> str:
    """Save token to file with secure permissions.

    Args:
        token: The API token to save.
        config: Configuration object.

    Returns:
        Description of where the token was stored.
    """
    cred_path = config.credentials_path

    # Create parent directory if needed
    cred_path.parent.mkdir(parents=True, exist_ok=True)

    # Write token with secure permissions
    cred_path.write_text(token)
    cred_path.chmod(0o600)

    return str(cred_path)


def load_token(config: Config | None = None) -> str | None:
    """Load API token from storage.

    Attempts keyring first, then file storage.

    Args:
        config: Configuration object (uses default if not provided).

    Returns:
        The stored token, or None if not found.
    """
    if config is None:
        config = get_config()

    # Try keyring first
    if _try_keyring_available():
        try:
            import keyring

            token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if token:
                return token
        except Exception:
            pass

    # Try file storage
    return _load_token_from_file(config)


def _load_token_from_file(config: Config) -> str | None:
    """Load token from file.

    Args:
        config: Configuration object.

    Returns:
        The stored token, or None if not found.
    """
    cred_path = config.credentials_path

    if cred_path.exists():
        try:
            return cred_path.read_text().strip()
        except Exception:
            return None
    return None


def clear_token(config: Config | None = None) -> bool:
    """Clear stored API token from all storage locations.

    Args:
        config: Configuration object (uses default if not provided).

    Returns:
        True if any token was cleared, False otherwise.
    """
    if config is None:
        config = get_config()

    cleared = False

    # Clear from keyring
    if _try_keyring_available():
        try:
            import keyring

            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            cleared = True
        except Exception:
            pass

    # Clear from file
    cred_path = config.credentials_path
    if cred_path.exists():
        try:
            cred_path.unlink()
            cleared = True
        except Exception:
            pass

    return cleared


def device_auth_start(
    http_client: httpx.Client,
    config: Config,
) -> dict[str, Any]:
    """Start device authorization flow.

    Args:
        http_client: HTTP client instance.
        config: Configuration object.

    Returns:
        Response containing device_code, user_code, verification_url, etc.

    Raises:
        AuthenticationError: If the request fails.
    """
    try:
        response = http_client.post(f"{config.url}/api/auth/cli/start")
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
    except httpx.HTTPStatusError as e:
        raise AuthenticationError(
            f"Failed to start device authorization: {e.response.text}",
            code="auth_start_failed",
            status_code=e.response.status_code,
        ) from e
    except httpx.RequestError as e:
        raise AuthenticationError(
            f"Network error during device authorization: {e}",
            code="network_error",
        ) from e


def device_auth_poll(
    http_client: httpx.Client,
    config: Config,
    device_code: str,
) -> dict[str, Any]:
    """Poll for device authorization completion.

    Args:
        http_client: HTTP client instance.
        config: Configuration object.
        device_code: Device code from start response.

    Returns:
        Response containing status, and token if authorized.

    Raises:
        AuthenticationError: If the request fails.
    """
    try:
        response = http_client.post(
            f"{config.url}/api/auth/cli/poll",
            json={"device_code": device_code},
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
    except httpx.HTTPStatusError as e:
        raise AuthenticationError(
            f"Failed to poll device authorization: {e.response.text}",
            code="auth_poll_failed",
            status_code=e.response.status_code,
        ) from e
    except httpx.RequestError as e:
        raise AuthenticationError(
            f"Network error during device authorization: {e}",
            code="network_error",
        ) from e


def run_device_auth_flow(
    http_client: httpx.Client,
    config: Config,
    console: Console | None = None,
) -> tuple[str, str]:
    """Run the full device authorization flow.

    Args:
        http_client: HTTP client instance.
        config: Configuration object.
        console: Rich console for output (optional).

    Returns:
        Tuple of (token, username) on success.

    Raises:
        AuthenticationError: If authorization fails or expires.
    """
    if console is None:
        console = Console()

    # Start device auth
    start_response = device_auth_start(http_client, config)

    device_code = start_response["device_code"]
    user_code = start_response["user_code"]
    verification_url = start_response["verification_url"]
    interval = start_response.get("interval", 5)
    expires_in = start_response.get("expires_in", 600)

    # Display instructions
    console.print()
    console.print(
        Panel(
            f"[bold]1.[/bold] Open: [link={verification_url}]{verification_url}[/link]\n"
            f"[bold]2.[/bold] Enter code: [bold cyan]{user_code}[/bold cyan]",
            title="[bold green]Authenticate with SLEAP Share[/bold green]",
            border_style="green",
        )
    )
    console.print()

    # Try to open browser
    try:
        webbrowser.open(verification_url)
        console.print("[dim]Opening browser...[/dim]")
    except Exception:
        pass

    # Poll for completion
    start_time = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Waiting for browser authorization...", total=None)

        while time.time() - start_time < expires_in:
            time.sleep(interval)

            poll_response = device_auth_poll(http_client, config, device_code)
            status = poll_response.get("status")

            if status == "success":
                token = poll_response["token"]
                username = poll_response.get("username", "")

                # Save token
                storage_location = save_token(token, config)

                progress.stop()
                console.print()
                console.print(f"[bold green]Logged in as {username}[/bold green]")
                console.print(f"[dim]Credentials stored in {storage_location}[/dim]")

                return token, username

            elif status == "expired":
                raise AuthenticationError(
                    "Authorization expired. Please try again.",
                    code="auth_expired",
                )

            # status == "pending" - continue polling

    raise AuthenticationError(
        "Authorization timed out. Please try again.",
        code="auth_timeout",
    )
