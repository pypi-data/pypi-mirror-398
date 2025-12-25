"""PayPal webhook verification and processing."""

import hashlib
import hmac
from typing import Any

import httpx

from apex.core.config import get_settings
from apex.infrastructure.paypal.client import PayPalClient
from apex.infrastructure.paypal.exceptions import PayPalWebhookError

settings = get_settings()


class PayPalWebhookHandler:
    """
    PayPal webhook verification and event processing.

    Handles webhook signature verification and event processing.
    """

    def __init__(self, client: PayPalClient | None = None):
        """
        Initialize webhook handler.

        Args:
            client: PayPal client instance
        """
        self.client = client or PayPalClient()

    async def verify_webhook_signature(
        self,
        webhook_id: str,
        transmission_id: str,
        transmission_time: str,
        cert_url: str,
        auth_algo: str,
        transmission_sig: str,
        webhook_event: dict[str, Any],
    ) -> bool:
        """
        Verify PayPal webhook signature.

        Args:
            webhook_id: Webhook ID from PayPal dashboard
            transmission_id: Transmission ID from headers
            transmission_time: Transmission time from headers
            cert_url: Certificate URL from headers
            auth_algo: Auth algorithm from headers
            transmission_sig: Transmission signature from headers
            webhook_event: Full webhook event body

        Returns:
            True if signature is valid

        Raises:
            PayPalWebhookError: If verification fails
        """
        data = {
            "auth_algo": auth_algo,
            "cert_url": cert_url,
            "transmission_id": transmission_id,
            "transmission_sig": transmission_sig,
            "transmission_time": transmission_time,
            "webhook_id": webhook_id,
            "webhook_event": webhook_event,
        }

        try:
            result = await self.client.request(
                "POST", "/v1/notifications/verify-webhook-signature", data=data
            )

            verification_status = result.get("verification_status")
            return verification_status == "SUCCESS"

        except Exception as e:
            raise PayPalWebhookError(f"Webhook verification failed: {str(e)}") from e

    async def process_webhook_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Process PayPal webhook event.

        Args:
            event: Webhook event data

        Returns:
            Processing result

        Raises:
            PayPalWebhookError: If processing fails
        """
        event_type = event.get("event_type")

        # Route to appropriate handler based on event type
        if event_type == "BILLING.SUBSCRIPTION.CREATED":
            return await self._handle_subscription_created(event)
        elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
            return await self._handle_subscription_activated(event)
        elif event_type == "BILLING.SUBSCRIPTION.UPDATED":
            return await self._handle_subscription_updated(event)
        elif event_type == "BILLING.SUBSCRIPTION.EXPIRED":
            return await self._handle_subscription_expired(event)
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            return await self._handle_subscription_cancelled(event)
        elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
            return await self._handle_subscription_suspended(event)
        elif event_type == "BILLING.SUBSCRIPTION.PAYMENT.FAILED":
            return await self._handle_payment_failed(event)
        elif event_type == "PAYMENT.SALE.COMPLETED":
            return await self._handle_payment_completed(event)
        else:
            return {"status": "ignored", "event_type": event_type}

    async def _handle_subscription_created(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription created event."""
        resource = event.get("resource", {})
        subscription_id = resource.get("id")

        # Implement your business logic here
        # e.g., Update database, send notifications, etc.

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_subscription_activated(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription activated event."""
        resource = event.get("resource", {})
        subscription_id = resource.get("id")

        # Implement your business logic here

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_subscription_updated(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription updated event."""
        resource = event.get("resource", {})
        subscription_id = resource.get("id")

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_subscription_expired(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription expired event."""
        resource = event.get("resource", {})
        subscription_id = resource.get("id")

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_subscription_cancelled(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription cancelled event."""
        resource = event.get("resource", {})
        subscription_id = resource.get("id")

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_subscription_suspended(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle subscription suspended event."""
        resource = event.get("resource", {})
        subscription_id = resource.get("id")

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_payment_failed(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle payment failed event."""
        resource = event.get("resource", {})
        subscription_id = resource.get("billing_agreement_id")

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_payment_completed(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle payment completed event."""
        resource = event.get("resource", {})
        payment_id = resource.get("id")

        return {"status": "processed", "payment_id": payment_id}

