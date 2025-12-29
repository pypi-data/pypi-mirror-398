"""Contact and list types."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ContactStatus(str, Enum):
    """Contact subscription status."""

    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    SUPPRESSED = "suppressed"


class ConsentType(str, Enum):
    """Type of consent obtained from the contact (NDPR compliance)."""

    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    LEGITIMATE_INTEREST = "legitimate_interest"


class Contact(BaseModel):
    """Contact object."""

    model_config = ConfigDict(extra="allow")

    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    status: ContactStatus
    custom_fields: dict[str, Any] | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    consent_type: ConsentType | None = None
    consent_source: str | None = None
    consent_timestamp: datetime | None = None
    consent_ip_address: str | None = None


class CreateContactParams(BaseModel):
    """Parameters for creating a contact."""

    model_config = ConfigDict(extra="forbid")

    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    custom_fields: dict[str, Any] | None = None
    source: str | None = None
    consent_type: ConsentType | None = None
    consent_source: str | None = None
    consent_timestamp: datetime | None = None
    consent_ip_address: str | None = None


class UpdateContactParams(BaseModel):
    """Parameters for updating a contact."""

    model_config = ConfigDict(extra="forbid")

    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    custom_fields: dict[str, Any] | None = None
    consent_type: ConsentType | None = None
    consent_source: str | None = None
    consent_timestamp: datetime | None = None
    consent_ip_address: str | None = None


class ListContactsParams(BaseModel):
    """Parameters for listing contacts."""

    model_config = ConfigDict(extra="forbid")

    status: ContactStatus | None = None
    page: int | None = None
    limit: int | None = None
    search: str | None = None


class ContactList(BaseModel):
    """Contact list object."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str | None = None
    contact_count: int
    created_at: datetime
    updated_at: datetime | None = None


class CreateContactListParams(BaseModel):
    """Parameters for creating a contact list."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None


class UpdateContactListParams(BaseModel):
    """Parameters for updating a contact list."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None


class ListContactListsParams(BaseModel):
    """Parameters for listing contact lists."""

    model_config = ConfigDict(extra="forbid")

    page: int | None = None
    limit: int | None = None
    search: str | None = None


class ContactListStats(BaseModel):
    """Contact list statistics."""

    model_config = ConfigDict(extra="allow")

    total: int
    active: int
    unsubscribed: int
    bounced: int
    complained: int
