"""
Marketplace operations for split payments, vendor payouts, and platform fees
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal

from ..http_client import HTTPClient


class MarketplaceResource:
    """Marketplace operations for multi-party payments"""

    def __init__(self, client: HTTPClient):
        self.client = client

    async def create_split_payment(
        self,
        amount: float,
        splits: List[Dict[str, Any]],
        currency: str = "INR",
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment with automatic splits to multiple parties

        Args:
            amount: Total payment amount
            currency: Payment currency
            splits: List of split configurations, e.g.:
                [
                    {"account_id": "vendor_123", "amount": 80.00, "type": "vendor"},
                    {"account_id": "platform", "amount": 15.00, "type": "fee"},
                    {"account_id": "tax", "amount": 5.00, "type": "tax"}
                ]
            description: Payment description
            metadata: Additional metadata

        Returns:
            Split payment creation response
        """
        data = {
            "amount": amount,
            "currency": currency,
            "splits": splits
        }

        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata

        return await self.client.request(
            method="POST",
            endpoint="/v1/marketplace/payments/split",
            data=data
        )

    async def get_split_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Get details of a split payment including all splits

        Args:
            payment_id: Split payment ID

        Returns:
            Split payment details with all splits
        """
        return await self.client.request(
            method="GET",
            endpoint=f"/v1/marketplace/payments/split/{payment_id}"
        )

    async def list_vendor_accounts(self) -> Dict[str, Any]:
        """
        List all connected vendor accounts for split payments

        Returns:
            List of vendor account details
        """
        return await self.client.request(
            method="GET",
            endpoint="/v1/marketplace/vendors"
        )

    async def add_vendor_account(
        self,
        vendor_id: str,
        name: str,
        account_details: Dict[str, Any],
        split_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a new vendor account for marketplace payouts

        Args:
            vendor_id: Unique vendor identifier
            name: Vendor display name
            account_details: Bank account or payout method details
            split_config: Default split configuration for this vendor

        Returns:
            Vendor account creation response
        """
        data = {
            "vendor_id": vendor_id,
            "name": name,
            "account_details": account_details
        }

        if split_config:
            data["split_config"] = split_config

        return await self.client.request(
            method="POST",
            endpoint="/v1/marketplace/vendors",
            data=data
        )

    async def update_vendor_split(
        self,
        vendor_id: str,
        split_type: str = "percentage",
        split_percentage: Optional[float] = None,
        split_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update split configuration for a vendor

        Args:
            vendor_id: Vendor identifier
            split_percentage: Percentage of transaction (0-100)
            split_amount: Fixed amount split
            split_type: 'percentage' or 'fixed'

        Returns:
            Updated vendor configuration
        """
        data = {"split_type": split_type}

        if split_percentage is not None:
            data["split_percentage"] = split_percentage
        if split_amount is not None:
            data["split_amount"] = split_amount

        return await self.client.request(
            method="PATCH",
            endpoint=f"/v1/marketplace/vendors/{vendor_id}/split",
            data=data
        )

    async def get_platform_fees(
        self,
        period: str = "month",
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Get platform fees collected in a period

        Args:
            period: Time period ('day', 'week', 'month', 'year')
            currency: Fee currency

        Returns:
            Platform fees summary
        """
        params = {
            "period": period,
            "currency": currency
        }

        return await self.client.request(
            method="GET",
            endpoint="/v1/marketplace/fees",
            params=params
        )

    async def process_bulk_splits(
        self,
        payments: List[Dict[str, Any]],
        process_immediately: bool = True
    ) -> Dict[str, Any]:
        """
        Process multiple split payments in bulk

        Args:
            payments: List of payment configurations with splits
            process_immediately: Whether to process immediately or queue

        Returns:
            Bulk processing response
        """
        data = {
            "payments": payments,
            "process_immediately": process_immediately
        }

        return await self.client.request(
            method="POST",
            endpoint="/v1/marketplace/payments/bulk-split",
            data=data
        )