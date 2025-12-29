"""Common types shared across resources."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    page: int = 1
    limit: int = 10
    total: int = 0
    total_pages: int = Field(default=1, alias="totalPages")
    has_next: bool = Field(default=False, alias="hasNext")
    has_prev: bool = Field(default=False, alias="hasPrev")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    model_config = ConfigDict(extra="allow")

    data: list[Any]
    meta: PaginationMeta
