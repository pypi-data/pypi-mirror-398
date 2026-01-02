from typing import Dict, Any, Optional

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
        quantity: int = 1,
        trial_days: Optional[int] = None,
        start_date: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription with enhanced options

        Args:
            plan_id: Plan identifier
            customer_notify: Whether to notify customer (default: True)
            total_count: Total billing cycles (default: 12)
            quantity: Subscription quantity (default: 1)
            trial_days: Number of trial days (optional)
            start_date: Subscription start date in ISO format (optional)
            provider: Force specific provider ('razorpay', 'paypal')

        Returns:
            Subscription creation response
        """
        data = {
            "plan_id": plan_id,
            "customer_notify": customer_notify,
            "total_count": total_count,
            "quantity": quantity
        }

        # Add optional enhanced parameters
        if trial_days is not None:
            data["trial_days"] = trial_days
        if start_date is not None:
            data["start_date"] = start_date
        if provider is not None:
            data["provider"] = provider

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

    async def pause(
        self,
        subscription_id: str,
        pause_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pause subscription

        Args:
            subscription_id: Subscription identifier
            pause_at: When to pause ('now' or 'cycle_end', default: 'now')

        Returns:
            Pause operation response
        """
        data = {}
        if pause_at:
            data["pause_at"] = pause_at

        return await self.client.request(
            method="POST",
            endpoint=f"/v1/subscriptions/{subscription_id}/pause",
            data=data
        )

    async def resume(self, subscription_id: str) -> Dict[str, Any]:
        """
        Resume paused subscription

        Args:
            subscription_id: Subscription identifier

        Returns:
            Resume operation response
        """
        return await self.client.request(
            method="POST",
            endpoint=f"/v1/subscriptions/{subscription_id}/resume"
        )

    async def change_plan(
        self,
        subscription_id: str,
        new_plan_id: str,
        prorate: bool = True
    ) -> Dict[str, Any]:
        """
        Change subscription plan

        Args:
            subscription_id: Current subscription identifier
            new_plan_id: New plan identifier
            prorate: Whether to prorate charges (default: True)

        Returns:
            Plan change response
        """
        data = {
            "new_plan_id": new_plan_id,
            "prorate": prorate
        }

        return await self.client.request(
            method="POST",
            endpoint=f"/v1/subscriptions/{subscription_id}/change_plan",
            data=data
        )