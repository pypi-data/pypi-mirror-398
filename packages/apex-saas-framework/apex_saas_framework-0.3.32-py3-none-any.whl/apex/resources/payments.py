"""
Payments Resource - Clerk-style payment management
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apex.client import Client
from apex.infrastructure.paypal.service import PayPalService as PayPalServiceInfra
from apex.infrastructure.paypal.client import PayPalClient


class Payments:
    """
    Payments resource - provides PayPal payment management
    
    Usage:
        async with client:
            # Create order
            order = await client.payments.create_order(
                amount=99.99,
                currency="USD",
                description="Premium Plan"
            )
            
            # Capture order
            capture = await client.payments.capture_order(order_id="...")
            
            # Create subscription
            subscription = await client.payments.create_subscription(
                plan_id="...",
                subscriber={"email": "user@example.com"}
            )
    """
    
    def __init__(self, client: Client):
        self.client = client
        self._paypal_service = None
    
    @property
    def paypal_service(self) -> PayPalServiceInfra:
        """Get PayPal service instance"""
        if self._paypal_service is None:
            try:
                # Try to get credentials from environment (supports both standard and alternative names)
                import os
                from apex.core.config import get_settings
                settings = get_settings()
                
                # Get credentials - try alternative names first, then standard
                client_id = (
                    os.getenv("NEW_US_SANDBOX_CLIENT_ID") or 
                    os.getenv("PAYPAL_CLIENT_ID") or 
                    settings.PAYPAL_CLIENT_ID
                )
                client_secret = (
                    os.getenv("NEW_US_SANDBOX_SECRET") or 
                    os.getenv("PAYPAL_CLIENT_SECRET") or 
                    settings.PAYPAL_CLIENT_SECRET
                )
                mode = os.getenv("PAYPAL_MODE") or settings.PAYPAL_MODE or "sandbox"
                
                # Strip whitespace in case .env has trailing spaces
                if client_id:
                    client_id = client_id.strip()
                if client_secret:
                    client_secret = client_secret.strip()
                
                paypal_client = PayPalClient(
                    client_id=client_id,
                    client_secret=client_secret,
                    mode=mode
                )
                self._paypal_service = PayPalServiceInfra(client=paypal_client)
            except ValueError as e:
                raise ValueError(
                    f"PayPal not configured: {str(e)}. "
                    "Set PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, and PAYPAL_MODE in environment."
                )
        return self._paypal_service
    
    async def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: Optional[str] = None,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        save_to_db: bool = False
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
        
        Returns:
            Order data with payment information
        """
        body = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    },
                    "description": description or f"Payment of {amount} {currency}",
                }
            ],
        }
        
        # Add application_context if URLs provided
        if return_url or cancel_url:
            body["application_context"] = {
                "return_url": return_url or "https://example.com/success",
                "cancel_url": cancel_url or "https://example.com/cancel",
            }
        
        response = await self.paypal_service.client.request("POST", "/v2/checkout/orders", data=body)
        order_id = response.get("id")
        
        result = {
            "order": response,
            "order_id": order_id
        }
        
        # Optionally save to database if requested
        if save_to_db:
            try:
                # Try to import Payment model (may not exist in SDK-only usage)
                from apex.app.models.default import Payment
                
                async with self.client.get_session() as session:
                    payment = Payment(
                        paypal_order_id=order_id,
                        amount=amount,
                        currency=currency,
                        payment_metadata=response,
                    )
                    session.add(payment)
                    await session.flush()
                    await session.refresh(payment)
                    await session.commit()
                    result["payment_id"] = str(payment.id)
            except ImportError:
                # Payment model not available - skip database save
                pass
            except Exception as e:
                # Database save failed - log but don't fail the order creation
                import warnings
                warnings.warn(f"Failed to save payment to database: {str(e)}")
        
        return result
    
    async def capture_order(self, order_id: str, update_db: bool = False) -> Dict[str, Any]:
        """
        Capture a PayPal order.
        
        Args:
            order_id: PayPal order ID
            update_db: Whether to update payment record in database (default: False)
        
        Returns:
            Capture response with payment information
        """
        capture_response = await self.paypal_service.client.request(
            "POST", f"/v2/checkout/orders/{order_id}/capture"
        )
        
        result = {
            "capture": capture_response
        }
        
        # Optionally update database if requested
        if update_db:
            try:
                from apex.app.models.default import Payment
                
                async with self.client.get_session() as session:
                    result_query = await session.execute(
                        select(Payment).where(Payment.paypal_order_id == order_id)
                    )
                    payment = result_query.scalar_one_or_none()
                    
                    if payment:
                        captures = (
                            capture_response.get("purchase_units", [])[0]
                            .get("payments", {})
                            .get("captures", [])
                        )
                        capture_id = captures[0]["id"] if captures else None
                        payment.paypal_capture_id = capture_id
                        payment.payment_metadata = capture_response
                        await session.flush()
                        await session.refresh(payment)
                        await session.commit()
                        result["payment_id"] = str(payment.id)
            except ImportError:
                # Payment model not available - skip database update
                pass
            except Exception as e:
                # Database update failed - log but don't fail the capture
                import warnings
                warnings.warn(f"Failed to update payment in database: {str(e)}")
        
        return result
    
    async def create_subscription(
        self,
        plan_id: str,
        subscriber: Dict[str, Any],
        return_url: str = "https://example.com/return",
        cancel_url: str = "https://example.com/cancel"
    ) -> Dict[str, Any]:
        """
        Create a PayPal subscription.
        
        Args:
            plan_id: Billing plan ID
            subscriber: Subscriber information (email, name, etc.)
            return_url: URL to redirect after approval
            cancel_url: URL to redirect if cancelled
        
        Returns:
            Subscription data with approval links
        """
        return await self.paypal_service.create_subscription(
            plan_id=plan_id,
            subscriber=subscriber,
            return_url=return_url,
            cancel_url=cancel_url
        )
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a PayPal subscription.
        
        Args:
            subscription_id: Subscription ID
        
        Returns:
            Cancellation response
        """
        return await self.paypal_service.cancel_subscription(subscription_id)
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details.
        
        Args:
            subscription_id: Subscription ID
        
        Returns:
            Subscription data
        """
        return await self.paypal_service.get_subscription(subscription_id)


