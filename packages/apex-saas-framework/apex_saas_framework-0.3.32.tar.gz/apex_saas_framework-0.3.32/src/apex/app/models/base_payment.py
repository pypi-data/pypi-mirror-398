"""
PayPal payment tracking model.
"""
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apex.app.database.base import BaseModel


class BasePayment(BaseModel):
    """Abstract payment record."""

    __abstract__ = True

    paypal_order_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    paypal_capture_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="created")  # created, captured, failed, refunded
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="paypal")  # paypal, stripe, manual
    payment_metadata: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    
    # Link to user and organization
    user_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    organization_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), index=True)


__all__ = ["BasePayment"]

