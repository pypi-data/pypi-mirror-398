"""Tests for error classes."""

from mailbreeze.errors import (
    AuthenticationError,
    MailBreezeError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    create_error_from_response,
)


class TestMailBreezeError:
    """Tests for base MailBreezeError class."""

    def test_basic_error(self) -> None:
        """Should create error with message and code."""
        error = MailBreezeError("Something went wrong", "UNKNOWN_ERROR")
        assert str(error) == "Something went wrong"
        assert error.code == "UNKNOWN_ERROR"
        assert error.status_code is None
        assert error.request_id is None
        assert error.details is None

    def test_error_with_all_fields(self) -> None:
        """Should create error with all optional fields."""
        error = MailBreezeError(
            message="Validation failed",
            code="VALIDATION_ERROR",
            status_code=400,
            request_id="req_123",
            details={"field": "email", "reason": "invalid format"},
        )
        assert error.message == "Validation failed"
        assert error.code == "VALIDATION_ERROR"
        assert error.status_code == 400
        assert error.request_id == "req_123"
        assert error.details == {"field": "email", "reason": "invalid format"}

    def test_error_inheritance(self) -> None:
        """Should inherit from Exception."""
        error = MailBreezeError("Test", "TEST")
        assert isinstance(error, Exception)

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        error = MailBreezeError(
            message="Test error",
            code="TEST_ERROR",
            status_code=500,
            request_id="req_abc",
            details={"key": "value"},
        )
        result = error.to_dict()
        assert result == {
            "message": "Test error",
            "code": "TEST_ERROR",
            "status_code": 500,
            "request_id": "req_abc",
            "details": {"key": "value"},
        }


class TestAuthenticationError:
    """Tests for AuthenticationError class."""

    def test_default_values(self) -> None:
        """Should have correct defaults."""
        error = AuthenticationError("Invalid API key")
        assert error.message == "Invalid API key"
        assert error.code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401

    def test_custom_code(self) -> None:
        """Should accept custom code."""
        error = AuthenticationError("Expired token", code="TOKEN_EXPIRED")
        assert error.code == "TOKEN_EXPIRED"
        assert error.status_code == 401

    def test_inheritance(self) -> None:
        """Should inherit from MailBreezeError."""
        error = AuthenticationError("Test")
        assert isinstance(error, MailBreezeError)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_default_values(self) -> None:
        """Should have correct defaults."""
        error = ValidationError("Invalid email format")
        assert error.message == "Invalid email format"
        assert error.code == "VALIDATION_ERROR"
        assert error.status_code == 400

    def test_with_details(self) -> None:
        """Should accept validation details."""
        error = ValidationError(
            "Validation failed",
            details={"email": ["Invalid format"], "subject": ["Required"]},
        )
        assert error.details == {"email": ["Invalid format"], "subject": ["Required"]}

    def test_inheritance(self) -> None:
        """Should inherit from MailBreezeError."""
        error = ValidationError("Test")
        assert isinstance(error, MailBreezeError)


class TestNotFoundError:
    """Tests for NotFoundError class."""

    def test_default_values(self) -> None:
        """Should have correct defaults."""
        error = NotFoundError("Email not found")
        assert error.message == "Email not found"
        assert error.code == "NOT_FOUND"
        assert error.status_code == 404

    def test_inheritance(self) -> None:
        """Should inherit from MailBreezeError."""
        error = NotFoundError("Test")
        assert isinstance(error, MailBreezeError)


class TestRateLimitError:
    """Tests for RateLimitError class."""

    def test_default_values(self) -> None:
        """Should have correct defaults."""
        error = RateLimitError("Too many requests")
        assert error.message == "Too many requests"
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert error.status_code == 429
        assert error.retry_after is None

    def test_with_retry_after(self) -> None:
        """Should accept retry_after value."""
        error = RateLimitError("Too many requests", retry_after=60)
        assert error.retry_after == 60

    def test_to_dict_includes_retry_after(self) -> None:
        """Should include retry_after in dict."""
        error = RateLimitError("Too many requests", retry_after=30)
        result = error.to_dict()
        assert result["retry_after"] == 30

    def test_inheritance(self) -> None:
        """Should inherit from MailBreezeError."""
        error = RateLimitError("Test")
        assert isinstance(error, MailBreezeError)


