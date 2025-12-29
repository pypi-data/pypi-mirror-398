"""Automations resource."""

from typing import Any

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.automations import (
    CancelEnrollmentResult,
    Enrollment,
    EnrollParams,
    ListEnrollmentsParams,
)
from mailbreeze.types.common import PaginatedResponse, PaginationMeta


class Enrollments(BaseResource):
    """Enrollments sub-resource for managing automation enrollments."""

    async def list(
        self,
        *,
        automation_id: str | None = None,
        status: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> PaginatedResponse[Enrollment]:
        """List automation enrollments.

        Args:
            automation_id: Filter by automation ID.
            status: Filter by enrollment status.
            page: Page number.
            limit: Items per page.

        Returns:
            Paginated list of enrollments.
        """
        params = ListEnrollmentsParams.model_validate(
            {"automation_id": automation_id, "status": status, "page": page, "limit": limit}
        )
        data = await self._get("/automations/enrollments", query=self._serialize_params(params))

        return PaginatedResponse(
            data=[Enrollment.model_validate(item) for item in data.get("items", [])],
            meta=PaginationMeta.model_validate(data.get("meta", {})),
        )

    async def cancel(self, enrollment_id: str) -> CancelEnrollmentResult:
        """Cancel an automation enrollment.

        Args:
            enrollment_id: Enrollment ID.

        Returns:
            Cancellation result.
        """
        data = await self._post(f"/automations/enrollments/{enrollment_id}/cancel")
        return CancelEnrollmentResult.model_validate(data)


class Automations(BaseResource):
    """Automations resource for managing marketing automations."""

    @property
    def enrollments(self) -> Enrollments:
        """Access enrollments sub-resource.

        Returns:
            Enrollments resource.
        """
        return Enrollments(self._client)

    async def enroll(
        self,
        *,
        automation_id: str,
        contact_id: str,
        variables: dict[str, Any] | None = None,
    ) -> Enrollment:
        """Enroll a contact in an automation.

        Args:
            automation_id: Automation ID.
            contact_id: Contact ID to enroll.
            variables: Variables to pass to the automation.

        Returns:
            Created enrollment object.
        """
        params = EnrollParams(
            automation_id=automation_id,
            contact_id=contact_id,
            variables=variables,
        )
        data = await self._post("/automations/enroll", body=self._serialize_params(params))
        return Enrollment.model_validate(data)
