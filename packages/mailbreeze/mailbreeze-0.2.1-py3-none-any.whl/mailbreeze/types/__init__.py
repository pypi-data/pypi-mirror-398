"""Type definitions for MailBreeze SDK."""

from mailbreeze.types.attachments import (
    Attachment,
    ConfirmUploadParams,
    CreateUploadParams,
    UploadUrl,
)
from mailbreeze.types.automations import (
    CancelEnrollmentResult,
    Enrollment,
    EnrollmentStatus,
    EnrollParams,
    ListEnrollmentsParams,
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
)
from mailbreeze.types.verification import (
    BatchVerificationParams,
    BatchVerificationResult,
    VerificationResult,
    VerificationStats,
    VerificationStatus,
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
    "BatchVerificationParams",
    "BatchVerificationResult",
    "VerificationResult",
    "VerificationStats",
    "VerificationStatus",
    # Automations
    "CancelEnrollmentResult",
    "Enrollment",
    "EnrollmentStatus",
    "EnrollParams",
    "ListEnrollmentsParams",
    # Attachments
    "Attachment",
    "ConfirmUploadParams",
    "CreateUploadParams",
    "UploadUrl",
]
