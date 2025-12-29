"""Tests for HTTP client."""

import httpx
import pytest
import respx

from mailbreeze.errors import (
    AuthenticationError,
    MailBreezeError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from mailbreeze.http_client import HttpClient


class TestHttpClientInit:
    """Tests for HttpClient initialization."""

    def test_requires_api_key(self) -> None:
        """Should require api_key."""
        with pytest.raises(ValueError, match="API key is required"):
            HttpClient(api_key="")

    def test_default_base_url(self) -> None:
        """Should use default base URL."""
        client = HttpClient(api_key="sk_test_123")
        assert client.base_url == "https://api.mailbreeze.com/api/v1"

    def test_custom_base_url(self) -> None:
        """Should accept custom base URL."""
        client = HttpClient(api_key="sk_test_123", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"

    def test_removes_trailing_slash(self) -> None:
        """Should remove trailing slash from base URL."""
        client = HttpClient(api_key="sk_test_123", base_url="https://api.example.com/")
        assert client.base_url == "https://api.example.com"

    def test_default_timeout(self) -> None:
        """Should have default timeout of 30 seconds."""
        client = HttpClient(api_key="sk_test_123")
        assert client.timeout == 30.0

    def test_custom_timeout(self) -> None:
        """Should accept custom timeout."""
        client = HttpClient(api_key="sk_test_123", timeout=60.0)
        assert client.timeout == 60.0


class TestHttpClientHeaders:
    """Tests for request headers."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_api_key_header(self) -> None:
        """Should set X-API-Key header."""
        route = respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("GET", "/test")

        assert route.called
        assert route.calls[0].request.headers["X-API-Key"] == "sk_test_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_bearer_auth(self) -> None:
        """Should set Authorization header when auth_style is bearer."""
        route = respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123", auth_style="bearer")
        await client.request("GET", "/test")

        assert route.calls[0].request.headers["Authorization"] == "Bearer sk_test_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_content_type(self) -> None:
        """Should set Content-Type header."""
        route = respx.post("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("POST", "/test", body={"key": "value"})

        assert route.calls[0].request.headers["Content-Type"] == "application/json"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_user_agent(self) -> None:
        """Should set User-Agent header."""
        route = respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("GET", "/test")

        assert "mailbreeze-python/" in route.calls[0].request.headers["User-Agent"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_idempotency_key(self) -> None:
        """Should set X-Idempotency-Key header when provided."""
        route = respx.post("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("POST", "/test", body={}, idempotency_key="idem_123")

        assert route.calls[0].request.headers["X-Idempotency-Key"] == "idem_123"

    @pytest.mark.asyncio
    async def test_rejects_idempotency_key_with_newlines(self) -> None:
        """Should reject idempotency key with newlines (security)."""
        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(MailBreezeError, match="Invalid idempotency key"):
            await client.request("POST", "/test", body={}, idempotency_key="idem\n123")

    @pytest.mark.asyncio
    async def test_rejects_idempotency_key_with_carriage_return(self) -> None:
        """Should reject idempotency key with carriage returns (security)."""
        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(MailBreezeError, match="Invalid idempotency key"):
            await client.request("POST", "/test", body={}, idempotency_key="idem\r123")


class TestHttpClientRequests:
    """Tests for making requests."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_request(self) -> None:
        """Should make GET request."""
        route = respx.get("https://api.mailbreeze.com/api/v1/emails").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {"id": "123"}})
        )

        client = HttpClient(api_key="sk_test_123")
        result = await client.request("GET", "/emails")

        assert route.called
        assert result == {"id": "123"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_post_request_with_body(self) -> None:
        """Should make POST request with JSON body."""
        route = respx.post("https://api.mailbreeze.com/api/v1/emails").mock(
            return_value=httpx.Response(201, json={"success": True, "data": {"id": "email_123"}})
        )

        client = HttpClient(api_key="sk_test_123")
        result = await client.request("POST", "/emails", body={"to": "user@example.com"})

        assert route.called
        assert route.calls[0].request.content == b'{"to":"user@example.com"}'
        assert result == {"id": "email_123"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_request_with_query_params(self) -> None:
        """Should append query parameters to URL."""
        route = respx.get("https://api.mailbreeze.com/api/v1/emails?page=1&limit=20").mock(
            return_value=httpx.Response(200, json={"success": True, "data": []})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("GET", "/emails", query={"page": 1, "limit": 20})

        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_204_no_content(self) -> None:
        """Should handle 204 No Content response."""
        respx.delete("https://api.mailbreeze.com/api/v1/emails/123").mock(
            return_value=httpx.Response(204)
        )

        client = HttpClient(api_key="sk_test_123")
        result = await client.request("DELETE", "/emails/123")

        assert result is None


class TestHttpClientResponseParsing:
    """Tests for response parsing."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_extracts_data_from_success_response(self) -> None:
        """Should extract data from success envelope."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                200, json={"success": True, "data": {"id": "123", "status": "active"}}
            )
        )

        client = HttpClient(api_key="sk_test_123")
        result = await client.request("GET", "/test")

        assert result == {"id": "123", "status": "active"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_raises_on_success_false(self) -> None:
        """Should raise error when success is false."""
        respx.post("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": False,
                    "error": {"code": "VALIDATION_ERROR", "message": "Invalid email"},
                },
            )
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(ValidationError) as exc_info:
            await client.request("POST", "/test", body={})

        assert exc_info.value.message == "Invalid email"


class TestHttpClientErrorHandling:
    """Tests for error handling."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_400_raises_validation_error(self) -> None:
        """Should raise ValidationError for 400."""
        respx.post("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                400,
                json={
                    "success": False,
                    "error": {
                        "code": "INVALID_EMAIL",
                        "message": "Invalid email format",
                        "details": {"email": "invalid"},
                    },
                },
            )
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(ValidationError) as exc_info:
            await client.request("POST", "/test", body={})

        assert exc_info.value.code == "INVALID_EMAIL"
        assert exc_info.value.details == {"email": "invalid"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_401_raises_authentication_error(self) -> None:
        """Should raise AuthenticationError for 401."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                401, json={"success": False, "error": {"message": "Invalid API key"}}
            )
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(AuthenticationError):
            await client.request("GET", "/test")

    @respx.mock
    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error_with_retry_after(self) -> None:
        """Should raise RateLimitError with retry_after from header."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "60"},
                json={"success": False, "error": {"message": "Too many requests"}},
            )
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(RateLimitError) as exc_info:
            await client.request("GET", "/test")

        assert exc_info.value.retry_after == 60

    @respx.mock
    @pytest.mark.asyncio
    async def test_500_raises_server_error(self) -> None:
        """Should raise ServerError for 500."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                500, json={"success": False, "error": {"message": "Internal error"}}
            )
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(ServerError):
            await client.request("GET", "/test")

    @respx.mock
    @pytest.mark.asyncio
    async def test_includes_request_id_in_error(self) -> None:
        """Should include X-Request-Id in error."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                400,
                headers={"X-Request-Id": "req_abc123"},
                json={"success": False, "error": {"message": "Error"}},
            )
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(ValidationError) as exc_info:
            await client.request("GET", "/test")

        assert exc_info.value.request_id == "req_abc123"


class TestHttpClientRetry:
    """Tests for retry logic."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_retries_on_500(self) -> None:
        """Should retry on 500 errors."""
        route = respx.get("https://api.mailbreeze.com/api/v1/test")
        route.side_effect = [
            httpx.Response(500, json={"success": False, "error": {"message": "Error"}}),
            httpx.Response(200, json={"success": True, "data": {"id": "123"}}),
        ]

        client = HttpClient(api_key="sk_test_123", max_retries=3)
        result = await client.request("GET", "/test")

        assert len(route.calls) == 2
        assert result == {"id": "123"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_does_not_retry_on_400(self) -> None:
        """Should not retry on 400 errors."""
        route = respx.post("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                400, json={"success": False, "error": {"message": "Invalid"}}
            )
        )

        client = HttpClient(api_key="sk_test_123", max_retries=3)

        with pytest.raises(ValidationError):
            await client.request("POST", "/test", body={})

        assert len(route.calls) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_exhausts_retries(self) -> None:
        """Should raise after exhausting retries."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(500, json={"success": False, "error": {"message": "Error"}})
        )

        client = HttpClient(api_key="sk_test_123", max_retries=2)

        with pytest.raises(ServerError):
            await client.request("GET", "/test")


class TestHttpClientEdgeCases:
    """Tests for edge cases and error handling."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_non_json_success_response(self) -> None:
        """Should return None for non-JSON success response."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, content=b"OK")
        )

        client = HttpClient(api_key="sk_test_123")
        result = await client.request("GET", "/test")

        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_non_json_error_response(self) -> None:
        """Should raise error for non-JSON error response."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(500, content=b"Internal Server Error")
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(ServerError) as exc_info:
            await client.request("GET", "/test")

        assert exc_info.value.message == "Unknown error"

    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_http_error_without_success_field(self) -> None:
        """Should raise error for HTTP error without success field in response."""
        respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(
                500, json={"error": {"code": "INTERNAL_ERROR", "message": "Server failed"}}
            )
        )

        client = HttpClient(api_key="sk_test_123")

        with pytest.raises(ServerError) as exc_info:
            await client.request("GET", "/test")

        assert exc_info.value.code == "INTERNAL_ERROR"

    @respx.mock
    @pytest.mark.asyncio
    async def test_path_without_leading_slash(self) -> None:
        """Should handle path without leading slash."""
        route = respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("GET", "test")  # No leading slash

        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_query_params_not_added(self) -> None:
        """Should not add query string for empty query params."""
        route = respx.get("https://api.mailbreeze.com/api/v1/test").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("GET", "/test", query={})

        assert route.called
        assert "?" not in str(route.calls[0].request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_query_params_with_none_values_filtered(self) -> None:
        """Should filter out None values from query params."""
        route = respx.get("https://api.mailbreeze.com/api/v1/test?page=1").mock(
            return_value=httpx.Response(200, json={"success": True, "data": {}})
        )

        client = HttpClient(api_key="sk_test_123")
        await client.request("GET", "/test", query={"page": 1, "filter": None})

        assert route.called


class TestHttpClientCleanup:
    """Tests for resource cleanup."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self) -> None:
        """Should close underlying httpx client."""
        client = HttpClient(api_key="sk_test_123")
        await client.close()

        assert client._client.is_closed

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as async context manager."""
        async with HttpClient(api_key="sk_test_123") as client:
            assert not client._client.is_closed

        assert client._client.is_closed
