"""PayPal Pydantic schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SubscriberName(BaseModel):
    """Subscriber name schema."""

    given_name: str
    surname: str


class SubscriberEmail(BaseModel):
    """Subscriber email schema."""

    email_address: str


class SubscriberInfo(BaseModel):
    """Subscriber information schema."""

    name: SubscriberName | None = None
    email_address: str


class CreateSubscriptionRequest(BaseModel):
    """Schema for creating a subscription."""

    plan_id: str
    subscriber_email: str
    subscriber_first_name: str
    subscriber_last_name: str
    return_url: str | None = None  # Optional - uses PAYPAL_RETURN_URL from .env if not provided
    cancel_url: str | None = None  # Optional - uses PAYPAL_CANCEL_URL from .env if not provided


class BillingCycle(BaseModel):
    """Billing cycle schema."""

    frequency: dict[str, Any]
    tenure_type: str
    sequence: int
    total_cycles: int
    pricing_scheme: dict[str, Any]


class CreatePlanRequest(BaseModel):
    """Schema for creating a billing plan."""

    product_id: str
    name: str
    description: str
    billing_cycles: list[BillingCycle]


class CreateProductRequest(BaseModel):
    """Schema for creating a product."""

    name: str
    description: str
    type: str = Field(default="SERVICE")


class CancelSubscriptionRequest(BaseModel):
    """Schema for cancelling a subscription."""

    subscription_id: str
    email: str
    reason: str | None = None


class SuspendSubscriptionRequest(BaseModel):
    """Schema for suspending a subscription."""

    subscription_id: str
    email: str
    reason: str | None = None


class ActivateSubscriptionRequest(BaseModel):
    """Schema for activating a subscription."""

    subscription_id: str
    email: str
    reason: str | None = None


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""

    id: str
    status: str
    plan_id: str
    start_time: str | None = None
    subscriber: dict[str, Any] | None = None
    billing_info: dict[str, Any] | None = None
    links: list[dict[str, Any]] | None = None


class WebhookEventRequest(BaseModel):
    """Schema for webhook event."""

    id: str
    event_type: str
    resource: dict[str, Any]
    summary: str | None = None
    create_time: str


class PurchaseUnitAmount(BaseModel):
    """Purchase unit amount schema."""

    currency_code: str
    value: str


class PurchaseUnit(BaseModel):
    """Purchase unit schema."""

    amount: PurchaseUnitAmount
    description: str | None = None


class PayPalOrderCreateRequest(BaseModel):
    """Schema for creating a PayPal order."""

    purchase_units: list[PurchaseUnit]
    email: str  # User email for authentication
    return_url: str | None = None  # URL to redirect after approval
    cancel_url: str | None = None  # URL to redirect if cancelled


class PayPalCaptureRequest(BaseModel):
    """Schema for capturing a PayPal order."""

    order_id: str
    email: str  # User email for authentication


class PayPalOrderResponse(BaseModel):
    """Schema for PayPal order response."""

    id: str
    status: str
    links: list[dict[str, Any]] | None = None
    purchase_units: list[dict[str, Any]] | None = None


class PayPalCaptureResponse(BaseModel):
    """Schema for PayPal capture response."""

    id: str
    status: str
    amount: dict[str, Any] | None = None
    payer: dict[str, Any] | None = None
    links: list[dict[str, Any]] | None = None

