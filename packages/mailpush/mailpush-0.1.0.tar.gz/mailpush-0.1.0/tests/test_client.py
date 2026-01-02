import pytest
import responses
from responses import matchers

from mailpush import (
    Attachment,
    AuthenticationError,
    Mailpush,
    MailpushError,
    RateLimitError,
    SendEmailRequest,
    ValidationError,
)


class TestMailpushClient:
    """Tests for Mailpush client initialization."""

    def test_init_with_valid_api_key(self):
        client = Mailpush("mp_live_test123")
        assert client._api_key == "mp_live_test123"
        assert client._base_url == "https://api.mailpush.app"

    def test_init_with_custom_base_url(self):
        client = Mailpush("mp_test_abc", base_url="https://custom.api.com")
        assert client._base_url == "https://custom.api.com"

    def test_init_without_api_key_raises_error(self):
        with pytest.raises(ValueError, match="API key is required"):
            Mailpush("")

    def test_init_with_invalid_api_key_format(self):
        with pytest.raises(ValueError, match="Invalid API key format"):
            Mailpush("invalid_key")


class TestEmailsSend:
    """Tests for emails.send() method."""

    @responses.activate
    def test_send_basic_email(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"id": "email_123", "messageId": "msg_456", "status": "queued"},
            status=200,
        )

        client = Mailpush("mp_live_test")
        response = client.emails.send(
            SendEmailRequest(
                from_address="sender@example.com",
                to="recipient@example.com",
                subject="Test",
                html="<p>Hello</p>",
            )
        )

        assert response.id == "email_123"
        assert response.message_id == "msg_456"
        assert response.status == "queued"

    @responses.activate
    def test_send_email_with_multiple_recipients(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"id": "email_123", "messageId": "msg_456", "status": "queued"},
            status=200,
            match=[
                matchers.json_params_matcher(
                    {
                        "from": "sender@example.com",
                        "to": ["a@example.com", "b@example.com"],
                        "cc": "cc@example.com",
                        "bcc": ["bcc@example.com"],
                        "subject": "Test",
                        "html": "<p>Hello</p>",
                    }
                )
            ],
        )

        client = Mailpush("mp_live_test")
        response = client.emails.send(
            SendEmailRequest(
                from_address="sender@example.com",
                to=["a@example.com", "b@example.com"],
                cc="cc@example.com",
                bcc=["bcc@example.com"],
                subject="Test",
                html="<p>Hello</p>",
            )
        )

        assert response.id == "email_123"

    @responses.activate
    def test_send_email_with_template(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"id": "email_123", "messageId": "msg_456", "status": "queued"},
            status=200,
            match=[
                matchers.json_params_matcher(
                    {
                        "from": "sender@example.com",
                        "to": "recipient@example.com",
                        "templateId": "tpl_abc",
                        "variables": {"name": "John"},
                    }
                )
            ],
        )

        client = Mailpush("mp_live_test")
        response = client.emails.send(
            SendEmailRequest(
                from_address="sender@example.com",
                to="recipient@example.com",
                template_id="tpl_abc",
                variables={"name": "John"},
            )
        )

        assert response.id == "email_123"

    @responses.activate
    def test_send_email_with_attachments(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"id": "email_123", "messageId": "msg_456", "status": "queued"},
            status=200,
        )

        client = Mailpush("mp_live_test")
        response = client.emails.send(
            SendEmailRequest(
                from_address="sender@example.com",
                to="recipient@example.com",
                subject="With Attachment",
                html="<p>See attached</p>",
                attachments=[
                    Attachment(
                        filename="test.pdf",
                        content="base64content",
                        content_type="application/pdf",
                    )
                ],
            )
        )

        assert response.id == "email_123"
        request_body = responses.calls[0].request.body
        assert b'"attachments"' in request_body
        assert b'"filename": "test.pdf"' in request_body


class TestErrorHandling:
    """Tests for error handling."""

    @responses.activate
    def test_authentication_error(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"error": "Unauthorized"},
            status=401,
        )

        client = Mailpush("mp_live_test")
        with pytest.raises(AuthenticationError) as exc:
            client.emails.send(
                SendEmailRequest(
                    from_address="sender@example.com",
                    to="recipient@example.com",
                    subject="Test",
                    html="<p>Test</p>",
                )
            )

        assert exc.value.code == "INVALID_API_KEY"

    @responses.activate
    def test_validation_error(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"error": "Invalid email address", "field": "to"},
            status=400,
        )

        client = Mailpush("mp_live_test")
        with pytest.raises(ValidationError) as exc:
            client.emails.send(
                SendEmailRequest(
                    from_address="sender@example.com",
                    to="invalid-email",
                    subject="Test",
                    html="<p>Test</p>",
                )
            )

        assert exc.value.code == "VALIDATION_ERROR"
        assert exc.value.details is not None

    @responses.activate
    def test_rate_limit_error(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"error": "Too many requests"},
            status=429,
            headers={"Retry-After": "60"},
        )

        client = Mailpush("mp_live_test")
        with pytest.raises(RateLimitError) as exc:
            client.emails.send(
                SendEmailRequest(
                    from_address="sender@example.com",
                    to="recipient@example.com",
                    subject="Test",
                    html="<p>Test</p>",
                )
            )

        assert exc.value.code == "RATE_LIMITED"
        assert exc.value.retry_after == 60

    @responses.activate
    def test_generic_error(self):
        responses.add(
            responses.POST,
            "https://api.mailpush.app/v1/send",
            json={"error": "Server error", "code": "INTERNAL_ERROR"},
            status=500,
        )

        client = Mailpush("mp_live_test")
        with pytest.raises(MailpushError) as exc:
            client.emails.send(
                SendEmailRequest(
                    from_address="sender@example.com",
                    to="recipient@example.com",
                    subject="Test",
                    html="<p>Test</p>",
                )
            )

        assert exc.value.code == "INTERNAL_ERROR"
