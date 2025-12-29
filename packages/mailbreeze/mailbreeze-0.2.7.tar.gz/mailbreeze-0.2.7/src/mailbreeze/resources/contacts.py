"""Contacts resource."""

from typing import Any

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.common import PaginatedResponse, PaginationMeta
from mailbreeze.types.contacts import (
    Contact,
    CreateContactParams,
    ListContactsParams,
    UpdateContactParams,
)


class Contacts(BaseResource):
    """Contacts resource for managing contacts within a list."""

    def __init__(self, client: Any, list_id: str) -> None:
        """Initialize contacts resource.

        Args:
            client: HTTP client.
            list_id: Contact list ID.
        """
        super().__init__(client)
        self._list_id = list_id

    async def create(
        self,
        *,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> Contact:
        """Create a new contact in the list.

        Args:
            email: Contact email address.
            first_name: Contact first name.
            last_name: Contact last name.
            custom_fields: Custom field values.

        Returns:
            Created contact object.
        """
        params = CreateContactParams.model_validate(
            {
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "customFields": custom_fields,
            }
        )
        data = await self._post(
            f"/api/v1/contact-lists/{self._list_id}/contacts",
            body=self._serialize_params(params),
        )
        return Contact.model_validate(data)

    async def list(
        self,
        *,
        status: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[Contact]:
        """List contacts in the list.

        Args:
            status: Filter by contact status.
            page: Page number.
            limit: Items per page.
            search: Search query.

        Returns:
            Paginated list of contacts.
        """
        params = ListContactsParams.model_validate(
            {"status": status, "page": page, "limit": limit, "search": search}
        )
        data = await self._get(
            f"/api/v1/contact-lists/{self._list_id}/contacts",
            query=self._serialize_params(params),
        )

        return PaginatedResponse(
            data=[Contact.model_validate(item) for item in data.get("data", [])],
            meta=PaginationMeta.model_validate(data.get("pagination", {})),
        )

    async def get(self, contact_id: str) -> Contact:
        """Get a contact by ID.

        Args:
            contact_id: Contact ID.

        Returns:
            Contact object.
        """
        data = await self._get(f"/api/v1/contact-lists/{self._list_id}/contacts/{contact_id}")
        return Contact.model_validate(data)

    async def update(
        self,
        contact_id: str,
        *,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> Contact:
        """Update a contact.

        Args:
            contact_id: Contact ID.
            email: New email address.
            first_name: New first name.
            last_name: New last name.
            custom_fields: New custom field values.

        Returns:
            Updated contact object.
        """
        params = UpdateContactParams.model_validate(
            {
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "customFields": custom_fields,
            }
        )
        data = await self._put(
            f"/api/v1/contact-lists/{self._list_id}/contacts/{contact_id}",
            body=self._serialize_params(params),
        )
        return Contact.model_validate(data)

    async def delete(self, contact_id: str) -> None:
        """Delete a contact.

        Args:
            contact_id: Contact ID.
        """
        await self._delete(f"/api/v1/contact-lists/{self._list_id}/contacts/{contact_id}")

    async def suppress(self, contact_id: str, reason: str = "manual") -> None:
        """Suppress a contact (add to suppression list).

        Args:
            contact_id: Contact ID.
            reason: Reason for suppression ('manual', 'bounce', 'complaint', 'unsubscribe').
        """
        await self._post(
            f"/api/v1/contact-lists/{self._list_id}/contacts/{contact_id}/suppress",
            body={"reason": reason},
        )
