"""Common types shared across resources."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    model_config = ConfigDict(extra="allow")

    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    model_config = ConfigDict(extra="allow")

    data: list[Any]
    meta: PaginationMeta
