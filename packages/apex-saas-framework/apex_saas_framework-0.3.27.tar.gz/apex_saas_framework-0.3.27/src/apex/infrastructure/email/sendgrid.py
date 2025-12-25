"""SendGrid email adapter."""

from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To

from apex.core.config import get_settings
from apex.infrastructure.email.base import EmailAdapter

_missing_config_warned = False


class SendGridEmailAdapter(EmailAdapter):
    """SendGrid email adapter using SendGrid Web API v3."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ):
        """
        Initialize SendGrid email adapter.

        Args:
            api_key: SendGrid API key
            from_email: From email address
            from_name: From name (optional)
        """
        # Load settings inside __init__ to ensure env vars are set before Client init
        settings = get_settings()
        
        # Use user's variable names: SEND_GRID_API and FROM_EMAIL
        # Support both SEND_GRID_API and SENDGRID_API_KEY for compatibility
        self.api_key = api_key or settings.sendgrid_api_key
        self.from_email = from_email or settings.FROM_EMAIL
        self.from_name = from_name or settings.FROM_NAME or settings.APP_NAME
        self.enabled = bool(self.api_key and self.from_email)

        global _missing_config_warned
        if self.enabled:
            self.client = SendGridAPIClient(api_key=self.api_key)
        else:
            self.client = None
            if not _missing_config_warned:
                print(
                    "SendGridEmailAdapter disabled: set SEND_GRID_API and FROM_EMAIL in your .env file."
                )
                _missing_config_warned = True

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
    ) -> bool:
        """
        Send an email via SendGrid.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Plain text email body
            html: Optional HTML email body

        Returns:
            True if email was sent successfully

        Raises:
            Exception: If SendGrid API call fails
        """
        if not self.enabled:
            return False

        try:
            # Handle single or multiple recipients
            recipients = [to] if isinstance(to, str) else to
            to_emails = [To(email) for email in recipients]

            # Create message
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_emails,
                subject=subject,
                plain_text_content=body,
                html_content=html or body,
            )

            # Send email
            response = self.client.send(message)

            # SendGrid returns 202 for successful queuing
            if response.status_code not in [200, 201, 202]:
                # Log detailed error response
                error_body = response.body.decode('utf-8') if response.body else "No error details"
                print(f"SendGrid API error {response.status_code}: {error_body}")
                print(f"Response headers: {dict(response.headers) if hasattr(response, 'headers') else 'N/A'}")
                return False
            
            return True

        except Exception as e:
            # Log error in production with more details
            error_msg = str(e)
            # Try to get more details from the exception
            if hasattr(e, 'body'):
                try:
                    error_body = e.body.decode('utf-8') if isinstance(e.body, bytes) else str(e.body)
                    error_msg += f" | Body: {error_body}"
                except:
                    error_msg += f" | Body: {str(e.body)}"
            if hasattr(e, 'status_code'):
                error_msg += f" | Status: {e.status_code}"
            if hasattr(e, 'headers'):
                error_msg += f" | Headers: {dict(e.headers)}"
            print(f"SendGrid error: {error_msg}")
            print(f"FROM_EMAIL: {self.from_email}, API Key present: {bool(self.api_key)}")
            return False

    async def send_template_email(
        self,
        to: str | list[str],
        template_id: str,
        dynamic_data: dict,
    ) -> bool:
        """
        Send an email using a SendGrid dynamic template.

        Args:
            to: Recipient email address(es)
            template_id: SendGrid template ID
            dynamic_data: Template variables (key-value pairs)

        Returns:
            True if email was sent successfully

        Example:
            await adapter.send_template_email(
                to="user@example.com",
                template_id="d-1234567890abcdef",
                dynamic_data={
                    "user_name": "John Doe",
                    "reset_link": "https://example.com/reset?token=abc123"
                }
            )
        """
        if not self.enabled:
            return False

        try:
            recipients = [to] if isinstance(to, str) else to
            to_emails = [To(email) for email in recipients]

            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_emails,
            )

            # Set template ID and dynamic data
            message.template_id = template_id
            message.dynamic_template_data = dynamic_data

            response = self.client.send(message)
            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"SendGrid template error: {str(e)}")
            return False

    async def send_bulk_email(
        self,
        to_list: list[tuple[str, dict]],
        template_id: str,
    ) -> bool:
        """
        Send bulk emails with personalized content using SendGrid.

        Args:
            to_list: List of (email, dynamic_data) tuples
            template_id: SendGrid template ID

        Returns:
            True if all emails were queued successfully

        Example:
            await adapter.send_bulk_email(
                to_list=[
                    ("user1@example.com", {"name": "John", "code": "ABC123"}),
                    ("user2@example.com", {"name": "Jane", "code": "XYZ789"}),
                ],
                template_id="d-1234567890abcdef"
            )
        """
        if not self.enabled:
            return False

        try:
            message = Mail(from_email=(self.from_email, self.from_name))
            message.template_id = template_id

            # Add personalized recipients
            for email, data in to_list:
                personalization = {
                    "to": [To(email)],
                    "dynamic_template_data": data,
                }
                message.add_personalization(personalization)

            response = self.client.send(message)
            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"SendGrid bulk email error: {str(e)}")
            return False

