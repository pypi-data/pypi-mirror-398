from typing import Any


class FlanksError(Exception):
    """Base exception for all Flanks SDK errors."""

    pass


class FlanksConfigError(FlanksError):
    """Raised when client configuration is invalid."""

    pass


class FlanksAPIError(FlanksError):
    """Base for all API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FlanksAuthError(FlanksAPIError):
    """401/403 - Invalid or expired credentials/token."""

    pass


class FlanksValidationError(FlanksAPIError):
    """400 - Request validation failed."""

    pass


class FlanksNotFoundError(FlanksAPIError):
    """404 - Resource not found."""

    pass


class FlanksServerError(FlanksAPIError):
    """5xx - Server-side error (retryable)."""

    pass


class FlanksNetworkError(FlanksError):
    """Network-level failure (connection refused, timeout, DNS)."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause
