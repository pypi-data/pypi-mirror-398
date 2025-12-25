from fastapi import HTTPException, status
from sqlalchemy import select

from apex.app.models.default import Payment
from apex.app.payments.schemas import PayPalOrderCreate, PayPalCaptureRequest, PaymentOut
from apex.infrastructure.paypal.client import PayPalClient


class PayPalService:
    def __init__(self, session, client: PayPalClient | None = None):
        self.session = session
        try:
            self.client = client or PayPalClient()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

    async def create_order(self, payload: PayPalOrderCreate) -> dict:
        body = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": payload.currency,
                        "value": f"{payload.amount:.2f}",
                    },
                    "description": payload.description,
                }
            ],
        }
        response = await self.client.request("POST", "/v2/checkout/orders", data=body)
        order_id = response.get("id")
        payment = Payment(
            paypal_order_id=order_id,
            amount=payload.amount,
            currency=payload.currency,
            payment_metadata=response,
        )
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return {"order": response, "payment": PaymentOut.model_validate(payment)}

    async def capture_order(self, payload: PayPalCaptureRequest) -> dict:
        capture_response = await self.client.request(
            "POST", f"/v2/checkout/orders/{payload.order_id}/capture"
        )
        result = await self.session.execute(
            select(Payment).where(Payment.paypal_order_id == payload.order_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        captures = (
            capture_response.get("purchase_units", [])[0]
            .get("payments", {})
            .get("captures", [])
        )
        capture_id = captures[0]["id"] if captures else None
        payment.paypal_capture_id = capture_id
        payment.payment_metadata = capture_response
        await self.session.flush()
        await self.session.refresh(payment)
        return {"capture": capture_response, "payment": PaymentOut.model_validate(payment)}

