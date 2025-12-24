from typing import Dict, Any

from ..http_client import HTTPClient


class SubscriptionsResource:
    """Subscription operations"""

    def __init__(self, client: HTTPClient):
        self.client = client

    async def create(
        self,
        plan_id: str,
        customer_notify: bool = True,
        total_count: int = 12,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Create a subscription"""
        data = {
            "plan_id": plan_id,
            "customer_notify": customer_notify,
            "total_count": total_count,
            "quantity": quantity
        }

        return await self.client.request(
            method="POST",
            endpoint="/v1/subscriptions",
            data=data
        )

    async def get(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        return await self.client.request(
            method="GET",
            endpoint=f"/v1/subscriptions/{subscription_id}"
        )

    async def cancel(
        self,
        subscription_id: str,
        cancel_at_cycle_end: bool = False
    ) -> Dict[str, Any]:
        """Cancel subscription"""
        data = {"cancel_at_cycle_end": cancel_at_cycle_end}

        return await self.client.request(
            method="POST",
            endpoint=f"/v1/subscriptions/{subscription_id}/cancel",
            data=data
        )