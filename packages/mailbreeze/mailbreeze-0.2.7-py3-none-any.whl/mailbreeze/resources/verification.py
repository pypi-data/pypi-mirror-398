"""Email verification resource."""

from typing import TypedDict

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.common import PaginatedResponse, PaginationMeta
from mailbreeze.types.verification import (
    BatchVerificationParams,
    BatchVerificationResult,
    VerificationResult,
    VerificationStats,
)


class VerifyParams(TypedDict):
    """Parameters for verifying a single email."""

    email: str


class Verification(BaseResource):
    """Email verification resource."""

    async def verify(self, params: VerifyParams) -> VerificationResult:
        """Verify a single email address.

        Args:
            params: Object containing the email address to verify.

        Returns:
            Verification result.

        Example:
            ```python
            result = await client.verification.verify({"email": "user@example.com"})
            print(result.is_deliverable)  # True if status is 'clean' or 'valid'
            ```
        """
        data = await self._post("/api/v1/email-verification/single", body=dict(params))
        return VerificationResult.model_validate(data)

    async def batch(self, emails: list[str]) -> BatchVerificationResult:
        """Start batch verification for multiple emails.

        Args:
            emails: List of email addresses to verify.

        Returns:
            Batch verification result with verification_id.
        """
        params = BatchVerificationParams(emails=emails)
        data = await self._post(
            "/api/v1/email-verification/batch", body=self._serialize_params(params)
        )
        return BatchVerificationResult.model_validate(data)

    async def get(self, verification_id: str) -> BatchVerificationResult:
        """Get batch verification status and results.

        Args:
            verification_id: Batch verification ID.

        Returns:
            Batch verification result.
        """
        data = await self._get(
            f"/api/v1/email-verification/{verification_id}", query={"includeResults": True}
        )
        return BatchVerificationResult.model_validate(data)

    async def list(
        self,
        *,
        status: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> PaginatedResponse[BatchVerificationResult]:
        """List verification batches.

        Args:
            status: Filter by status ('pending', 'processing', 'completed', 'failed').
            page: Page number.
            limit: Items per page.

        Returns:
            Paginated list of verification batches.
        """
        query: dict[str, str | int] = {}
        if status:
            query["status"] = status
        if page:
            query["page"] = page
        if limit:
            query["limit"] = limit

        data = await self._get("/api/v1/email-verification", query=query if query else None)

        return PaginatedResponse(
            data=[BatchVerificationResult.model_validate(item) for item in data.get("data", [])],
            meta=PaginationMeta.model_validate(data.get("pagination", {})),
        )

    async def stats(self) -> VerificationStats:
        """Get verification statistics.

        Returns:
            Verification statistics.
        """
        data = await self._get("/api/v1/email-verification/stats")
        return VerificationStats.model_validate(data)
