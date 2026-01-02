from dataclasses import dataclass
from typing import Dict, List, Optional, Union


@dataclass
class Attachment:
    """Email attachment with base64 encoded content."""
    filename: str
    content: str
    content_type: str


@dataclass
class SendEmailRequest:
    """Parameters for sending an email."""
    from_address: str
    to: Union[str, List[str]]
    subject: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    cc: Optional[Union[str, List[str]]] = None
    bcc: Optional[Union[str, List[str]]] = None
    reply_to: Optional[str] = None
    template_id: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    attachments: Optional[List[Attachment]] = None
    create_contact: Optional[bool] = None


@dataclass
class SendEmailResponse:
    """Response from send email API."""
    id: str
    message_id: str
    status: str
