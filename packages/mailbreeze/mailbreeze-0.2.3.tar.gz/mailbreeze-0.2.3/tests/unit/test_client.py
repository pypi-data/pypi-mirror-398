"""Tests for MailBreeze client."""

import pytest

from mailbreeze import MailBreeze
from mailbreeze.resources.attachments import Attachments
from mailbreeze.resources.contacts import Contacts
from mailbreeze.resources.emails import Emails
from mailbreeze.resources.lists import Lists
from mailbreeze.resources.verification import Verification


class TestMailBreezeClient:
    """Tests for MailBreeze client initialization."""

    def test_requires_api_key(self) -> None:
        """Should require api_key."""
        with pytest.raises(ValueError, match="API key is required"):
            MailBreeze(api_key="")

    def test_initializes_resources(self) -> None:
        """Should initialize all resource properties."""
        client = MailBreeze(api_key="sk_test_123")

        assert isinstance(client.emails, Emails)
        assert isinstance(client.lists, Lists)
        assert isinstance(client.attachments, Attachments)
        assert isinstance(client.verification, Verification)

    def test_contacts_returns_scoped_resource(self) -> None:
        """Should return contacts resource scoped to list."""
        client = MailBreeze(api_key="sk_test_123")
        contacts = client.contacts("list_123")

        assert isinstance(contacts, Contacts)
        assert contacts._list_id == "list_123"

    def test_custom_options(self) -> None:
        """Should accept custom options."""
        client = MailBreeze(
            api_key="sk_test_123",
            base_url="https://custom.api.com",
            timeout=60.0,
            max_retries=5,
        )

        assert client._client.base_url == "https://custom.api.com"
        assert client._client.timeout == 60.0
        assert client._client.max_retries == 5

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Should close underlying client."""
        client = MailBreeze(api_key="sk_test_123")
        await client.close()

        assert client._client._client.is_closed

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as async context manager."""
        async with MailBreeze(api_key="sk_test_123") as client:
            assert not client._client._client.is_closed

        assert client._client._client.is_closed
