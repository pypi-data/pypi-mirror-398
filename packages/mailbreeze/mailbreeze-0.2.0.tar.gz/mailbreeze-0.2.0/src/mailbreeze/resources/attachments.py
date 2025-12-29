"""Attachments resource."""

from mailbreeze.resources.base import BaseResource
from mailbreeze.types.attachments import (
    Attachment,
    ConfirmUploadParams,
    CreateUploadParams,
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
        params = CreateUploadParams(
            filename=filename,
            content_type=content_type,
            size=size,
        )
        data = await self._post("/attachments/upload", body=self._serialize_params(params))
        return UploadUrl.model_validate(data)

    async def confirm(self, attachment_id: str) -> Attachment:
        """Confirm an attachment upload.

        Args:
            attachment_id: Attachment ID from create_upload.

        Returns:
            Confirmed attachment object.
        """
        params = ConfirmUploadParams(attachment_id=attachment_id)
        data = await self._post("/attachments/confirm", body=self._serialize_params(params))
        return Attachment.model_validate(data)
