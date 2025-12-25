from fastapi import APIRouter, Depends

from apex.app.core.auth import require_permission
from apex.app.core.dependencies import get_session
from apex.app.payments.schemas import PayPalCaptureRequest, PayPalOrderCreate
from apex.app.payments.services import PayPalService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_paypal_service(session: AsyncSession = Depends(get_session)) -> PayPalService:
    return PayPalService(session)


@router.post(
    "/paypal/create-order",
    dependencies=[Depends(require_permission("payments:manage"))],
)
async def create_order(payload: PayPalOrderCreate, service: PayPalService = Depends(get_paypal_service)):
    return await service.create_order(payload)


@router.post(
    "/paypal/capture",
    dependencies=[Depends(require_permission("payments:manage"))],
)
async def capture_order(payload: PayPalCaptureRequest, service: PayPalService = Depends(get_paypal_service)):
    return await service.capture_order(payload)

