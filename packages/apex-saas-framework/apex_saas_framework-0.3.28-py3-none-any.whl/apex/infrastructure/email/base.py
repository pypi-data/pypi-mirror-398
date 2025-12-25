"""Abstract email adapter interface."""

from abc import ABC, abstractmethod


class EmailAdapter(ABC):
    """Abstract base class for email adapters."""

    @abstractmethod
    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Plain text email body
            html: Optional HTML email body

        Returns:
            True if email was sent successfully
        """
        pass

