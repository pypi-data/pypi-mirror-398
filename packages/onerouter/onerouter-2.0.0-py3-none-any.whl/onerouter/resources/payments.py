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
        method: Optional[str] = None,
        provider: Optional[str] = None,
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        # Payment method specific options
        upi_app: Optional[str] = None,
        emi_plan: Optional[str] = None,  # '3_months', '6_months', '12_months', etc.
        card_network: Optional[str] = None,
        wallet_provider: Optional[str] = None,
        bank_code: Optional[str] = None,
        save_card: bool = False  # Save card for future payments
    ) -> Dict[str, Any]:
        """
        Create a payment order with payment method support

        Args:
            amount: Amount in currency units (e.g., 500.00 for ₹500)
            currency: Currency code (INR, USD, etc.)
            method: Payment method ('upi', 'card', 'netbanking', 'wallet', etc.)
            provider: Force specific provider ('razorpay', 'paypal')
            receipt: Optional receipt ID
            notes: Optional metadata
            idempotency_key: Optional idempotency key

            # Payment method specific options:
            upi_app: UPI app preference ('gpay', 'phonepe', 'paytm', 'bhim', etc.)
            emi_plan: EMI plan ('3_months', '6_months', '12_months', etc.)
            card_network: Preferred card network ('visa', 'mastercard', 'amex', etc.)
            wallet_provider: Wallet provider ('paytm', 'mobikwik', 'olamoney', etc.)
            bank_code: Net banking bank code (for Razorpay)

        Returns:
            {
                "transaction_id": "txn_xxx",
                "provider": "razorpay",
                "provider_order_id": "order_xxx",
                "amount": 500.00,
                "currency": "INR",
                "status": "created",
                "checkout_url": "https://...",
                "payment_method": "upi",  # New field
                "method_details": {...}   # New field with method-specific info
            }
        """
        if not idempotency_key:
            idempotency_key = self._generate_idempotency_key()

        data = {
            "amount": amount,
            "currency": currency
        }

        # Add payment method preferences
        if method:
            data["method"] = method
        if provider:
            data["provider"] = provider

        # Add method-specific options
        if upi_app:
            data["upi_app"] = upi_app
        if emi_plan:
            data["emi_plan"] = emi_plan
        if card_network:
            data["card_network"] = card_network
        if wallet_provider:
            data["wallet_provider"] = wallet_provider
        if bank_code:
            data["bank_code"] = bank_code
        if save_card:
            data["save_card"] = save_card

        # Legacy parameters
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
        reason: Optional[str] = None,
        speed: str = "normal",
        notes: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a refund with enhanced options

        Args:
            payment_id: Payment transaction ID to refund
            amount: Refund amount (None for full refund)
            reason: Reason for refund ('customer_request', 'duplicate', 'fraudulent', etc.)
            speed: Refund speed ('normal', 'optimum' for Razorpay)
            notes: Additional metadata for the refund
            idempotency_key: Optional idempotency key

        Returns:
            Refund creation response
        """
        if not idempotency_key:
            idempotency_key = self._generate_idempotency_key()

        data = {"payment_id": payment_id}

        # Add optional parameters
        if amount is not None:
            data["amount"] = amount
        if reason:
            data["reason"] = reason
        if speed != "normal":  # Only add if not default
            data["speed"] = speed
        if notes:
            data["notes"] = notes

        return await self.client.request(
            method="POST",
            endpoint="/v1/payments/refund",
            data=data,
            idempotency_key=idempotency_key
        )

    def _generate_idempotency_key(self) -> str:
        """Generate unique idempotency key"""
        return f"idem_{int(time.time())}_{secrets.token_hex(8)}"