class MailpushError(Exception):
    """Base exception for Mailpush SDK errors."""
    def __init__(self, message: str, code: str, details=None):
        super().__init__(message)
        self.code = code
        self.details = details


class AuthenticationError(MailpushError):
    """Raised when API key is invalid or missing."""
    pass


class ValidationError(MailpushError):
    """Raised when request validation fails."""
    pass


class RateLimitError(MailpushError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, code: str, retry_after: int = None):
        super().__init__(message, code)
        self.retry_after = retry_after
