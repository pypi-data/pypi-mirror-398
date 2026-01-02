from typing import Optional, Dict, Any

from ..http_client import HTTPClient


class PaymentLinksResource:
    """Payment link operations"""

    def __init__(self, client: HTTPClient):
        self.client = client

    async def create(
        self,
        amount: float,
        description: str,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a payment link"""
        data = {
            "amount": amount,
            "description": description
        }

        if customer_email:
            data["customer_email"] = customer_email

        return await self.client.request(
            method="POST",
            endpoint="/v1/payment-links",
            data=data
        )