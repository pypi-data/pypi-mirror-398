"""Email types."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EmailStatus(str, Enum):
    """Email delivery status."""

    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    FAILED = "failed"


class SendEmailParams(BaseModel):
    """Parameters for sending an email."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from")
    to: str | list[str]
    subject: str | None = None
    html: str | None = None
    text: str | None = None
    template_id: str | None = None
    variables: dict[str, Any] | None = None
    attachment_ids: list[str] | None = None
    reply_to: str | None = None
    cc: str | list[str] | None = None
    bcc: str | list[str] | None = None
    headers: dict[str, str] | None = None
    tags: list[str] | None = None


class SendEmailResult(BaseModel):
    """Result of sending an email."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    message_id: str = Field(alias="messageId")
    id: str | None = None
    status: EmailStatus | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")


class Email(BaseModel):
    """Email object returned from API."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(alias="_id")
    from_: str = Field(alias="from")
    to: list[str]
    subject: str | None = None
    status: EmailStatus | str  # API may return string values
    created_at: datetime = Field(alias="createdAt")
    sent_at: datetime | None = Field(default=None, alias="sentAt")
    delivered_at: datetime | None = Field(default=None, alias="deliveredAt")


class ListEmailsParams(BaseModel):
    """Parameters for listing emails."""

    model_config = ConfigDict(extra="forbid")

    status: EmailStatus | None = None
    page: int | None = None
    limit: int | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


class EmailStats(BaseModel):
    """Email statistics."""

    model_config = ConfigDict(extra="allow")

    total: int
    sent: int
    failed: int
    transactional: int
    marketing: int
    success_rate: float = Field(alias="successRate")
