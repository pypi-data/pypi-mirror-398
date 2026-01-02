from typing import Dict, Any, Optional, List

from ..http_client import HTTPClient


class SavedPaymentMethodsResource:
    """Saved payment methods management"""

    def __init__(self, client: HTTPClient):
        self.client = client

    async def list(self) -> List[Dict[str, Any]]:
        """
        List saved payment methods for the authenticated user

        Returns:
            List of saved payment methods
        """
        return await self.client.request(
            method="GET",
            endpoint="/v1/payment-methods"
        )

    async def save(
        self,
        payment_method_id: str,
        nickname: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a payment method for future use

        Args:
            payment_method_id: Payment method ID from successful payment
            nickname: User-friendly name for the saved method
            metadata: Additional metadata

        Returns:
            Saved payment method details
        """
        data = {"payment_method_id": payment_method_id}
        if nickname:
            data["nickname"] = nickname
        if metadata:
            data["metadata"] = metadata

        return await self.client.request(
            method="POST",
            endpoint="/v1/payment-methods",
            data=data
        )

    async def delete(self, saved_method_id: str) -> Dict[str, Any]:
        """
        Delete a saved payment method

        Args:
            saved_method_id: ID of the saved payment method

        Returns:
            Deletion confirmation
        """
        return await self.client.request(
            method="DELETE",
            endpoint=f"/v1/payment-methods/{saved_method_id}"
        )

    async def update(
        self,
        saved_method_id: str,
        nickname: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a saved payment method

        Args:
            saved_method_id: ID of the saved payment method
            nickname: New nickname
            metadata: Updated metadata

        Returns:
            Updated payment method details
        """
        data = {}
        if nickname:
            data["nickname"] = nickname
        if metadata:
            data["metadata"] = metadata

        return await self.client.request(
            method="PATCH",
            endpoint=f"/v1/payment-methods/{saved_method_id}",
            data=data
        )