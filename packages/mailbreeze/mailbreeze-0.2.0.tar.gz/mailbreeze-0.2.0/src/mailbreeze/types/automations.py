"""Automation types."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class EnrollmentStatus(str, Enum):
    """Automation enrollment status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EnrollParams(BaseModel):
    """Parameters for enrolling a contact in an automation."""

    model_config = ConfigDict(extra="forbid")

    automation_id: str
    contact_id: str
    variables: dict[str, Any] | None = None


class Enrollment(BaseModel):
    """Automation enrollment object."""

    model_config = ConfigDict(extra="allow")

    id: str
    automation_id: str
    contact_id: str
    status: EnrollmentStatus
    current_step: int
    variables: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class ListEnrollmentsParams(BaseModel):
    """Parameters for listing enrollments."""

    model_config = ConfigDict(extra="forbid")

    automation_id: str | None = None
    status: EnrollmentStatus | None = None
    page: int | None = None
    limit: int | None = None


class CancelEnrollmentResult(BaseModel):
    """Result of cancelling an enrollment."""

    model_config = ConfigDict(extra="allow")

    id: str
    cancelled: bool
