"""Email functionality stories: every sending scenario a single verse.

Verify that the mail wrapper correctly integrates btx_lib_mail with the
application's configuration system and provides a clean interface for
email operations.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bitranox_template_cli_app_config_log_mail.mail import (
    EmailConfig,
    load_email_config_from_dict,
    send_email,
    send_notification,
)


# ======================== EmailConfig Default Values ========================


@pytest.mark.os_agnostic
def test_email_config_provides_sensible_defaults() -> None:
    """When no values provided, EmailConfig uses safe defaults."""
    config = EmailConfig()

    assert config.smtp_hosts == []
    assert config.from_address == "noreply@localhost"
    assert config.smtp_username is None
    assert config.smtp_password is None
    assert config.use_starttls is True
    assert config.timeout == 30.0
    assert config.raise_on_missing_attachments is True
    assert config.raise_on_invalid_recipient is True


@pytest.mark.os_agnostic
def test_email_config_accepts_custom_values() -> None:
    """When custom values provided, EmailConfig stores them correctly."""
    config = EmailConfig(
        smtp_hosts=["smtp.example.com:587"],
        from_address="test@example.com",
        smtp_username="user",
        smtp_password="pass",
        use_starttls=False,
        timeout=60.0,
    )

    assert config.smtp_hosts == ["smtp.example.com:587"]
    assert config.from_address == "test@example.com"
    assert config.smtp_username == "user"
    assert config.smtp_password == "pass"
    assert config.use_starttls is False
    assert config.timeout == 60.0


@pytest.mark.os_agnostic
def test_email_config_is_immutable() -> None:
    """Once created, EmailConfig cannot be modified."""
    config = EmailConfig()

    with pytest.raises(AttributeError):
        config.smtp_hosts = ["new.smtp.com"]  # type: ignore[misc]


# ======================== EmailConfig Validation ========================


@pytest.mark.os_agnostic
def test_email_config_rejects_negative_timeout() -> None:
    """Negative timeout values are caught early with clear error."""
    with pytest.raises(ValueError, match="timeout must be positive"):
        EmailConfig(timeout=-5.0)


@pytest.mark.os_agnostic
def test_email_config_rejects_zero_timeout() -> None:
    """Zero timeout is rejected as it would cause immediate failures."""
    with pytest.raises(ValueError, match="timeout must be positive"):
        EmailConfig(timeout=0.0)


@pytest.mark.os_agnostic
def test_email_config_rejects_invalid_from_address() -> None:
    """From address without @ is caught early with clear error."""
    with pytest.raises(ValueError, match="from_address must contain @"):
        EmailConfig(from_address="not-an-email")


@pytest.mark.os_agnostic
def test_email_config_rejects_malformed_smtp_host_port() -> None:
    """SMTP host with invalid host:port format is rejected."""
    with pytest.raises(ValueError, match="Invalid SMTP host format"):
        EmailConfig(smtp_hosts=["smtp.test.com:587:extra"])


@pytest.mark.os_agnostic
def test_email_config_rejects_non_numeric_port() -> None:
    """Port must be a number, not text."""
    with pytest.raises(ValueError, match="Port must be numeric"):
        EmailConfig(smtp_hosts=["smtp.test.com:abc"])


@pytest.mark.os_agnostic
def test_email_config_rejects_port_above_65535() -> None:
    """Port must be within valid TCP range."""
    with pytest.raises(ValueError, match="Port must be 1-65535"):
        EmailConfig(smtp_hosts=["smtp.test.com:99999"])


@pytest.mark.os_agnostic
def test_email_config_rejects_port_below_1() -> None:
    """Port 0 is reserved and invalid."""
    with pytest.raises(ValueError, match="Port must be 1-65535"):
        EmailConfig(smtp_hosts=["smtp.test.com:0"])


@pytest.mark.os_agnostic
def test_email_config_accepts_host_without_port() -> None:
    """SMTP host without explicit port uses default."""
    config = EmailConfig(smtp_hosts=["smtp.test.com"])
    assert config.smtp_hosts == ["smtp.test.com"]


@pytest.mark.os_agnostic
def test_email_config_accepts_host_with_valid_port() -> None:
    """SMTP host with standard port is accepted."""
    config = EmailConfig(smtp_hosts=["smtp.test.com:587"])
    assert config.smtp_hosts == ["smtp.test.com:587"]


# ======================== EmailConfig Conversion ========================


@pytest.mark.os_agnostic
def test_email_config_converts_to_conf_mail() -> None:
    """to_conf_mail produces btx_lib_mail compatible configuration."""
    config = EmailConfig(
        smtp_hosts=["smtp.example.com:587"],
        smtp_username="user",
        smtp_password="pass",
        timeout=45.0,
    )

    conf = config.to_conf_mail()

    assert conf.smtphosts == ["smtp.example.com:587"]
    assert conf.smtp_username == "user"
    assert conf.smtp_password == "pass"
    assert conf.smtp_timeout == 45.0
    assert conf.smtp_use_starttls is True


# ======================== load_email_config_from_dict ========================


@pytest.mark.os_agnostic
def test_load_config_returns_defaults_when_email_section_missing() -> None:
    """Missing email section falls back to safe defaults."""
    config = load_email_config_from_dict({})

    assert config.smtp_hosts == []
    assert config.from_address == "noreply@localhost"


@pytest.mark.os_agnostic
def test_load_config_extracts_values_from_email_section() -> None:
    """Email section values are correctly extracted and typed."""
    config_dict = {
        "email": {
            "smtp_hosts": ["smtp.test.com:587"],
            "from_address": "alerts@test.com",
            "smtp_username": "testuser",
            "smtp_password": "testpass",
            "use_starttls": False,
            "timeout": 120.0,
        }
    }

    config = load_email_config_from_dict(config_dict)

    assert config.smtp_hosts == ["smtp.test.com:587"]
    assert config.from_address == "alerts@test.com"
    assert config.smtp_username == "testuser"
    assert config.smtp_password == "testpass"
    assert config.use_starttls is False
    assert config.timeout == 120.0


@pytest.mark.os_agnostic
def test_load_config_merges_partial_config_with_defaults() -> None:
    """Partial config inherits defaults for unspecified values."""
    config_dict = {
        "email": {
            "smtp_hosts": ["smtp.partial.com"],
            "from_address": "partial@test.com",
        }
    }

    config = load_email_config_from_dict(config_dict)

    assert config.smtp_hosts == ["smtp.partial.com"]
    assert config.from_address == "partial@test.com"
    assert config.smtp_username is None
    assert config.use_starttls is True


@pytest.mark.os_agnostic
def test_load_config_handles_non_dict_email_section() -> None:
    """Non-dict email section falls back to defaults."""
    config_dict = {"email": "invalid"}

    config = load_email_config_from_dict(config_dict)

    assert config.smtp_hosts == []
    assert config.from_address == "noreply@localhost"


@pytest.mark.os_agnostic
def test_load_config_uses_default_for_malformed_timeout() -> None:
    """Invalid timeout string falls back to default."""
    config_dict = {"email": {"timeout": "not_a_number"}}

    email_config = load_email_config_from_dict(config_dict)

    assert email_config.timeout == 30.0


@pytest.mark.os_agnostic
def test_load_config_uses_default_for_non_list_smtp_hosts() -> None:
    """String smtp_hosts falls back to empty list."""
    config_dict = {"email": {"smtp_hosts": "should_be_list"}}

    email_config = load_email_config_from_dict(config_dict)

    assert email_config.smtp_hosts == []


@pytest.mark.os_agnostic
def test_load_config_uses_default_for_string_boolean() -> None:
    """String boolean value falls back to default."""
    config_dict = {"email": {"use_starttls": "yes"}}

    email_config = load_email_config_from_dict(config_dict)

    assert email_config.use_starttls is True


@pytest.mark.os_agnostic
def test_load_config_preserves_empty_string_username() -> None:
    """Empty string username is preserved (current behavior)."""
    config_dict = {"email": {"smtp_username": ""}}

    email_config = load_email_config_from_dict(config_dict)

    assert email_config.smtp_username == ""


@pytest.mark.os_agnostic
def test_load_config_uses_valid_values_with_defaults_for_invalid() -> None:
    """Mixed valid/invalid config uses valid values and defaults for rest."""
    config_dict = {
        "email": {
            "smtp_hosts": ["smtp.test.com:587"],
            "from_address": "test@example.com",
            "timeout": "invalid",
            "use_starttls": "maybe",
        }
    }

    email_config = load_email_config_from_dict(config_dict)

    assert email_config.smtp_hosts == ["smtp.test.com:587"]
    assert email_config.from_address == "test@example.com"
    assert email_config.timeout == 30.0
    assert email_config.use_starttls is True


# ======================== send_email ========================


@pytest.mark.os_agnostic
def test_send_email_delivers_simple_message() -> None:
    """Basic email with required fields is sent successfully."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_includes_html_body() -> None:
    """Email with both plain text and HTML is sent as multipart."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Plain text",
            body_html="<h1>HTML</h1>",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_accepts_multiple_recipients() -> None:
    """Email can be sent to multiple recipients at once."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients=["user1@test.com", "user2@test.com"],
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_allows_sender_override() -> None:
    """from_address parameter overrides config default."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="default@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
            from_address="override@test.com",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_includes_attachments(tmp_path: Path) -> None:
    """Email with file attachments is sent successfully."""
    attachment = tmp_path / "test.txt"
    attachment.write_text("Test attachment content")

    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
            attachments=[attachment],
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_email_uses_credentials_when_provided() -> None:
    """SMTP credentials are used when configured."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        smtp_username="testuser",
        smtp_password="testpass",
    )

    with patch("smtplib.SMTP"):
        result = send_email(
            config=config,
            recipients="recipient@test.com",
            subject="Test Subject",
            body="Test body",
        )

    assert result is True


