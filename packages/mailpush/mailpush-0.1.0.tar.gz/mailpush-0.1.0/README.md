# Mailpush Python SDK

Official Python SDK for the [Mailpush](https://mailpush.app) email API.

## Installation

```bash
pip install mailpush
```

## Quick Start

```python
from mailpush import Mailpush, SendEmailRequest

client = Mailpush("mp_live_xxx")

response = client.emails.send(SendEmailRequest(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Hello from Mailpush",
    html="<h1>Welcome!</h1>"
))

print(f"Email sent: {response.id}")
```

## Features

- Simple, intuitive API
- Full type hints support
- Automatic retries on rate limits
- Support for attachments
- Template support with variables

## Sending Emails

### Basic Email

```python
from mailpush import Mailpush, SendEmailRequest

client = Mailpush("mp_live_xxx")

response = client.emails.send(SendEmailRequest(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Welcome!",
    html="<h1>Hello World</h1>",
    text="Hello World"
))
```

### With Multiple Recipients

```python
response = client.emails.send(SendEmailRequest(
    from_address="hello@yourdomain.com",
    to=["user1@example.com", "user2@example.com"],
    cc="manager@example.com",
    bcc=["admin@example.com"],
    subject="Team Update",
    html="<p>Important update...</p>"
))
```

### With Attachments

```python
import base64
from mailpush import Mailpush, SendEmailRequest, Attachment

client = Mailpush("mp_live_xxx")

with open("report.pdf", "rb") as f:
    content = base64.b64encode(f.read()).decode()

response = client.emails.send(SendEmailRequest(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Your Report",
    html="<p>Please find attached your report.</p>",
    attachments=[
        Attachment(
            filename="report.pdf",
            content=content,
            content_type="application/pdf"
        )
    ]
))
```

### Using Templates

```python
response = client.emails.send(SendEmailRequest(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    template_id="welcome-template-id",
    variables={
        "name": "John",
        "company": "Acme Inc"
    }
))
```

## Error Handling

```python
from mailpush import (
    Mailpush,
    SendEmailRequest,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    MailpushError
)

client = Mailpush("mp_live_xxx")

try:
    response = client.emails.send(SendEmailRequest(
        from_address="hello@yourdomain.com",
        to="user@example.com",
        subject="Test",
        html="<p>Hello</p>"
    ))
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Validation failed: {e.details}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except MailpushError as e:
    print(f"Error: {e.code} - {e}")
```

## Configuration

### Custom Base URL

```python
client = Mailpush("mp_live_xxx", base_url="https://api.custom.com")
```

## License

MIT
