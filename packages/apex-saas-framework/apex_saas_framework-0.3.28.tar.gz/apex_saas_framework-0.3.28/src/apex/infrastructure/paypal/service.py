"""PayPal service for subscription management."""

from typing import Any

from apex.infrastructure.paypal.client import PayPalClient


class PayPalService:
    """
    PayPal service for managing subscriptions and payments.

    This service wraps the PayPal REST API v2 for subscription management.
    """

    def __init__(self, client: PayPalClient | None = None):
        """
        Initialize PayPal service.

        Args:
            client: PayPal client instance (creates new one if not provided)
        """
        self.client = client or PayPalClient()

    async def create_product(self, name: str, description: str,  type: str = "SERVICE") -> dict[str, Any]:
        """
        Create a PayPal product.

        Args:
            name: Product name
            description: Product description
            type: Product type (SERVICE, PHYSICAL, DIGITAL)

        Returns:
            Created product data
        """
        data = {
            "name": name,
            "description": description,
            "type": type,
        }

        return await self.client.request("POST", "/v1/catalogs/products", data=data)

    async def create_plan(
        self,
        product_id: str,
        name: str,
        description: str,
        billing_cycles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Create a subscription plan.

        Args:
            product_id: Product ID
            name: Plan name
            description: Plan description
            billing_cycles: Billing cycle configuration

        Returns:
            Created plan data
        """
        data = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "billing_cycles": billing_cycles,
            "payment_preferences": {
                "auto_bill_outstanding": True,
                "payment_failure_threshold": 3,
            },
        }

        return await self.client.request("POST", "/v1/billing/plans", data=data)

    async def create_subscription(
        self,
        plan_id: str,
        subscriber: dict[str, Any],
        return_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        """
        Create a subscription.

        Args:
            plan_id: Billing plan ID
            subscriber: Subscriber information
            return_url: URL to redirect after approval
            cancel_url: URL to redirect if cancelled

        Returns:
            Created subscription data with approval links
        """
        data = {
            "plan_id": plan_id,
            "subscriber": subscriber,
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "brand_name": "Your Brand",
                "user_action": "SUBSCRIBE_NOW",
            },
        }

        return await self.client.request("POST", "/v1/billing/subscriptions", data=data)

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """
        Get subscription details.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription data
        """
        return await self.client.request("GET", f"/v1/billing/subscriptions/{subscription_id}")

    async def cancel_subscription(self, subscription_id: str, reason: str = "") -> dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            reason: Cancellation reason (not sent to PayPal, kept for logging)

        Returns:
            Empty dict on success
        """
        # PayPal cancel API requires empty body
        data = {}
        return await self.client.request(
            "POST", f"/v1/billing/subscriptions/{subscription_id}/cancel", data=data
        )

    async def suspend_subscription(self, subscription_id: str, reason: str = "") -> dict[str, Any]:
        """
        Suspend a subscription.

        Args:
            subscription_id: Subscription ID
            reason: Suspension reason (not sent to PayPal, kept for logging)

        Returns:
            Empty dict on success
        """
        # PayPal suspend API requires empty body
        data = {}
        return await self.client.request(
            "POST", f"/v1/billing/subscriptions/{subscription_id}/suspend", data=data
        )

    async def activate_subscription(self, subscription_id: str, reason: str = "") -> dict[str, Any]:
        """
        Activate a suspended subscription.

        Args:
            subscription_id: Subscription ID
            reason: Activation reason (not sent to PayPal, kept for logging)

        Returns:
            Empty dict on success
        """
        # PayPal activate API requires empty body
        data = {}
        return await self.client.request(
            "POST", f"/v1/billing/subscriptions/{subscription_id}/activate", data=data
        )

    async def list_transactions(
        self,
        subscription_id: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """
        List subscription transactions.

        Args:
            subscription_id: Subscription ID
            start_date: Start date (ISO 8601 format)
            end_date: End date (ISO 8601 format)

        Returns:
            Transaction data
        """
        params = {
            "start_time": start_date,
            "end_time": end_date,
        }

        return await self.client.request(
            "GET",
            f"/v1/billing/subscriptions/{subscription_id}/transactions",
            params=params,
        )

    async def create_order(
        self,
        intent: str = "CAPTURE",
        purchase_units: list[dict[str, Any]] | None = None,
        return_url: str | None = None,
        cancel_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a PayPal order.

        Args:
            intent: Order intent (CAPTURE or AUTHORIZE)
            purchase_units: List of purchase units with amount and description
            return_url: URL to redirect after approval
            cancel_url: URL to redirect if cancelled

        Returns:
            Created order data with approval links
        """
        data = {
            "intent": intent,
            "purchase_units": purchase_units or [],
        }
        
        # Add application_context if URLs provided
        if return_url or cancel_url:
            data["application_context"] = {
                "return_url": return_url or "https://example.com/success",
                "cancel_url": cancel_url or "https://example.com/cancel",
            }

        return await self.client.request("POST", "/v2/checkout/orders", data=data)

    async def capture_order(self, order_id: str) -> dict[str, Any]:
        """
        Capture a PayPal order.

        Args:
            order_id: PayPal order ID

        Returns:
            Capture response data
        """
        return await self.client.request(
            "POST", f"/v2/checkout/orders/{order_id}/capture", data={}
        )

    async def get_order(self, order_id: str) -> dict[str, Any]:
        """
        Get order details.

        Args:
            order_id: PayPal order ID

        Returns:
            Order data
        """
        return await self.client.request("GET", f"/v2/checkout/orders/{order_id}")

