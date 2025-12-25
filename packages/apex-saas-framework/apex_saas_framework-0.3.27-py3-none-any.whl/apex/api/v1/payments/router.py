"""Payments router - PayPal subscription management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import EmailStr

from apex.api.v1.auth.router import get_user_service
from apex.app.models.default import Payment
from apex.core.config import get_settings
from apex.domain.services.user import UserService
from apex.infrastructure.database.session import get_db
from apex.infrastructure.paypal import PayPalService
from sqlalchemy import select

settings = get_settings()
from apex.infrastructure.paypal.schemas import (
    ActivateSubscriptionRequest,
    CancelSubscriptionRequest,
    CreateSubscriptionRequest,
    PayPalCaptureRequest,
    PayPalCaptureResponse,
    PayPalOrderCreateRequest,
    PayPalOrderResponse,
    SubscriptionResponse,
    SuspendSubscriptionRequest,
)
from apex.infrastructure.paypal.webhooks import PayPalWebhookHandler

router = APIRouter(tags=["Payments"])


def get_paypal_service() -> PayPalService:
    """Get PayPal service instance."""
    return PayPalService()


def get_webhook_handler() -> PayPalWebhookHandler:
    """Get PayPal webhook handler instance."""
    return PayPalWebhookHandler()


@router.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Create a PayPal subscription.

    Args:
        request: Subscription creation request
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        Subscription data with approval links

    Example response:
        {
            "id": "I-BW452GLLEP1G",
            "status": "APPROVAL_PENDING",
            "plan_id": "P-5ML4271244454362WXNWU5NQ",
            "links": [
                {
                    "href": "https://www.paypal.com/webapps/billing/subscriptions?ba_token=...",
                    "rel": "approve",
                    "method": "GET"
                }
            ]
        }
    """
    # Verify user exists
    user = await user_service.get_user_by_email(request.subscriber_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        subscriber = {
            "name": {
                "given_name": request.subscriber_first_name,
                "surname": request.subscriber_last_name,
            },
            "email_address": request.subscriber_email,
        }

        # Use redirect URLs from request, or fall back to .env settings
        return_url = request.return_url or settings.PAYPAL_RETURN_URL
        cancel_url = request.cancel_url or settings.PAYPAL_CANCEL_URL

        subscription = await paypal.create_subscription(
            plan_id=request.plan_id,
            subscriber=subscriber,
            return_url=return_url,
            cancel_url=cancel_url,
        )

        # PayPal response doesn't include plan_id at top level, so add it from the request
        subscription["plan_id"] = request.plan_id

        return SubscriptionResponse(**subscription)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create subscription: {str(e)}",
        ) from e


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    email: EmailStr,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Get subscription details.

    Args:
        subscription_id: PayPal subscription ID
        email: User email for authentication
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        Subscription details
    """
    # Verify user exists
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        subscription = await paypal.get_subscription(subscription_id)
        return SubscriptionResponse(**subscription)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription not found: {str(e)}",
        ) from e


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Cancel a subscription.

    Args:
        request: Cancellation request
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        Success message
    """
    # Verify user exists
    user = await user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        await paypal.cancel_subscription(
            subscription_id=request.subscription_id,
            reason=request.reason or "User requested cancellation",
        )

        return {"message": "Subscription cancelled successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel subscription: {str(e)}",
        ) from e


@router.post("/suspend", status_code=status.HTTP_200_OK)
async def suspend_subscription(
    request: SuspendSubscriptionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Suspend a subscription.

    Args:
        request: Suspension request
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        Success message
    """
    # Verify user exists
    user = await user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        await paypal.suspend_subscription(
            subscription_id=request.subscription_id,
            reason=request.reason or "Subscription suspended",
        )

        return {"message": "Subscription suspended successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to suspend subscription: {str(e)}",
        ) from e


@router.post("/activate", status_code=status.HTTP_200_OK)
async def activate_subscription(
    request: ActivateSubscriptionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Activate a suspended subscription.

    Args:
        request: Activation request
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        Success message
    """
    # Verify user exists
    user = await user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        await paypal.activate_subscription(
            subscription_id=request.subscription_id,
            reason=request.reason or "Subscription reactivated",
        )

        return {"message": "Subscription activated successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to activate subscription: {str(e)}",
        ) from e


@router.get("/billing-history/{subscription_id}")
async def get_billing_history(
    subscription_id: str,
    email: EmailStr,
    start_date: str,
    end_date: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Get billing history for a subscription.

    Args:
        subscription_id: PayPal subscription ID
        email: User email for authentication
        start_date: Start date (ISO 8601 format, e.g., 2023-01-01T00:00:00Z)
        end_date: End date (ISO 8601 format)
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        Transaction history
    """
    # Verify user exists
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        transactions = await paypal.list_transactions(
            subscription_id=subscription_id,
            start_date=start_date,
            end_date=end_date,
        )

        return transactions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get billing history: {str(e)}",
        ) from e


@router.post("/orders", response_model=PayPalOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_paypal_order(
    payload: PayPalOrderCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Create a PayPal order.

    Creates a PayPal order and stores it in the database.

    Args:
        payload: Order creation request with purchase units and user email
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        PayPal order response with approval links
    """
    # Verify user exists
    user = await user_service.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        # Prepare purchase units for PayPal
        purchase_units = []
        for unit in payload.purchase_units:
            purchase_units.append({
                "amount": {
                    "currency_code": unit.amount.currency_code,
                    "value": unit.amount.value,
                },
                "description": unit.description,
            })
        
        # Use redirect URLs from payload, or fall back to .env settings
        return_url = payload.return_url or settings.PAYPAL_RETURN_URL
        cancel_url = payload.cancel_url or settings.PAYPAL_CANCEL_URL
        
        if not return_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="return_url is required. Provide it in the request or set PAYPAL_RETURN_URL in .env",
            )
        if not cancel_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cancel_url is required. Provide it in the request or set PAYPAL_CANCEL_URL in .env",
            )
        
        # Create order in PayPal
        order_response = await paypal.create_order(
            intent="CAPTURE",
            purchase_units=purchase_units,
            return_url=return_url,
            cancel_url=cancel_url,
        )
        
        # Store order in database
        first_unit = payload.purchase_units[0]
        amount_value = float(first_unit.amount.value)
        currency_code = first_unit.amount.currency_code
        
        # Check if order already exists
        stmt = select(Payment).where(Payment.paypal_order_id == order_response["id"])
        result = await db.execute(stmt)
        existing_payment = result.scalar_one_or_none()
        
        if existing_payment:
            existing_payment.amount = amount_value
            existing_payment.currency = currency_code
            existing_payment.payment_metadata = order_response
        else:
            payment = Payment(
                paypal_order_id=order_response["id"],
                amount=amount_value,
                currency=currency_code,
                payment_metadata=order_response,
            )
            db.add(payment)
        
        await db.commit()
        
        return PayPalOrderResponse(**order_response)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create order: {str(e)}",
        ) from e


