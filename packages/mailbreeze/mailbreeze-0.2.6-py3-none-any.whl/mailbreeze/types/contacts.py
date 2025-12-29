"""Contact and list types."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    email: str
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    status: ContactStatus | str  # API may return string values
    custom_fields: dict[str, Any] | None = Field(default=None, alias="customFields")
    source: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    consent_type: ConsentType | None = Field(default=None, alias="consentType")
    consent_source: str | None = Field(default=None, alias="consentSource")
    consent_timestamp: datetime | None = Field(default=None, alias="consentTimestamp")
    consent_ip_address: str | None = Field(default=None, alias="consentIpAddress")


class CreateContactParams(BaseModel):
    """Parameters for creating a contact."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    email: str
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    custom_fields: dict[str, Any] | None = Field(default=None, alias="customFields")
    source: str | None = None
    consent_type: ConsentType | None = Field(default=None, alias="consentType")
    consent_source: str | None = Field(default=None, alias="consentSource")
    consent_timestamp: datetime | None = Field(default=None, alias="consentTimestamp")
    consent_ip_address: str | None = Field(default=None, alias="consentIpAddress")


class UpdateContactParams(BaseModel):
    """Parameters for updating a contact."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    email: str | None = None
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    custom_fields: dict[str, Any] | None = Field(default=None, alias="customFields")
    consent_type: ConsentType | None = Field(default=None, alias="consentType")
    consent_source: str | None = Field(default=None, alias="consentSource")
    consent_timestamp: datetime | None = Field(default=None, alias="consentTimestamp")
    consent_ip_address: str | None = Field(default=None, alias="consentIpAddress")


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
    contact_count: int = 0
    created_at: datetime | None = None
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

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    total_contacts: int = Field(default=0, alias="totalContacts")
    active_contacts: int = Field(default=0, alias="activeContacts")
    unsubscribed_contacts: int = Field(default=0, alias="unsubscribedContacts")
    bounced_contacts: int = Field(default=0, alias="bouncedContacts")
    complained_contacts: int = Field(default=0, alias="complainedContacts")
    suppressed_contacts: int = Field(default=0, alias="suppressedContacts")
