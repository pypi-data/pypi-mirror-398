from .http_client import HTTPClient
from .resources.payments import PaymentsResource
from .resources.subscriptions import SubscriptionsResource
from .resources.payment_links import PaymentLinksResource
from .resources.saved_payment_methods import SavedPaymentMethodsResource
from .resources.marketplace import MarketplaceResource


# ============================================
# MAIN CLIENT
# ============================================

class OneRouter:
    """
    OneRouter Unified API Client

    Usage:
        client = OneRouter(api_key="unf_live_xxx")

        # Create payment
        order = await client.payments.create(amount=500.00, currency="INR")

        # Create subscription with trial
        sub = await client.subscriptions.create(plan_id="plan_123", trial_days=7)

        # Enhanced refund
        refund = await client.payments.refund("txn_123", amount=100.00, reason="customer_request")

        # Manage saved payment methods
        methods = await client.saved_payment_methods.list()

        # Marketplace split payments
        split_payment = await client.marketplace.create_split_payment(
            amount=100.00,
            splits=[
                {"account_id": "vendor_123", "amount": 80.00, "type": "vendor"},
                {"account_id": "platform", "amount": 15.00, "type": "fee"}
            ]
        )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.onerouter.com",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize OneRouter client

        Args:
            api_key: Your OneRouter API key (unf_live_xxx or unf_test_xxx)
            base_url: API base URL (default: https://api.onerouter.com)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        if not api_key:
            raise ValueError("API key is required")

        if not api_key.startswith(("unf_live_", "unf_test_")):
            raise ValueError("Invalid API key format. Must start with unf_live_ or unf_test_")

        self.http_client = HTTPClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )

        # Initialize resource classes
        self.payments = PaymentsResource(self.http_client)
        self.subscriptions = SubscriptionsResource(self.http_client)
        self.payment_links = PaymentLinksResource(self.http_client)
        self.saved_payment_methods = SavedPaymentMethodsResource(self.http_client)
        self.marketplace = MarketplaceResource(self.http_client)

    async def close(self):
        """Close HTTP client (call this when done)"""
        await self.http_client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()