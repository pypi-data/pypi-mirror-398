"""Base resource class for API resources."""

from typing import Any, TypeVar

from pydantic import BaseModel

from mailbreeze.http_client import HttpClient

T = TypeVar("T", bound=BaseModel)


class BaseResource:
    """Base class for API resources.

    Provides common HTTP method helpers that handle serialization
    and response parsing.
    """

    def __init__(self, client: HttpClient) -> None:
        """Initialize resource with HTTP client.

        Args:
            client: HTTP client for making requests.
        """
        self._client = client

    async def _get(
        self,
        path: str,
        query: dict[str, Any] | None = None,
    ) -> Any:
        """Make a GET request.

        Args:
            path: API path.
            query: Query parameters.

        Returns:
            Response data.
        """
        return await self._client.request("GET", path, query=query)

    async def _post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        """Make a POST request.

        Args:
            path: API path.
            body: Request body.
            idempotency_key: Idempotency key for request deduplication.

        Returns:
            Response data.
        """
        return await self._client.request("POST", path, body=body, idempotency_key=idempotency_key)

    async def _put(
        self,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """Make a PUT request.

        Args:
            path: API path.
            body: Request body.

        Returns:
            Response data.
        """
        return await self._client.request("PUT", path, body=body)

    async def _patch(
        self,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """Make a PATCH request.

        Args:
            path: API path.
            body: Request body.

        Returns:
            Response data.
        """
        return await self._client.request("PATCH", path, body=body)

    async def _delete(
        self,
        path: str,
    ) -> Any:
        """Make a DELETE request.

        Args:
            path: API path.

        Returns:
            Response data.
        """
        return await self._client.request("DELETE", path)

    def _serialize_params(self, params: BaseModel) -> dict[str, Any]:
        """Serialize Pydantic model to dict, excluding None values.

        Args:
            params: Pydantic model to serialize.

        Returns:
            Dictionary with non-None values, using aliases.
        """
        return params.model_dump(mode="json", exclude_none=True, by_alias=True)
