"""
Payment functions - PayPal integration.

Usage:
    from apex.payments import create_order, capture_order
    # Or use paypal namespace
    from apex.payments import paypal
    
    # Set client once
    from apex import Client, set_default_client
    client = Client(database_url="...", user_model=User)
    set_default_client(client)
    
    # Use functions directly (no await, no client parameter)
    order = create_order(amount=99.99, currency="USD")
    capture = capture_order(order_id=order['order_id'])
    
    # Or via paypal namespace
    order = paypal.create_order(amount=99.99, currency="USD")
"""

from typing import Optional, Dict, Any
import logging

from apex.client import Client
from apex.sync import set_default_client as _set_default_client
from apex.core.exceptions import (
    ApexError,
    ClientError,
    ExternalServiceError,
    ValidationError,
)
from apex.core.validation import (
    validate_positive_number,
    validate_string,
)
from apex.infrastructure.paypal.exceptions import PayPalError


def set_client(client: Client) -> None:
    """Set the default client for payment operations."""
    _set_default_client(client)


def create_order(
    amount: float,
    currency: str = "USD",
    description: Optional[str] = None,
    return_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    save_to_db: bool = False,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Create a PayPal order.
    
    Args:
        amount: Order amount
        currency: Currency code (default: USD)
        description: Order description
        return_url: URL to redirect after approval (optional)
        cancel_url: URL to redirect if cancelled (optional)
        save_to_db: Whether to save payment record to database (default: False)
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Order data with payment information
    
    Example:
        from apex.payments import create_order
        order = create_order(amount=99.99, currency="USD", description="Premium Plan")
    """
    from apex.sync import _client, _run

    try:
        amount = validate_positive_number(amount, "amount")
        currency = validate_string(currency, "currency", min_length=3, max_length=3).upper()
        if description:
            description = validate_string(description, "description", max_length=1000)

        c = _client(client)

        async def _create():
            return await c.payments.create_order(
                amount=amount,
                currency=currency,
                description=description,
                return_url=return_url,
                cancel_url=cancel_url,
                save_to_db=save_to_db,
            )

        return _run(_create())

    except ValidationError:
        raise
    except PayPalError as e:
        raise ExternalServiceError(
            f"PayPal error: {str(e)}", details={"service": "paypal", "original_error": str(e)}
        )
    except ClientError:
        raise
    except Exception as e:
        logging.error(f"Unexpected error creating order: {e}", exc_info=True)
        raise ExternalServiceError(f"Order creation failed: {str(e)}")


def capture_order(
    order_id: str,
    update_db: bool = False,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Capture a PayPal order.
    
    Args:
        order_id: PayPal order ID
        update_db: Whether to update payment record in database (default: False)
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Capture response with payment information
    
    Example:
        from apex.payments import capture_order
        capture = capture_order(order_id="...")
    """
    from apex.sync import _client, _run

    try:
        order_id = validate_string(order_id, "order_id", min_length=1)
        c = _client(client)

        async def _capture():
            return await c.payments.capture_order(order_id=order_id, update_db=update_db)

        return _run(_capture())

    except ValidationError:
        raise
    except PayPalError as e:
        raise ExternalServiceError(
            f"PayPal error: {str(e)}", details={"service": "paypal", "original_error": str(e)}
        )
    except ClientError:
        raise
    except Exception as e:
        logging.error(f"Unexpected error capturing order: {e}", exc_info=True)
        raise ExternalServiceError(f"Capture failed: {str(e)}")


def get_order(
    order_id: str,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Get a PayPal order by ID.
    
    Args:
        order_id: PayPal order ID
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Order data
    
    Example:
        from apex.payments import get_order
        order = get_order(order_id="...")
    """
    from apex.sync import _client, _run

    try:
        order_id = validate_string(order_id, "order_id", min_length=1)
        c = _client(client)

        async def _get():
            return await c.payments.paypal_service.get_order(order_id)

        return _run(_get())

    except ValidationError:
        raise
    except PayPalError as e:
        raise ExternalServiceError(
            f"PayPal error: {str(e)}", details={"service": "paypal", "original_error": str(e)}
        )
    except ClientError:
        raise
    except Exception as e:
        logging.error(f"Unexpected error getting order: {e}", exc_info=True)
        raise ExternalServiceError(f"Get order failed: {str(e)}")


def create_subscription(
    plan_id: str,
    subscriber: Dict[str, Any],
    return_url: str = "https://example.com/return",
    cancel_url: str = "https://example.com/cancel",
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Create a PayPal subscription.
    
    Args:
        plan_id: Billing plan ID
        subscriber: Subscriber information (email, name, etc.)
        return_url: URL to redirect after approval
        cancel_url: URL to redirect if cancelled
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Subscription data with approval links
    
    Example:
        from apex.payments import create_subscription
        subscription = create_subscription(
            plan_id="P-...",
            subscriber={"email": "user@example.com"}
        )
    """
    from apex.sync import _client, _run

    try:
        plan_id = validate_string(plan_id, "plan_id", min_length=1)
        if not isinstance(subscriber, dict):
            raise ValidationError("subscriber must be a dict")

        c = _client(client)

        async def _create():
            return await c.payments.create_subscription(
                plan_id=plan_id,
                subscriber=subscriber,
                return_url=return_url,
                cancel_url=cancel_url
            )

        return _run(_create())

    except ValidationError:
        raise
    except PayPalError as e:
        raise ExternalServiceError(
            f"PayPal error: {str(e)}", details={"service": "paypal", "original_error": str(e)}
        )
    except ClientError:
        raise
    except Exception as e:
        logging.error(f"Unexpected error creating subscription: {e}", exc_info=True)
        raise ExternalServiceError(f"Create subscription failed: {str(e)}")


def cancel_subscription(
    subscription_id: str,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Cancel a PayPal subscription.
    
    Args:
        subscription_id: Subscription ID
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Cancellation response
    
    Example:
        from apex.payments import cancel_subscription
        result = cancel_subscription(subscription_id="I-...")
    """
    from apex.sync import _client, _run

    try:
        subscription_id = validate_string(subscription_id, "subscription_id", min_length=1)
        c = _client(client)

        async def _cancel():
            return await c.payments.cancel_subscription(subscription_id)

        return _run(_cancel())

    except ValidationError:
        raise
    except PayPalError as e:
        raise ExternalServiceError(
            f"PayPal error: {str(e)}", details={"service": "paypal", "original_error": str(e)}
        )
    except ClientError:
        raise
    except Exception as e:
        logging.error(f"Unexpected error canceling subscription: {e}", exc_info=True)
        raise ExternalServiceError(f"Cancel subscription failed: {str(e)}")


def get_subscription(
    subscription_id: str,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Get subscription details.
    
    Args:
        subscription_id: Subscription ID
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Subscription data
    
    Example:
        from apex.payments import get_subscription
        subscription = get_subscription(subscription_id="I-...")
    """
    from apex.sync import _client, _run

    try:
        subscription_id = validate_string(subscription_id, "subscription_id", min_length=1)
        c = _client(client)

        async def _get():
            return await c.payments.get_subscription(subscription_id)

        return _run(_get())

    except ValidationError:
        raise
    except PayPalError as e:
        raise ExternalServiceError(
            f"PayPal error: {str(e)}", details={"service": "paypal", "original_error": str(e)}
        )
    except ClientError:
        raise
    except Exception as e:
        logging.error(f"Unexpected error getting subscription: {e}", exc_info=True)
        raise ExternalServiceError(f"Get subscription failed: {str(e)}")


# PayPal-specific exports (for clarity)
paypal = {
    "create_order": create_order,
    "capture_order": capture_order,
    "get_order": get_order,
    "create_subscription": create_subscription,
    "cancel_subscription": cancel_subscription,
    "get_subscription": get_subscription,
}

__all__ = [
    "create_order",
    "capture_order",
    "get_order",
    "create_subscription",
    "cancel_subscription",
    "get_subscription",
    "paypal",
    "set_client",
]

