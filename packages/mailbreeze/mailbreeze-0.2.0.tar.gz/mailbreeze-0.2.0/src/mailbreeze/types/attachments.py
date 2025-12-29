"""Attachment types."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateUploadParams(BaseModel):
    """Parameters for creating an upload URL."""

    model_config = ConfigDict(extra="forbid")

    filename: str
    content_type: str
    size: int


class UploadUrl(BaseModel):
    """Upload URL response."""

    model_config = ConfigDict(extra="allow")

    attachment_id: str
    upload_url: str
    expires_at: datetime


class ConfirmUploadParams(BaseModel):
    """Parameters for confirming an upload."""

    model_config = ConfigDict(extra="forbid")

    attachment_id: str


class Attachment(BaseModel):
    """Confirmed attachment object."""

    model_config = ConfigDict(extra="allow")

    id: str
    filename: str
    content_type: str
    size: int
    status: str
    created_at: datetime
