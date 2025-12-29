"""Email verification types."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VerificationResult(BaseModel):
    """Single email verification result."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    email: str
    # API returns 'clean'/'dirty' but normalize to standard values
    status: str  # 'clean', 'dirty', 'unknown', 'valid', 'invalid', 'risky'
    is_valid: bool | None = Field(default=None, alias="isValid")
    result: str | None = None  # 'valid', 'invalid', 'risky', 'unknown'
    reason: str | None = None
    cached: bool | None = None
    risk_score: int | None = Field(default=None, alias="riskScore")
    details: dict[str, Any] | None = None

    @property
    def is_deliverable(self) -> bool:
        """Check if email is deliverable based on status."""
        return self.status in ("clean", "valid")


class VerificationDetails(BaseModel):
    """Detailed verification information."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    is_free_provider: bool | None = Field(default=None, alias="isFreeProvider")
    is_disposable: bool | None = Field(default=None, alias="isDisposable")
    is_role_account: bool | None = Field(default=None, alias="isRoleAccount")
    has_mx_records: bool | None = Field(default=None, alias="hasMxRecords")
    is_spam_trap: bool | None = Field(default=None, alias="isSpamTrap")


class BatchVerificationParams(BaseModel):
    """Parameters for batch verification."""

    model_config = ConfigDict(extra="forbid")

    emails: list[str]


class BatchResults(BaseModel):
    """Batch verification results grouped by category."""

    model_config = ConfigDict(extra="allow")

    clean: list[str] = Field(default_factory=list)
    dirty: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)


class BatchVerificationResult(BaseModel):
    """Batch verification result."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Some responses may have verificationId, others may not (immediate results)
    verification_id: str | None = Field(default=None, alias="verificationId")
    id: str | None = None
    status: str = "completed"
    total_emails: int | None = Field(default=None, alias="totalEmails")
    total: int | None = None
    processed: int | None = Field(default=None, alias="processedEmails")
    credits_deducted: int | None = Field(default=None, alias="creditsDeducted")
    results: BatchResults | list[VerificationResult] | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    analytics: dict[str, int] | None = None


class VerificationStats(BaseModel):
    """Verification statistics."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    total_verified: int = Field(alias="totalVerified")
    total_valid: int = Field(alias="totalValid")
    total_invalid: int = Field(alias="totalInvalid")
    total_unknown: int = Field(alias="totalUnknown")
    total_verifications: int = Field(alias="totalVerifications")
    valid_percentage: float = Field(alias="validPercentage")
