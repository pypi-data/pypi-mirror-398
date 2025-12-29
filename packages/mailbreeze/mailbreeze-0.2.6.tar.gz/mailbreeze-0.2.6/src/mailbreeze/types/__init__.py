"""Type definitions for MailBreeze SDK."""

from mailbreeze.types.attachments import (
    Attachment,
    ConfirmUploadParams,
    CreateUploadParams,
    UploadUrl,
)
from mailbreeze.types.common import (
    PaginatedResponse,
    PaginationMeta,
)
from mailbreeze.types.contacts import (
    Contact,
    ContactList,
    ContactListStats,
    ContactStatus,
    CreateContactListParams,
    CreateContactParams,
    ListContactListsParams,
    ListContactsParams,
    UpdateContactListParams,
    UpdateContactParams,
)
from mailbreeze.types.emails import (
    Email,
    EmailStats,
    EmailStatus,
    ListEmailsParams,
    SendEmailParams,
    SendEmailResult,
)
from mailbreeze.types.verification import (
    BatchResults,
    BatchVerificationParams,
    BatchVerificationResult,
    VerificationDetails,
    VerificationResult,
    VerificationStats,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "PaginationMeta",
    # Emails
    "Email",
    "EmailStats",
    "EmailStatus",
    "ListEmailsParams",
    "SendEmailParams",
    "SendEmailResult",
    # Contacts
    "Contact",
    "ContactList",
    "ContactListStats",
    "ContactStatus",
    "CreateContactParams",
    "CreateContactListParams",
    "ListContactsParams",
    "ListContactListsParams",
    "UpdateContactParams",
    "UpdateContactListParams",
    # Verification
    "BatchResults",
    "BatchVerificationParams",
    "BatchVerificationResult",
    "VerificationDetails",
    "VerificationResult",
    "VerificationStats",
    # Attachments
    "Attachment",
    "ConfirmUploadParams",
    "CreateUploadParams",
    "UploadUrl",
]
