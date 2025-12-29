"""HTTP client for MailBreeze API.

Handles authentication, retries, timeouts, and error mapping.
"""

import asyncio
import re
from typing import Any

import httpx

from mailbreeze.errors import (
    MailBreezeError,
    RateLimitError,
    create_error_from_response,
)

__version__ = "0.1.0"

DEFAULT_BASE_URL = "https://api.mailbreeze.com/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class HttpClient:
    """HTTP client for making requests to the MailBreeze API.

    Handles authentication, retries, timeouts, and error mapping.

    Args:
        api_key: MailBreeze API key.
        base_url: API base URL. Defaults to https://api.mailbreeze.com.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum retry attempts for retryable errors. Defaults to 3.
        auth_style: Authentication style - "header" (X-API-Key) or "bearer".
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        auth_style: str = "header",
    ) -> None:
        if not api_key:
            raise ValueError("API key is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.auth_style = auth_style
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API path (will be appended to base_url).
            body: Request body for POST/PUT/PATCH requests.
            query: Query parameters.
            idempotency_key: Idempotency key for request deduplication.

        Returns:
            Parsed response data.

        Raises:
            MailBreezeError: On API errors.
        """
        url = self._build_url(path, query)
        headers = self._build_headers(idempotency_key)

        last_error: MailBreezeError | None = None
        attempt = 0
        max_attempts = self.max_retries + 1

        while attempt < max_attempts:
            attempt += 1

            try:
                response = await self._execute_request(method, url, headers, body)
                return await self._handle_response(response)
            except MailBreezeError as e:
                last_error = e

                # Don't retry on client errors (4xx except 429)
                if not self._is_retryable(e):
                    raise

                # Check if we have retries left
                if attempt >= max_attempts:
                    raise

                # Calculate delay and wait
                delay = self._get_retry_delay(e, attempt)
                await asyncio.sleep(delay)

        # This should never be reached, but satisfies type checker
        if last_error:  # pragma: no cover
            raise last_error  # pragma: no cover
        raise MailBreezeError(
            "Unexpected error during request", "UNEXPECTED_ERROR"
        )  # pragma: no cover

    async def _execute_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> httpx.Response:
        """Execute the HTTP request."""
        kwargs: dict[str, Any] = {"headers": headers}

        if body is not None and method not in ("GET", "HEAD"):
            kwargs["json"] = body

        return await self._client.request(method, url, **kwargs)

    async def _handle_response(self, response: httpx.Response) -> Any:
        """Handle the HTTP response and extract data."""
        request_id = response.headers.get("X-Request-Id")
        retry_after_header = response.headers.get("Retry-After")
        retry_after = int(retry_after_header) if retry_after_header else None

        # Handle 204 No Content
        if response.status_code == 204:
            return None

        # Parse JSON body
        try:
            data = response.json()
        except Exception:
            if not response.is_success:
                raise create_error_from_response(
                    status_code=response.status_code,
                    body=None,
                    request_id=request_id,
                ) from None
            return None

        # Handle API error in body
        if not data.get("success", True):
            error_body = data.get("error", {})
            # Use 400 as default for success: false with ok response
            status_code = response.status_code if not response.is_success else 400
            raise create_error_from_response(
                status_code=status_code,
                body=error_body,
                request_id=request_id,
                retry_after=retry_after,
            )

        # Handle HTTP error even if success field is missing
        if not response.is_success:
            raise create_error_from_response(
                status_code=response.status_code,
                body=data.get("error"),
                request_id=request_id,
                retry_after=retry_after,
            )

        return data.get("data")

    def _build_url(self, path: str, query: dict[str, Any] | None = None) -> str:
        """Build the full URL with query parameters."""
        # Ensure path starts with /
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{normalized_path}"

        if query:
            params = httpx.QueryParams({k: v for k, v in query.items() if v is not None})
            if params:
                url = f"{url}?{params}"

        return url

    def _build_headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        """Build request headers."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": f"mailbreeze-python/{__version__}",
        }

        # Authentication
        if self.auth_style == "bearer":
            headers["Authorization"] = f"Bearer {self._api_key}"
        else:
            headers["X-API-Key"] = self._api_key

        # Idempotency key - validate to prevent header injection
        if idempotency_key:
            if re.search(r"[\r\n]", idempotency_key):
                raise MailBreezeError(
                    "Invalid idempotency key: contains invalid characters",
                    "INVALID_IDEMPOTENCY_KEY",
                )
            headers["X-Idempotency-Key"] = idempotency_key

        return headers

    def _is_retryable(self, error: MailBreezeError) -> bool:
        """Check if the error is retryable."""
        # Retry on 429 (rate limit) and 5xx (server errors)
        return error.status_code == 429 or (
            error.status_code is not None and error.status_code >= 500
        )

    def _get_retry_delay(self, error: MailBreezeError, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        # Use Retry-After header if available (for rate limits)
        if isinstance(error, RateLimitError) and error.retry_after:
            return float(error.retry_after)

        # Exponential backoff: 1s, 2s, 4s, 8s...
        return float(2 ** (attempt - 1))

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "HttpClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()
