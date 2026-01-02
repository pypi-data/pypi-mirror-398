from typing import Callable

from ..types import SendEmailRequest, SendEmailResponse


class Emails:
    """Email sending resource."""
    def __init__(self, request_fn: Callable):
        self._request = request_fn

    def send(self, request: SendEmailRequest) -> SendEmailResponse:
        """Send an email through the Mailpush API."""
        data = {
            "from": request.from_address,
            "to": request.to,
        }
        if request.subject:
            data["subject"] = request.subject
        if request.html:
            data["html"] = request.html
        if request.text:
            data["text"] = request.text
        if request.cc:
            data["cc"] = request.cc
        if request.bcc:
            data["bcc"] = request.bcc
        if request.reply_to:
            data["replyTo"] = request.reply_to
        if request.template_id:
            data["templateId"] = request.template_id
        if request.variables:
            data["variables"] = request.variables
        if request.attachments:
            data["attachments"] = [
                {
                    "filename": a.filename,
                    "content": a.content,
                    "contentType": a.content_type,
                }
                for a in request.attachments
            ]
        if request.create_contact is not None:
            data["createContact"] = request.create_contact

        result = self._request("POST", "/v1/send", data)
        return SendEmailResponse(
            id=result["id"],
            message_id=result["messageId"],
            status=result["status"],
        )
