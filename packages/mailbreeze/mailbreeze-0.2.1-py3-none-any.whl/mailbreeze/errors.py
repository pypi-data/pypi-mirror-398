"""Error classes for MailBreeze SDK.

All API-related errors extend from MailBreezeError.
"""

from typing import Any


class MailBreezeError(Exception):
    """Base error class for all MailBreeze SDK errors.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code for programmatic handling.
        status_code: HTTP status code (if applicable).
        request_id: Unique request ID for debugging with support.
        details: Additional error details (e.g., field-level validation errors).
    """

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.request_id = request_id
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        """Serialize error to dictionary.

        Useful for logging and error reporting.
        """
        return {
            "message": self.message,
            "code": self.code,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "details": self.details,
        }


class AuthenticationError(MailBreezeError):
    """Authentication failed (401).

    Raised when API key is missing, invalid, or expired.
    """

    def __init__(
        self,
        message: str,
        code: str = "AUTHENTICATION_ERROR",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=401,
            request_id=request_id,
        )


class ValidationError(MailBreezeError):
    """Validation failed (400).

    Raised when request data fails validation.
    """

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            request_id=request_id,
            details=details,
        )


class NotFoundError(MailBreezeError):
    """Resource not found (404).

    Raised when the requested resource does not exist.
    """

    def __init__(
        self,
        message: str,
        code: str = "NOT_FOUND",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=404,
            request_id=request_id,
        )


class RateLimitError(MailBreezeError):
    """Rate limit exceeded (429).

    Raised when too many requests are made in a time window.

    Attributes:
        retry_after: Seconds to wait before retrying.
    """

    def __init__(
        self,
        message: str,
        code: str = "RATE_LIMIT_EXCEEDED",
        request_id: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=429,
            request_id=request_id,
        )
        self.retry_after = retry_after

    def to_dict(self) -> dict[str, Any]:
        """Serialize error to dictionary including retry_after."""
        result = super().to_dict()
        result["retry_after"] = self.retry_after
        return result


class ServerError(MailBreezeError):
    """Server error (5xx).

    Raised when the API encounters an internal error.
    """

    def __init__(
        self,
        message: str,
        code: str = "SERVER_ERROR",
        status_code: int = 500,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            request_id=request_id,
        )


def create_error_from_response(
    status_code: int,
    body: dict[str, Any] | None,
    request_id: str | None = None,
    retry_after: int | None = None,
) -> MailBreezeError:
    """Create the appropriate error class from an HTTP response.

    Maps status codes to specific error types.

    Args:
        status_code: HTTP status code.
        body: Response body containing error details.
        request_id: Unique request ID for debugging.
        retry_after: Seconds to wait before retrying (for rate limits).

    Returns:
        Appropriate MailBreezeError subclass.
    """
    message = body.get("message", "Unknown error") if body else "Unknown error"
    code = body.get("code", "UNKNOWN_ERROR") if body else "UNKNOWN_ERROR"
    details = body.get("details") if body else None

    if status_code == 400:
        return ValidationError(
            message=message,
            code=code,
            request_id=request_id,
            details=details,
        )
    elif status_code == 401:
        return AuthenticationError(
            message=message,
            code=code,
            request_id=request_id,
        )
    elif status_code == 404:
        return NotFoundError(
            message=message,
            code=code,
            request_id=request_id,
        )
    elif status_code == 429:
        return RateLimitError(
            message=message,
            code=code,
            request_id=request_id,
            retry_after=retry_after,
        )
    elif status_code >= 500:
        return ServerError(
            message=message,
            code=code,
            status_code=status_code,
            request_id=request_id,
        )
    else:
        return MailBreezeError(
            message=message,
            code=code,
            status_code=status_code,
            request_id=request_id,
            details=details,
        )
