"""Attachment types."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateUploadParams(BaseModel):
    """Parameters for creating an upload URL."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    filename: str = Field(alias="fileName")
    content_type: str = Field(alias="contentType")
    size: int = Field(alias="fileSize")


class UploadUrl(BaseModel):
    """Upload URL response."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    attachment_id: str = Field(alias="attachmentId")
    upload_url: str = Field(alias="uploadUrl")
    upload_token: str | None = Field(default=None, alias="uploadToken")
    expires_at: datetime = Field(alias="expiresAt")


class ConfirmUploadParams(BaseModel):
    """Parameters for confirming an upload."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    attachment_id: str = Field(alias="attachmentId")


class Attachment(BaseModel):
    """Confirmed attachment object."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    filename: str = Field(alias="fileName")
    content_type: str = Field(alias="contentType")
    size: int = Field(alias="fileSize")
    status: str
    created_at: datetime = Field(alias="createdAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
