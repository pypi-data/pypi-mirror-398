"""Attachments resource."""

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.attachments import (
    Attachment,
    UploadUrl,
)


class Attachments(BaseResource):
    """Attachments resource for managing email attachments."""

    async def create_upload(
        self,
        *,
        filename: str,
        content_type: str,
        size: int,
    ) -> UploadUrl:
        """Create a pre-signed upload URL.

        Args:
            filename: Attachment filename.
            content_type: MIME content type.
            size: File size in bytes.

        Returns:
            Upload URL details.
        """
        # API expects specific field names (matching JS SDK behavior)
        body = {
            "filename": filename,
            "contentType": content_type,
            "size": size,
        }
        data = await self._post("/attachments/presigned-url", body=body)
        return UploadUrl.model_validate(data)

    async def confirm(self, attachment_id: str) -> Attachment | None:
        """Confirm an attachment upload.

        Args:
            attachment_id: Attachment ID from create_upload.

        Returns:
            Confirmed attachment object, or None if no content returned.
        """
        data = await self._post(f"/attachments/{attachment_id}/confirm", body={})
        # API may return 204 No Content
        if data is None:
            return None
        return Attachment.model_validate(data)