@router.get("/orders/{order_id}", response_model=PayPalOrderResponse, status_code=status.HTTP_200_OK)
async def get_paypal_order(
    order_id: str,
    email: EmailStr = Query(..., description="User email for authentication"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Get PayPal order status.

    Retrieves the current status and details of a PayPal order.

    Args:
        order_id: PayPal order ID
        email: User email for authentication
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        PayPal order response with current status
    """
    # Verify user exists
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        # Get order from PayPal
        order_response = await paypal.get_order(order_id)
        
        return PayPalOrderResponse(**order_response)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get order: {str(e)}",
        ) from e


@router.post("/orders/capture", response_model=PayPalCaptureResponse, status_code=status.HTTP_200_OK)
async def capture_paypal_order(
    payload: PayPalCaptureRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserService = Depends(get_user_service),
    paypal: PayPalService = Depends(get_paypal_service),
):
    """
    Capture a PayPal order.

    Captures funds for a previously approved PayPal order.

    Args:
        payload: Capture request with order ID and user email
        db: Database session
        user_service: User service to verify user exists
        paypal: PayPal service

    Returns:
        PayPal capture response
    """
    # Verify user exists
    user = await user_service.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    try:
        # Capture order in PayPal
        capture_response = await paypal.capture_order(payload.order_id)
        
        # Find order in database
        stmt = select(Payment).where(Payment.paypal_order_id == payload.order_id)
        result = await db.execute(stmt)
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {payload.order_id} not found in database.",
            )
        
        # Extract capture ID from response
        purchase_units = capture_response.get("purchase_units", [])
        capture_id = None
        if purchase_units:
            captures = purchase_units[0].get("payments", {}).get("captures", [])
            if captures:
                capture_id = captures[0].get("id")
        
        # Update payment record
        payment.paypal_capture_id = capture_id
        payment.payment_metadata = capture_response
        
        await db.commit()

        # Build a normalized response that always includes `amount`
        # at the top level for easier consumption by frontends.
        amount: dict[str, Any] | None = None
        payer: dict[str, Any] | None = capture_response.get("payer")
        links: list[dict[str, Any]] | None = capture_response.get("links")

        if purchase_units:
            # Safely drill into the first purchase unit's captures to extract amount.
            captures = purchase_units[0].get("payments", {}).get("captures", [])
            if captures:
                amount = captures[0].get("amount")

        return PayPalCaptureResponse(
            id=capture_response.get("id", capture_id or ""),
            status=capture_response.get("status", "COMPLETED"),
            amount=amount,
            payer=payer,
            links=links,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to capture order: {str(e)}",
        ) from e


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paypal_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    webhook_handler: PayPalWebhookHandler = Depends(get_webhook_handler),
):
    """
    Handle PayPal webhooks.

    This endpoint receives webhook events from PayPal.
    Configure this URL in your PayPal Developer Dashboard.

    Args:
        request: FastAPI request object
        db: Database session
        webhook_handler: Webhook handler instance

    Returns:
        Success message
    """
    try:
        # Get webhook headers
        transmission_id = request.headers.get("PAYPAL-TRANSMISSION-ID")
        transmission_time = request.headers.get("PAYPAL-TRANSMISSION-TIME")
        cert_url = request.headers.get("PAYPAL-CERT-URL")
        auth_algo = request.headers.get("PAYPAL-AUTH-ALGO")
        transmission_sig = request.headers.get("PAYPAL-TRANSMISSION-SIG")

        # Get webhook body
        webhook_event = await request.json()

        # Verify webhook signature (optional but recommended)
        # webhook_id = settings.PAYPAL_WEBHOOK_ID
        # if webhook_id:
        #     is_valid = await webhook_handler.verify_webhook_signature(
        #         webhook_id=webhook_id,
        #         transmission_id=transmission_id,
        #         transmission_time=transmission_time,
        #         cert_url=cert_url,
        #         auth_algo=auth_algo,
        #         transmission_sig=transmission_sig,
        #         webhook_event=webhook_event,
        #     )
        #     if not is_valid:
        #         raise HTTPException(
        #             status_code=status.HTTP_401_UNAUTHORIZED,
        #             detail="Invalid webhook signature",
        #         )

        # Process webhook event
        result = await webhook_handler.process_webhook_event(webhook_event)

        return {"status": "success", "result": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process webhook: {str(e)}",
        ) from e

