"""Email verification types."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class VerificationStatus(str, Enum):
    """Email verification result status."""

    VALID = "valid"
    INVALID = "invalid"
    RISKY = "risky"
    UNKNOWN = "unknown"


class VerificationResult(BaseModel):
    """Single email verification result."""

    model_config = ConfigDict(extra="allow")

    email: str
    status: VerificationStatus
    is_valid: bool
    is_disposable: bool
    is_role_based: bool
    is_free_provider: bool
    mx_found: bool
    smtp_check: bool | None = None
    suggestion: str | None = None


class BatchVerificationParams(BaseModel):
    """Parameters for batch verification."""

    model_config = ConfigDict(extra="forbid")

    emails: list[str]


class BatchVerificationResult(BaseModel):
    """Batch verification result."""

    model_config = ConfigDict(extra="allow")

    verification_id: str
    status: str
    total: int
    processed: int
    results: list[VerificationResult] | None = None
    created_at: datetime
    completed_at: datetime | None = None


class VerificationStats(BaseModel):
    """Verification statistics."""

    model_config = ConfigDict(extra="allow")

    total_verified: int
    valid_count: int
    invalid_count: int
    risky_count: int
    unknown_count: int
