"""Tests for resource classes."""

import httpx
import pytest
import respx

from mailbreeze import MailBreeze
from mailbreeze.errors import NotFoundError, ValidationError
from mailbreeze.types.attachments import Attachment, UploadUrl
from mailbreeze.types.common import PaginatedResponse
from mailbreeze.types.contacts import Contact, ContactList, ContactListStats
from mailbreeze.types.emails import EmailStats, SendEmailResult
from mailbreeze.types.verification import BatchVerificationResult, VerificationResult


# Helper to wrap response data in API format
def api_response(data: dict | list) -> dict:
    """Wrap data in API response format."""
    return {"success": True, "data": data}


class TestEmailsResource:
    """Tests for Emails resource."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_send_email(self) -> None:
        """Should send an email."""
        route = respx.post("https://api.mailbreeze.com/api/v1/emails").mock(
            return_value=httpx.Response(
                201,
                json=api_response(
                    {
                        "messageId": "msg_123",
                        "id": "email_123",
                        "status": "pending",
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.emails.send(
                from_="hello@example.com",
                to="user@example.com",
                subject="Hello",
                html="<p>Hello</p>",
            )

        assert route.called
        assert isinstance(result, SendEmailResult)
        assert result.message_id == "msg_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_send_email_with_idempotency_key(self) -> None:
        """Should include idempotency key in request."""
        route = respx.post("https://api.mailbreeze.com/api/v1/emails").mock(
            return_value=httpx.Response(
                201,
                json=api_response(
                    {
                        "messageId": "msg_123",
                        "id": "email_123",
                        "status": "pending",
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            await client.emails.send(
                from_="hello@example.com",
                to="user@example.com",
                subject="Hello",
                html="<p>Hello</p>",
                idempotency_key="unique_key_123",
            )

        assert route.calls[0].request.headers["X-Idempotency-Key"] == "unique_key_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_emails(self) -> None:
        """Should list emails with pagination."""
        respx.get("https://api.mailbreeze.com/api/v1/emails").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "data": [
                            {
                                "_id": "email_1",
                                "from": "a@example.com",
                                "to": ["b@example.com"],
                                "status": "delivered",
                                "createdAt": "2024-01-01T00:00:00Z",
                            },
                        ],
                        "pagination": {
                            "page": 1,
                            "limit": 20,
                            "total": 1,
                            "totalPages": 1,
                            "hasNext": False,
                            "hasPrev": False,
                        },
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.emails.list(page=1, limit=20)

        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        assert result.meta.total == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_email(self) -> None:
        """Should get email by ID."""
        respx.get("https://api.mailbreeze.com/api/v1/emails/email_123").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "email": {
                            "_id": "email_123",
                            "from": "a@example.com",
                            "to": ["b@example.com"],
                            "status": "delivered",
                            "createdAt": "2024-01-01T00:00:00Z",
                        },
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            email = await client.emails.get("email_123")

        assert email.id == "email_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_email_stats(self) -> None:
        """Should get email statistics."""
        respx.get("https://api.mailbreeze.com/api/v1/emails/stats").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "stats": {
                            "total": 100,
                            "sent": 95,
                            "failed": 2,
                            "transactional": 80,
                            "marketing": 20,
                            "successRate": 95.0,
                        },
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            stats = await client.emails.stats()

        assert isinstance(stats, EmailStats)
        assert stats.total == 100
        assert stats.sent == 95


class TestListsResource:
    """Tests for Lists resource."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_list(self) -> None:
        """Should create a contact list."""
        route = respx.post("https://api.mailbreeze.com/api/v1/contact-lists").mock(
            return_value=httpx.Response(
                201,
                json=api_response(
                    {
                        "id": "list_123",
                        "name": "Newsletter",
                        "description": "Weekly newsletter",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            list_ = await client.lists.create(
                name="Newsletter",
                description="Weekly newsletter",
            )

        assert route.called
        assert isinstance(list_, ContactList)
        assert list_.id == "list_123"
        assert list_.name == "Newsletter"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_lists(self) -> None:
        """Should list contact lists."""
        respx.get("https://api.mailbreeze.com/api/v1/contact-lists").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "data": [
                            {
                                "id": "list_1",
                                "name": "Newsletter",
                            },
                        ],
                        "pagination": {
                            "page": 1,
                            "limit": 20,
                            "total": 1,
                            "totalPages": 1,
                            "hasNext": False,
                            "hasPrev": False,
                        },
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.lists.list()

        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_list(self) -> None:
        """Should get list by ID."""
        respx.get("https://api.mailbreeze.com/api/v1/contact-lists/list_123").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "id": "list_123",
                        "name": "Newsletter",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            list_ = await client.lists.get("list_123")

        assert list_.id == "list_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_list(self) -> None:
        """Should update a list."""
        respx.put("https://api.mailbreeze.com/api/v1/contact-lists/list_123").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "id": "list_123",
                        "name": "Updated Newsletter",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            list_ = await client.lists.update("list_123", name="Updated Newsletter")

        assert list_.name == "Updated Newsletter"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_list(self) -> None:
        """Should delete a list."""
        route = respx.delete("https://api.mailbreeze.com/api/v1/contact-lists/list_123").mock(
            return_value=httpx.Response(204)
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            await client.lists.delete("list_123")

        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_list_stats(self) -> None:
        """Should get list statistics."""
        respx.get("https://api.mailbreeze.com/api/v1/contact-lists/list_123/stats").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "totalContacts": 100,
                        "activeContacts": 90,
                        "unsubscribedContacts": 5,
                        "bouncedContacts": 3,
                        "complainedContacts": 2,
                        "suppressedContacts": 0,
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            stats = await client.lists.stats("list_123")

        assert isinstance(stats, ContactListStats)
        assert stats.total_contacts == 100
        assert stats.active_contacts == 90


class TestContactsResource:
    """Tests for Contacts resource."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_contact(self) -> None:
        """Should create a contact."""
        route = respx.post(
            "https://api.mailbreeze.com/api/v1/contact-lists/list_123/contacts"
        ).mock(
            return_value=httpx.Response(
                201,
                json=api_response(
                    {
                        "id": "contact_123",
                        "email": "user@example.com",
                        "firstName": "John",
                        "lastName": "Doe",
                        "status": "active",
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            contacts = client.contacts("list_123")
            contact = await contacts.create(
                email="user@example.com",
                first_name="John",
                last_name="Doe",
            )

        assert route.called
        assert isinstance(contact, Contact)
        assert contact.email == "user@example.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_contacts(self) -> None:
        """Should list contacts."""
        respx.get("https://api.mailbreeze.com/api/v1/contact-lists/list_123/contacts").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "data": [
                            {
                                "id": "contact_1",
                                "email": "user@example.com",
                                "status": "active",
                                "createdAt": "2024-01-01T00:00:00Z",
                            },
                        ],
                        "pagination": {
                            "page": 1,
                            "limit": 20,
                            "total": 1,
                            "totalPages": 1,
                            "hasNext": False,
                            "hasPrev": False,
                        },
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            contacts = client.contacts("list_123")
            result = await contacts.list()

        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_contact(self) -> None:
        """Should get contact by ID."""
        respx.get(
            "https://api.mailbreeze.com/api/v1/contact-lists/list_123/contacts/contact_456"
        ).mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "id": "contact_456",
                        "email": "user@example.com",
                        "status": "active",
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            contacts = client.contacts("list_123")
            contact = await contacts.get("contact_456")

        assert contact.id == "contact_456"

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_contact(self) -> None:
        """Should update a contact."""
        respx.put(
            "https://api.mailbreeze.com/api/v1/contact-lists/list_123/contacts/contact_456"
        ).mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "id": "contact_456",
                        "email": "user@example.com",
                        "firstName": "Jane",
                        "status": "active",
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            contacts = client.contacts("list_123")
            contact = await contacts.update("contact_456", first_name="Jane")

        assert contact.first_name == "Jane"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_contact(self) -> None:
        """Should delete a contact."""
        route = respx.delete(
            "https://api.mailbreeze.com/api/v1/contact-lists/list_123/contacts/contact_456"
        ).mock(return_value=httpx.Response(204))

        async with MailBreeze(api_key="sk_test_123") as client:
            contacts = client.contacts("list_123")
            await contacts.delete("contact_456")

        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_suppress_contact(self) -> None:
        """Should suppress a contact."""
        route = respx.post(
            "https://api.mailbreeze.com/api/v1/contact-lists/list_123/contacts/contact_456/suppress"
        ).mock(return_value=httpx.Response(204))

        async with MailBreeze(api_key="sk_test_123") as client:
            contacts = client.contacts("list_123")
            await contacts.suppress("contact_456", reason="manual")

        assert route.called


class TestVerificationResource:
    """Tests for Verification resource."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_verify_email(self) -> None:
        """Should verify a single email."""
        route = respx.post("https://api.mailbreeze.com/api/v1/email-verification/single").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "email": "user@example.com",
                        "status": "clean",
                        "isValid": True,
                        "isDisposable": False,
                        "isRoleBased": False,
                        "isFreeProvider": True,
                        "mxFound": True,
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.verification.verify({"email": "user@example.com"})

        assert route.called
        assert isinstance(result, VerificationResult)
        assert result.is_valid is True
        assert result.email == "user@example.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_batch_verification(self) -> None:
        """Should start batch verification."""
        respx.post("https://api.mailbreeze.com/api/v1/email-verification/batch").mock(
            return_value=httpx.Response(
                202,
                json=api_response(
                    {
                        "verificationId": "ver_123",
                        "status": "processing",
                        "totalEmails": 2,
                        "processedEmails": 0,
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.verification.batch(["a@example.com", "b@example.com"])

        assert isinstance(result, BatchVerificationResult)
        assert result.verification_id == "ver_123"
        assert result.total_emails == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_verification_status(self) -> None:
        """Should get batch verification status."""
        respx.get("https://api.mailbreeze.com/api/v1/email-verification/ver_123").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "verificationId": "ver_123",
                        "status": "completed",
                        "totalEmails": 2,
                        "processedEmails": 2,
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.verification.get("ver_123")

        assert isinstance(result, BatchVerificationResult)
        assert result.status == "completed"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_verifications(self) -> None:
        """Should list verification batches."""
        respx.get("https://api.mailbreeze.com/api/v1/email-verification").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "data": [
                            {
                                "verificationId": "ver_1",
                                "status": "completed",
                                "totalEmails": 10,
                            },
                        ],
                        "pagination": {
                            "page": 1,
                            "limit": 20,
                            "total": 1,
                            "totalPages": 1,
                            "hasNext": False,
                            "hasPrev": False,
                        },
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.verification.list()

        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1


class TestAttachmentsResource:
    """Tests for Attachments resource."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_upload(self) -> None:
        """Should create upload URL."""
        respx.post("https://api.mailbreeze.com/api/v1/attachments/presigned-url").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "attachmentId": "att_123",
                        "uploadUrl": "https://storage.example.com/upload",
                        "expiresAt": "2024-01-01T01:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            result = await client.attachments.create_upload(
                filename="document.pdf",
                content_type="application/pdf",
                size=1024,
            )

        assert isinstance(result, UploadUrl)
        assert result.attachment_id == "att_123"
        assert "upload" in result.upload_url

    @respx.mock
    @pytest.mark.asyncio
    async def test_confirm_upload(self) -> None:
        """Should confirm upload."""
        respx.post("https://api.mailbreeze.com/api/v1/attachments/att_123/confirm").mock(
            return_value=httpx.Response(
                200,
                json=api_response(
                    {
                        "id": "att_123",
                        "fileName": "document.pdf",
                        "contentType": "application/pdf",
                        "fileSize": 1024,
                        "status": "ready",
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ),
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            attachment = await client.attachments.confirm("att_123")

        assert isinstance(attachment, Attachment)
        assert attachment.id == "att_123"
        assert attachment.status == "ready"

    @respx.mock
    @pytest.mark.asyncio
    async def test_confirm_upload_no_content(self) -> None:
        """Should handle 204 No Content response."""
        respx.post("https://api.mailbreeze.com/api/v1/attachments/att_123/confirm").mock(
            return_value=httpx.Response(204)
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            attachment = await client.attachments.confirm("att_123")

        assert attachment is None


class TestErrorHandling:
    """Tests for error handling in resources."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_not_found_error(self) -> None:
        """Should raise NotFoundError for 404."""
        respx.get("https://api.mailbreeze.com/api/v1/emails/nonexistent").mock(
            return_value=httpx.Response(
                404,
                json={
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": "Email not found"},
                },
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            with pytest.raises(NotFoundError):
                await client.emails.get("nonexistent")

    @respx.mock
    @pytest.mark.asyncio
    async def test_validation_error(self) -> None:
        """Should raise ValidationError for 400."""
        respx.post("https://api.mailbreeze.com/api/v1/emails").mock(
            return_value=httpx.Response(
                400,
                json={
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid email format",
                        "details": {"to": "Invalid email address"},
                    },
                },
            )
        )

        async with MailBreeze(api_key="sk_test_123") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.emails.send(
                    from_="hello@example.com",
                    to="invalid-email",
                    subject="Test",
                )

        assert exc_info.value.details is not None
        assert "to" in exc_info.value.details
