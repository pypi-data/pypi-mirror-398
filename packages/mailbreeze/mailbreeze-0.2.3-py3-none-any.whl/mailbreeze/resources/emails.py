"""Emails resource."""

from typing import Any

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.common import PaginatedResponse, PaginationMeta
from mailbreeze.types.emails import (
    Email,
    EmailStats,
    ListEmailsParams,
    SendEmailParams,
)


class Emails(BaseResource):
    """Emails resource for sending and managing emails."""

    async def send(
        self,
        *,
        from_: str,
        to: str | list[str],
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        template_id: str | None = None,
        variables: dict[str, Any] | None = None,
        attachment_ids: list[str] | None = None,
        reply_to: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        headers: dict[str, str] | None = None,
        tags: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> Email:
        """Send an email.

        Args:
            from_: Sender email address.
            to: Recipient email address(es).
            subject: Email subject (required if not using template).
            html: HTML body content.
            text: Plain text body content.
            template_id: Template ID to use instead of subject/html/text.
            variables: Template variables.
            attachment_ids: List of attachment IDs.
            reply_to: Reply-to email address.
            cc: CC recipient(s).
            bcc: BCC recipient(s).
            headers: Custom email headers.
            tags: Tags for categorization.
            idempotency_key: Idempotency key for request deduplication.

        Returns:
            Created email object.
        """
        params = SendEmailParams.model_validate(
            {
                "from": from_,
                "to": to,
                "subject": subject,
                "html": html,
                "text": text,
                "template_id": template_id,
                "variables": variables,
                "attachment_ids": attachment_ids,
                "reply_to": reply_to,
                "cc": cc,
                "bcc": bcc,
                "headers": headers,
                "tags": tags,
            }
        )

        data = await self._post(
            "/emails",
            body=self._serialize_params(params),
            idempotency_key=idempotency_key,
        )
        return Email.model_validate(data)

    async def list(
        self,
        *,
        status: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> PaginatedResponse[Email]:
        """List emails.

        Args:
            status: Filter by email status.
            page: Page number.
            limit: Items per page.

        Returns:
            Paginated list of emails.
        """
        params = ListEmailsParams.model_validate({"status": status, "page": page, "limit": limit})
        data = await self._get("/emails", query=self._serialize_params(params))

        return PaginatedResponse(
            data=[Email.model_validate(item) for item in data.get("items", [])],
            meta=PaginationMeta.model_validate(data.get("meta", {})),
        )

    async def get(self, email_id: str) -> Email:
        """Get an email by ID.

        Args:
            email_id: Email ID.

        Returns:
            Email object.
        """
        data = await self._get(f"/emails/{email_id}")
        return Email.model_validate(data)

    async def stats(self) -> EmailStats:
        """Get email statistics.

        Returns:
            Email statistics including success rate.

        Example:
            ```python
            stats = await client.emails.stats()
            print(stats.success_rate)  # 100.0
            print(stats.total)  # 71
            ```
        """
        data = await self._get("/emails/stats")
        # Backend returns {"stats": {...}} so extract the nested object
        stats_data = data.get("stats", data)
        return EmailStats.model_validate(stats_data)
