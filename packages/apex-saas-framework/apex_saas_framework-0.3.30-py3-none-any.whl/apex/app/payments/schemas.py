from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PayPalOrderCreate(BaseModel):
    plan_id: str
    amount: float
    currency: str = "USD"
    description: str | None = None


class PayPalCaptureRequest(BaseModel):
    order_id: str


class PaymentOut(BaseModel):
    id: UUID
    paypal_order_id: str
    paypal_capture_id: str | None
    amount: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True

