"""Custom exceptions for sleap-share client."""

from __future__ import annotations


class SleapShareError(Exception):
    """Base exception for sleap-share client errors.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code (e.g., "not_found", "rate_limited").
        status_code: HTTP status code if applicable.
    """

    def __init__(
        self,
        message: str,
        code: str = "unknown_error",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def __str__(self) -> str:
        return self.message


class AuthenticationError(SleapShareError):
    """Raised when authentication fails or token is invalid."""

    def __init__(
        self,
        message: str = "Authentication required. Run 'sleap-share login' to authenticate.",
        code: str = "authentication_required",
        status_code: int = 401,
    ) -> None:
        super().__init__(message, code, status_code)


class NotFoundError(SleapShareError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        code: str = "not_found",
        status_code: int = 404,
    ) -> None:
        super().__init__(message, code, status_code)


class RateLimitError(SleapShareError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        code: str = "rate_limited",
        status_code: int = 429,
        retry_after: int | None = None,
    ) -> None:
        if retry_after:
            message = f"{message} Retry after {retry_after} seconds."
        super().__init__(message, code, status_code)
        self.retry_after = retry_after


class ValidationError(SleapShareError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation error.",
        code: str = "validation_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(message, code, status_code)


class PermissionError(SleapShareError):
    """Raised when the user lacks permission for an operation."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        code: str = "permission_denied",
        status_code: int = 403,
    ) -> None:
        super().__init__(message, code, status_code)


class UploadError(SleapShareError):
    """Raised when file upload fails."""

    def __init__(
        self,
        message: str = "File upload failed.",
        code: str = "upload_failed",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, code, status_code)


class DownloadError(SleapShareError):
    """Raised when file download fails."""

    def __init__(
        self,
        message: str = "File download failed.",
        code: str = "download_failed",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, code, status_code)


class NetworkError(SleapShareError):
    """Raised when a network error occurs."""

    def __init__(
        self,
        message: str = "Network error. Please check your internet connection.",
        code: str = "network_error",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, code, status_code)