# ======================== send_notification ========================


@pytest.mark.os_agnostic
def test_send_notification_delivers_plain_text_message() -> None:
    """Notification sends plain-text email without HTML."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="alerts@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_notification(
            config=config,
            recipients="admin@test.com",
            subject="Alert",
            message="System notification",
        )

    assert result is True


@pytest.mark.os_agnostic
def test_send_notification_accepts_multiple_recipients() -> None:
    """Notification can be sent to multiple recipients."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="alerts@test.com",
    )

    with patch("smtplib.SMTP"):
        result = send_notification(
            config=config,
            recipients=["admin1@test.com", "admin2@test.com"],
            subject="Alert",
            message="System notification",
        )

    assert result is True


# ======================== Error Scenarios ========================


@pytest.mark.os_agnostic
def test_send_email_raises_when_smtp_connection_fails() -> None:
    """SMTP connection failure raises RuntimeError."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Cannot connect to SMTP server")

        with pytest.raises(RuntimeError, match="failed.*on all of following hosts"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_authentication_fails() -> None:
    """SMTP authentication failure raises RuntimeError."""
    mock_instance = MagicMock()
    mock_instance.login.side_effect = Exception("Authentication failed")

    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        smtp_username="user@test.com",
        smtp_password="wrong_password",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = mock_instance

        with pytest.raises(RuntimeError, match="failed.*on all of following hosts"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_recipient_validation_fails() -> None:
    """Invalid recipient raises RuntimeError."""
    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ValueError("Invalid recipient address")

        with pytest.raises(RuntimeError, match="following recipients failed"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_attachment_missing(tmp_path: Path) -> None:
    """Missing attachment raises FileNotFoundError when configured."""
    nonexistent = tmp_path / "nonexistent.txt"

    config = EmailConfig(
        smtp_hosts=["smtp.test.com:587"],
        from_address="sender@test.com",
        raise_on_missing_attachments=True,
    )

    with patch("smtplib.SMTP"):
        with pytest.raises(FileNotFoundError):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
                attachments=[nonexistent],
            )


@pytest.mark.os_agnostic
def test_send_email_raises_when_all_smtp_hosts_fail() -> None:
    """All SMTP hosts failing raises RuntimeError."""
    config = EmailConfig(
        smtp_hosts=["smtp1.test.com:587", "smtp2.test.com:587"],
        from_address="sender@test.com",
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = ConnectionError("Connection refused")

        with pytest.raises(RuntimeError, match="following recipients failed"):
            send_email(
                config=config,
                recipients="recipient@test.com",
                subject="Test",
                body="Hello",
            )


# ======================== Real SMTP Integration ========================


@pytest.fixture
def smtp_config_from_env() -> EmailConfig | None:
    """Load SMTP configuration from environment for integration tests."""
    import os

    smtp_server = os.getenv("TEST_SMTP_SERVER")
    email_address = os.getenv("TEST_EMAIL_ADDRESS")

    if not smtp_server or not email_address:
        pytest.skip("TEST_SMTP_SERVER or TEST_EMAIL_ADDRESS not configured in .env")

    return EmailConfig(
        smtp_hosts=[smtp_server],
        from_address=email_address,
        timeout=10.0,
    )


@pytest.mark.os_agnostic
def test_real_smtp_sends_email(smtp_config_from_env: EmailConfig | None) -> None:
    """Integration: send real email via configured SMTP server."""
    if smtp_config_from_env is None:
        pytest.skip("SMTP not configured")

    result = send_email(
        config=smtp_config_from_env,
        recipients=smtp_config_from_env.from_address,
        subject="Test Email from bitranox_template_cli_app_config_log_mail",
        body="This is a test email sent from the integration test suite.\n\nIf you receive this, the email functionality is working correctly.",
    )

    assert result is True


@pytest.mark.os_agnostic
def test_real_smtp_sends_html_email(smtp_config_from_env: EmailConfig | None) -> None:
    """Integration: send HTML email via configured SMTP server."""
    if smtp_config_from_env is None:
        pytest.skip("SMTP not configured")

    result = send_email(
        config=smtp_config_from_env,
        recipients=smtp_config_from_env.from_address,
        subject="Test HTML Email from bitranox_template_cli_app_config_log_mail",
        body="This is the plain text version.",
        body_html="<html><body><h1>Test Email</h1><p>This is a <strong>HTML</strong> test email.</p></body></html>",
    )

    assert result is True


@pytest.mark.os_agnostic
def test_real_smtp_sends_notification(smtp_config_from_env: EmailConfig | None) -> None:
    """Integration: send notification via configured SMTP server."""
    if smtp_config_from_env is None:
        pytest.skip("SMTP not configured")

    result = send_notification(
        config=smtp_config_from_env,
        recipients=smtp_config_from_env.from_address,
        subject="Test Notification from bitranox_template_cli_app_config_log_mail",
        message="This is a test notification.\n\nSystem: All tests passing!",
    )

    assert result is True
