"""PayPal-specific exceptions."""


class PayPalError(Exception):
    """Base exception for PayPal errors."""

    pass


class PayPalAuthenticationError(PayPalError):
    """Raised when PayPal authentication fails."""

    pass


class PayPalAPIError(PayPalError):
    """Raised when PayPal API returns an error."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        """
        Initialize PayPal API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response: Full response from PayPal
        """
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class PayPalWebhookError(PayPalError):
    """Raised when webhook verification or processing fails."""

    pass

