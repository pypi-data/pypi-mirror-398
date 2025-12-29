"""MailBreeze client - main entry point for the SDK."""

from typing import Any

from mailbreeze.http_client import HttpClient
from mailbreeze.resources.attachments import Attachments
from mailbreeze.resources.automations import Automations
from mailbreeze.resources.contacts import Contacts
from mailbreeze.resources.emails import Emails
from mailbreeze.resources.lists import Lists
from mailbreeze.resources.verification import Verification


class MailBreeze:
    """MailBreeze SDK client.

    Main entry point for interacting with the MailBreeze API.

    Example:
        ```python
        import asyncio
        from mailbreeze import MailBreeze

        async def main():
            client = MailBreeze(api_key="sk_live_xxx")

            # Send an email
            email = await client.emails.send(
                from_="hello@yourdomain.com",
                to="user@example.com",
                subject="Welcome!",
                html="<h1>Hello!</h1>",
            )
            print(email.id)

        asyncio.run(main())
        ```

    Args:
        api_key: MailBreeze API key.
        base_url: API base URL. Defaults to https://api.mailbreeze.com.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum retry attempts for retryable errors. Defaults to 3.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        """Initialize the MailBreeze client."""
        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url is not None:
            kwargs["base_url"] = base_url
        if timeout is not None:
            kwargs["timeout"] = timeout
        if max_retries is not None:
            kwargs["max_retries"] = max_retries

        self._client = HttpClient(**kwargs)

        # Initialize resources
        self.emails = Emails(self._client)
        self.lists = Lists(self._client)
        self.attachments = Attachments(self._client)
        self.verification = Verification(self._client)
        self.automations = Automations(self._client)

    def contacts(self, list_id: str) -> Contacts:
        """Get contacts resource for a specific list.

        Args:
            list_id: Contact list ID.

        Returns:
            Contacts resource scoped to the list.

        Example:
            ```python
            contacts = client.contacts("list_xxx")
            contact = await contacts.create(email="user@example.com")
            ```
        """
        return Contacts(self._client, list_id)

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._client.close()

    async def __aenter__(self) -> "MailBreeze":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()
