"""PayPal REST API v2 client."""

import base64
from datetime import datetime, timedelta
from typing import Any

import httpx

from apex.core.config import get_settings
from apex.infrastructure.paypal.exceptions import PayPalAPIError, PayPalAuthenticationError

settings = get_settings()


class PayPalClient:
    """
    PayPal REST API v2 client.

    Handles authentication and API requests to PayPal.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        mode: str | None = None,
    ):
        """
        Initialize PayPal client.

        Args:
            client_id: PayPal client ID (defaults to settings)
            client_secret: PayPal client secret (defaults to settings)
            mode: 'sandbox' or 'live' (defaults to settings)
        """
        self.client_id = client_id or settings.PAYPAL_CLIENT_ID
        self.client_secret = client_secret or settings.PAYPAL_CLIENT_SECRET
        self.mode = mode or settings.PAYPAL_MODE

        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal client ID and secret are required")

        self.base_url = self._get_base_url()
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    def _get_base_url(self) -> str:
        """Get PayPal API base URL based on mode."""
        if self.mode == "live":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    async def _get_access_token(self) -> str:
        """
        Get or refresh PayPal access token.

        Returns:
            Valid access token

        Raises:
            PayPalAuthenticationError: If authentication fails
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token

        # Request new access token
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/oauth2/token",
                    headers=headers,
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

                self._access_token = result["access_token"]
                expires_in = result.get("expires_in", 3600)
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)

                return self._access_token

            except httpx.HTTPStatusError as e:
                raise PayPalAuthenticationError(
                    f"Failed to authenticate with PayPal: {e.response.text}"
                ) from e
            except Exception as e:
                raise PayPalAuthenticationError(f"PayPal authentication error: {str(e)}") from e

    async def request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to PayPal API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., '/v1/billing/subscriptions')
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            PayPalAPIError: If API request fails
        """
        access_token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                )
                response.raise_for_status()

                # Handle empty responses (e.g., 204 No Content)
                if response.status_code == 204:
                    return {}

                return response.json()

            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                try:
                    error_json = e.response.json()
                    error_detail = error_json.get("message", error_detail)
                except Exception:
                    pass

                raise PayPalAPIError(
                    f"PayPal API error: {error_detail}",
                    status_code=e.response.status_code,
                    response=e.response.json() if e.response.text else None,
                ) from e
            except Exception as e:
                raise PayPalAPIError(f"PayPal request error: {str(e)}") from e

