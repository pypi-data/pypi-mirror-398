"""Email infrastructure."""

from apex.infrastructure.email.base import EmailAdapter
from apex.infrastructure.email.sendgrid import SendGridEmailAdapter
from apex.infrastructure.email.smtp import SMTPEmailAdapter
from apex.infrastructure.email.templates import (
    email_verification_template,
    password_reset_email_template,
    welcome_email_template,
)

__all__ = [
    "EmailAdapter",
    "SMTPEmailAdapter",
    "SendGridEmailAdapter",
    "password_reset_email_template",
    "welcome_email_template",
    "email_verification_template",
]

