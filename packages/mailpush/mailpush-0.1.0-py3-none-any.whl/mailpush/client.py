from typing import Any, Dict, Optional

import requests

from .errors import (
    AuthenticationError,
    MailpushError,
    RateLimitError,
    ValidationError,
)
from .resources.emails import Emails


class Mailpush:
    """Mailpush API client."""
    DEFAULT_BASE_URL = "https://api.mailpush.app"

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Initialize the Mailpush client with an API key."""
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith("mp_"):
            raise ValueError("Invalid API key format")

        self._api_key = api_key
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self.emails = Emails(self._request)

    def _request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Mailpush API."""
        url = f"{self._base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        response = requests.request(method, url, json=data, headers=headers)

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", "INVALID_API_KEY")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limited",
                "RATE_LIMITED",
                int(retry_after) if retry_after else None,
            )
        elif response.status_code == 400:
            body = response.json()
            raise ValidationError(
                body.get("error", "Validation error"), "VALIDATION_ERROR", body
            )
        elif not response.ok:
            body = response.json()
            raise MailpushError(
                body.get("error", "Unknown error"), body.get("code", "UNKNOWN")
            )

        return response.json()
