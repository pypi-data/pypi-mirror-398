"""
Email Resource - Clerk-style email management
"""
from typing import Optional, List
from apex.client import Client
from apex.infrastructure.email.sendgrid import SendGridEmailAdapter
from apex.infrastructure.email.base import EmailAdapter


class Email:
    """
    Email resource - provides email sending capabilities
    
    Usage:
        async with client:
            # Send email
            await client.email.send(
                to="user@example.com",
                subject="Welcome!",
                body="Welcome to our platform",
                html="<h1>Welcome!</h1>"
            )
            
            # Send to multiple recipients
            await client.email.send_bulk(
                to=["user1@example.com", "user2@example.com"],
                subject="Newsletter",
                body="Check out our latest updates"
            )
    """
    
    def __init__(self, client: Client, adapter: Optional[EmailAdapter] = None):
        self.client = client
        # Use provided adapter, or create SendGrid adapter (reads from .env automatically)
        self.adapter = adapter or SendGridEmailAdapter()
    
    async def send(
        self,
        to: str,
        subject: str,
        body: Optional[str] = None,
        html: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html: HTML body
            from_email: From email (uses default if not provided)
            from_name: From name (uses default if not provided)
        
        Returns:
            True if sent successfully
        
        Raises:
            ValueError: If email adapter is not configured
        """
        if not self.adapter.enabled:
            raise ValueError(
                "Email adapter is not configured. "
                "Set SEND_GRID_API and FROM_EMAIL in environment variables."
            )
        
        # SendGrid adapter doesn't accept from_email/from_name in send_email
        # They are set during initialization from .env
        return await self.adapter.send_email(
            to=to,
            subject=subject,
            body=body or "",
            html=html
        )
    
    async def send_bulk(
        self,
        to: List[str],
        subject: str,
        body: Optional[str] = None,
        html: Optional[str] = None
    ) -> bool:
        """
        Send email to multiple recipients.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html: HTML body
        
        Returns:
            True if sent successfully
        """
        if not self.adapter.enabled:
            raise ValueError(
                "Email adapter is not configured. "
                "Set SEND_GRID_API and FROM_EMAIL in environment variables."
            )
        
        results = []
        for recipient in to:
            result = await self.adapter.send_email(
                to=recipient,
                subject=subject,
                body=body,
                html=html
            )
            results.append(result)
        
        return all(results)



