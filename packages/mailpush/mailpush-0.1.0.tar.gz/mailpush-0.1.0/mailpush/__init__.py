from .client import Mailpush
from .errors import (
    AuthenticationError,
    MailpushError,
    RateLimitError,
    ValidationError,
)
from .types import Attachment, SendEmailRequest, SendEmailResponse

__version__ = "0.1.0"

__all__ = [
    "Mailpush",
    "SendEmailRequest",
    "SendEmailResponse",
    "Attachment",
    "MailpushError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
]
