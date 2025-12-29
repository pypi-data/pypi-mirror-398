"""Email verification resource."""

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.verification import (
    BatchVerificationParams,
    BatchVerificationResult,
    VerificationResult,
    VerificationStats,
)


class Verification(BaseResource):
    """Email verification resource."""

    async def verify(self, email: str) -> VerificationResult:
        """Verify a single email address.

        Args:
            email: Email address to verify.

        Returns:
            Verification result.
        """
        data = await self._post("/verification/verify", body={"email": email})
        return VerificationResult.model_validate(data)

    async def batch(self, emails: list[str]) -> BatchVerificationResult:
        """Start batch verification for multiple emails.

        Args:
            emails: List of email addresses to verify.

        Returns:
            Batch verification result with verification_id.
        """
        params = BatchVerificationParams(emails=emails)
        data = await self._post("/verification/batch", body=self._serialize_params(params))
        return BatchVerificationResult.model_validate(data)

    async def get(self, verification_id: str) -> BatchVerificationResult:
        """Get batch verification status and results.

        Args:
            verification_id: Batch verification ID.

        Returns:
            Batch verification result.
        """
        data = await self._get(f"/verification/{verification_id}")
        return BatchVerificationResult.model_validate(data)

    async def stats(self) -> VerificationStats:
        """Get verification statistics.

        Returns:
            Verification statistics.
        """
        data = await self._get("/verification/stats")
        return VerificationStats.model_validate(data)
