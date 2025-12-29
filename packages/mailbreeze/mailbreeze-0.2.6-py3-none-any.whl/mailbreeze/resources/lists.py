"""Lists resource."""

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.common import PaginatedResponse, PaginationMeta
from mailbreeze.types.contacts import (
    ContactList,
    ContactListStats,
    CreateContactListParams,
    ListContactListsParams,
    UpdateContactListParams,
)


class Lists(BaseResource):
    """Lists resource for managing contact lists."""

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> ContactList:
        """Create a new contact list.

        Args:
            name: List name.
            description: List description.

        Returns:
            Created list object.
        """
        params = CreateContactListParams(name=name, description=description)
        data = await self._post("/contact-lists", body=self._serialize_params(params))
        return ContactList.model_validate(data)

    async def list(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[ContactList]:
        """List all contact lists.

        Args:
            page: Page number.
            limit: Items per page.
            search: Search query.

        Returns:
            Paginated list of contact lists.
        """
        params = ListContactListsParams(page=page, limit=limit, search=search)
        data = await self._get("/contact-lists", query=self._serialize_params(params))

        # Handle both array and paginated object responses (like JS SDK's extractPaginatedList)
        if isinstance(data, list):
            return PaginatedResponse(
                data=[ContactList.model_validate(item) for item in data],
                meta=PaginationMeta.model_validate(
                    {
                        "page": 1,
                        "limit": len(data),
                        "total": len(data),
                        "totalPages": 1,
                        "hasNext": False,
                        "hasPrev": False,
                    }
                ),
            )

        return PaginatedResponse(
            data=[ContactList.model_validate(item) for item in data.get("data", [])],
            meta=PaginationMeta.model_validate(data.get("pagination", {})),
        )

    async def get(self, list_id: str) -> ContactList:
        """Get a contact list by ID.

        Args:
            list_id: List ID.

        Returns:
            Contact list object.
        """
        data = await self._get(f"/contact-lists/{list_id}")
        return ContactList.model_validate(data)

    async def update(
        self,
        list_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> ContactList:
        """Update a contact list.

        Args:
            list_id: List ID.
            name: New name.
            description: New description.

        Returns:
            Updated list object.
        """
        params = UpdateContactListParams(name=name, description=description)
        data = await self._put(f"/contact-lists/{list_id}", body=self._serialize_params(params))
        return ContactList.model_validate(data)

    async def delete(self, list_id: str) -> None:
        """Delete a contact list.

        Args:
            list_id: List ID.
        """
        await self._delete(f"/contact-lists/{list_id}")

    async def stats(self, list_id: str) -> ContactListStats:
        """Get contact list statistics.

        Args:
            list_id: List ID.

        Returns:
            List statistics.
        """
        data = await self._get(f"/contact-lists/{list_id}/stats")
        return ContactListStats.model_validate(data)
