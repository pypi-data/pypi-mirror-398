"""SMTP email adapter."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import cast

from apex.core.config import get_settings
from apex.infrastructure.email.base import EmailAdapter

settings = get_settings()


class SMTPEmailAdapter(EmailAdapter):
    """SMTP email adapter."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        from_email: str | None = None,
        use_tls: bool = True,
    ):
        """
        Initialize SMTP email adapter.

        Args:
            host: SMTP host
            port: SMTP port
            user: SMTP username
            password: SMTP password
            from_email: From email address
            use_tls: Use TLS encryption
        """
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        self.from_email = from_email or settings.SMTP_FROM_EMAIL
        self.use_tls = use_tls or settings.SMTP_USE_TLS

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Plain text email body
            html: Optional HTML email body

        Returns:
            True if email was sent successfully
        """
        if not all([self.host, self.port, self.user, self.password, self.from_email]):
            raise ValueError("SMTP configuration is incomplete")

        recipients = [to] if isinstance(to, str) else to

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(body, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(self.host, cast(int, self.port)) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception:
            return False

