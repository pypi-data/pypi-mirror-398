"""
Email functions - SendGrid integration.

Usage:
    from apex.email import send_email, send_bulk_email
    
    # Set client once
    from apex import Client, set_default_client
    client = Client(database_url="...", user_model=User)
    set_default_client(client)
    
    # Send emails (uses SendGrid if configured)
    send_email(to="user@example.com", subject="Hello", body="Welcome!")
    send_bulk_email(to=["user1@example.com", "user2@example.com"], subject="Newsletter", body="Updates")
"""

from typing import Optional, List

from apex.client import Client
from apex.sync import (
    send_email as _send_email,
    send_bulk_email as _send_bulk_email,
    set_default_client as _set_default_client,
)


def set_client(client: Client) -> None:
    """Set the default client for email operations."""
    _set_default_client(client)


def send_email(
    to: str,
    subject: str,
    body: Optional[str] = None,
    html: Optional[str] = None,
    client: Optional[Client] = None,
) -> bool:
    """
    Send an email via SendGrid (if configured in .env).
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body (optional)
        html: HTML body (optional)
        client: Optional client instance (uses default if not provided)
    
    Returns:
        True if sent successfully, False otherwise
    
    Example:
        from apex.email import send_email
        success = send_email(to="user@example.com", subject="Hello", body="Welcome!")
    """
    return _send_email(client=client, to=to, subject=subject, body=body, html=html)


def send_bulk_email(
    to: List[str],
    subject: str,
    body: Optional[str] = None,
    html: Optional[str] = None,
    client: Optional[Client] = None,
) -> bool:
    """
    Send email to multiple recipients via SendGrid (if configured in .env).
    
    Args:
        to: List of recipient email addresses
        subject: Email subject
        body: Plain text body (optional)
        html: HTML body (optional)
        client: Optional client instance (uses default if not provided)
    
    Returns:
        True if all emails sent successfully, False otherwise
    
    Example:
        from apex.email import send_bulk_email
        success = send_bulk_email(
            to=["user1@example.com", "user2@example.com"],
            subject="Newsletter",
            body="Check out our updates"
        )
    """
    return _send_bulk_email(client=client, to=to, subject=subject, body=body, html=html)


# SendGrid-specific exports (for clarity)
sendgrid = {
    "send_email": send_email,
    "send_bulk_email": send_bulk_email,
}

__all__ = ["send_email", "send_bulk_email", "sendgrid", "set_client"]