class TestServerError:
    """Tests for ServerError class."""

    def test_default_values(self) -> None:
        """Should have correct defaults."""
        error = ServerError("Internal server error")
        assert error.message == "Internal server error"
        assert error.code == "SERVER_ERROR"
        assert error.status_code == 500

    def test_custom_status_code(self) -> None:
        """Should accept custom 5xx status code."""
        error = ServerError("Service unavailable", status_code=503)
        assert error.status_code == 503

    def test_inheritance(self) -> None:
        """Should inherit from MailBreezeError."""
        error = ServerError("Test")
        assert isinstance(error, MailBreezeError)


class TestCreateErrorFromResponse:
    """Tests for create_error_from_response factory function."""

    def test_400_creates_validation_error(self) -> None:
        """Should create ValidationError for 400."""
        error = create_error_from_response(
            status_code=400,
            body={"code": "INVALID_EMAIL", "message": "Invalid email format"},
        )
        assert isinstance(error, ValidationError)
        assert error.message == "Invalid email format"
        assert error.code == "INVALID_EMAIL"

    def test_401_creates_authentication_error(self) -> None:
        """Should create AuthenticationError for 401."""
        error = create_error_from_response(
            status_code=401,
            body={"code": "INVALID_API_KEY", "message": "Invalid API key"},
        )
        assert isinstance(error, AuthenticationError)
        assert error.message == "Invalid API key"

    def test_404_creates_not_found_error(self) -> None:
        """Should create NotFoundError for 404."""
        error = create_error_from_response(
            status_code=404,
            body={"code": "EMAIL_NOT_FOUND", "message": "Email not found"},
        )
        assert isinstance(error, NotFoundError)
        assert error.message == "Email not found"

    def test_429_creates_rate_limit_error(self) -> None:
        """Should create RateLimitError for 429."""
        error = create_error_from_response(
            status_code=429,
            body={"code": "RATE_LIMIT", "message": "Too many requests"},
            retry_after=60,
        )
        assert isinstance(error, RateLimitError)
        assert error.retry_after == 60

    def test_500_creates_server_error(self) -> None:
        """Should create ServerError for 500."""
        error = create_error_from_response(
            status_code=500,
            body={"code": "INTERNAL_ERROR", "message": "Internal error"},
        )
        assert isinstance(error, ServerError)
        assert error.status_code == 500

    def test_502_creates_server_error(self) -> None:
        """Should create ServerError for 502."""
        error = create_error_from_response(
            status_code=502,
            body={"message": "Bad gateway"},
        )
        assert isinstance(error, ServerError)
        assert error.status_code == 502

    def test_unknown_status_creates_base_error(self) -> None:
        """Should create MailBreezeError for unknown status."""
        error = create_error_from_response(
            status_code=418,
            body={"message": "I'm a teapot"},
        )
        assert type(error) is MailBreezeError
        assert error.status_code == 418

    def test_handles_none_body(self) -> None:
        """Should handle None body gracefully."""
        error = create_error_from_response(status_code=500, body=None)
        assert error.message == "Unknown error"
        assert error.code == "UNKNOWN_ERROR"

    def test_handles_empty_body(self) -> None:
        """Should handle empty body gracefully."""
        error = create_error_from_response(status_code=500, body={})
        assert error.message == "Unknown error"
        assert error.code == "UNKNOWN_ERROR"

    def test_includes_request_id(self) -> None:
        """Should include request_id when provided."""
        error = create_error_from_response(
            status_code=400,
            body={"message": "Error"},
            request_id="req_xyz",
        )
        assert error.request_id == "req_xyz"

    def test_includes_details(self) -> None:
        """Should include details from body."""
        error = create_error_from_response(
            status_code=400,
            body={
                "message": "Validation failed",
                "code": "VALIDATION_ERROR",
                "details": {"email": "invalid"},
            },
        )
        assert error.details == {"email": "invalid"}
