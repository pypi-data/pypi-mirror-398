"""Email verification types."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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
    is_valid: bool = Field(alias="isValid")
    is_disposable: bool = Field(alias="isDisposable")
    is_role_based: bool = Field(alias="isRoleBased")
    is_free_provider: bool = Field(alias="isFreeProvider")
    mx_found: bool = Field(alias="mxFound")
    smtp_check: bool | None = Field(default=None, alias="smtpCheck")
    suggestion: str | None = None


class BatchVerificationParams(BaseModel):
    """Parameters for batch verification."""

    model_config = ConfigDict(extra="forbid")

    emails: list[str]


class BatchVerificationResult(BaseModel):
    """Batch verification result."""

    model_config = ConfigDict(extra="allow")

    verification_id: str = Field(alias="verificationId")
    status: str
    total: int
    processed: int
    results: list[VerificationResult] | None = None
    created_at: datetime = Field(alias="createdAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")


class VerificationStats(BaseModel):
    """Verification statistics."""

    model_config = ConfigDict(extra="allow")

    total_verified: int = Field(alias="totalVerified")
    total_valid: int = Field(alias="totalValid")
    total_invalid: int = Field(alias="totalInvalid")
    total_unknown: int = Field(alias="totalUnknown")
    total_verifications: int = Field(alias="totalVerifications")
    valid_percentage: float = Field(alias="validPercentage")
