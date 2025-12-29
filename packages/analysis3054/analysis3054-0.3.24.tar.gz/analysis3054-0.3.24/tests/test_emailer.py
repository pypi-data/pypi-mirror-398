import os
from email.message import EmailMessage

import pytest

from analysis3054.emailer import EmailContent, _coerce_content, _normalize_recipients, send_email


class DummySMTP:
    instances: list["DummySMTP"] = []

    def __init__(self, *args, **kwargs):
        self.sent_messages: list[EmailMessage] = []
        self.login_args: tuple[str, str] | None = None
        DummySMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, message):
        self.sent_messages.append(message)


def test_coerce_content_defaults_to_html():
    content = _coerce_content("<p>Hello</p>")
    assert isinstance(content, EmailContent)
    assert content.is_html is True
    assert content.subject == "Automated message"
    assert content.body == "<p>Hello</p>"


def test_normalize_recipients_strips_and_validates():
    normalized = _normalize_recipients([" alice@example.com ", "bob@example.com"])
    assert normalized == ["alice@example.com", "bob@example.com"]

    with pytest.raises(ValueError):
        _normalize_recipients(["  "])
    with pytest.raises(TypeError):
        _normalize_recipients([123])  # type: ignore[list-item]


def test_send_email_gmail_path(monkeypatch):
    DummySMTP.instances.clear()
    monkeypatch.setenv("ANALYSIS3054_EMAIL_PROVIDER", "gmail")
    monkeypatch.setenv("GMAIL_USER", "sender@example.com")
    monkeypatch.setenv("GMAIL_PASSWORD", "app-password")
    monkeypatch.setattr("analysis3054.emailer.smtplib.SMTP_SSL", DummySMTP)

    content = {
        "subject": "Status update",
        "body": "<h1>Update</h1><p>All systems go.</p>",
        "plain_text": "Update: All systems go.",
        "is_html": True,
    }

    result = send_email(["recipient@example.com"], content, open_before_sending=False)

    assert isinstance(result, EmailMessage)
    assert DummySMTP.instances[0].login_args == ("sender@example.com", "app-password")
    assert len(DummySMTP.instances[0].sent_messages) == 1
    sent = DummySMTP.instances[0].sent_messages[0]
    assert sent["To"] == "recipient@example.com"
    assert sent.get_body(preferencelist=("html",)).get_content_type() == "text/html"
    assert "All systems go" in sent.get_body(preferencelist=("html",)).get_content()


def test_gmail_preview_mode_does_not_send(monkeypatch):
    DummySMTP.instances.clear()
    monkeypatch.setenv("ANALYSIS3054_EMAIL_PROVIDER", "gmail")
    monkeypatch.setenv("GMAIL_USER", "sender@example.com")
    monkeypatch.setenv("GMAIL_PASSWORD", "app-password")
    monkeypatch.setattr("analysis3054.emailer.smtplib.SMTP_SSL", DummySMTP)

    message = send_email(["recipient@example.com"], "Hi there", open_before_sending=True)

    assert isinstance(message, EmailMessage)
    assert DummySMTP.instances == []  # Preview mode should not open SMTP connection
    assert message.get_body(preferencelist=("html",)).get_content_type() == "text/html"
    assert "Hi there" in message.get_body(preferencelist=("html",)).get_content()

    # Clean up environment for other tests
    os.environ.pop("ANALYSIS3054_EMAIL_PROVIDER", None)
