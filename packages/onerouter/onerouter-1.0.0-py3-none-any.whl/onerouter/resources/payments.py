import time
import secrets
from typing import Optional, Dict, Any

from ..http_client import HTTPClient


class PaymentsResource:
    """Payment operations"""

    def __init__(self, client: HTTPClient):
        self.client = client

    async def create(
        self,
        amount: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment order

        Args:
            amount: Amount in currency units (e.g., 500.00 for ₹500)
            currency: Currency code (INR, USD, etc.)
            receipt: Optional receipt ID
            notes: Optional metadata
            idempotency_key: Optional idempotency key

        Returns:
            {
                "transaction_id": "txn_xxx",
                "provider": "razorpay",
                "provider_order_id": "order_xxx",
                "amount": 500.00,
                "currency": "INR",
                "status": "created",
                "checkout_url": "https://..."
            }
        """
        if not idempotency_key:
            idempotency_key = self._generate_idempotency_key()

        data = {
            "amount": amount,
            "currency": currency
        }

        if receipt:
            data["receipt"] = receipt
        if notes:
            data["notes"] = notes

        return await self.client.request(
            method="POST",
            endpoint="/v1/payments/orders",
            data=data,
            idempotency_key=idempotency_key
        )

    async def get(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment order details"""
        return await self.client.request(
            method="GET",
            endpoint=f"/v1/payments/orders/{transaction_id}"
        )

    async def refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a refund (full or partial)"""
        if not idempotency_key:
            idempotency_key = self._generate_idempotency_key()

        data = {"payment_id": payment_id}
        if amount:
            data["amount"] = amount

        return await self.client.request(
            method="POST",
            endpoint="/v1/payments/refund",
            data=data,
            idempotency_key=idempotency_key
        )

    def _generate_idempotency_key(self) -> str:
        """Generate unique idempotency key"""
        return f"idem_{int(time.time())}_{secrets.token_hex(8)}"