import asyncio

from .client import OneRouter


# ============================================
# SYNC WRAPPER (for non-async code)
# ============================================

class OneRouterSync:
    """Synchronous wrapper for OneRouter (for non-async code)"""

    def __init__(self, api_key: str, **kwargs):
        self.async_client = OneRouter(api_key=api_key, **kwargs)
        self._loop = asyncio.get_event_loop()

    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        return self._loop.run_until_complete(coro)

    @property
    def payments(self):
        """Sync payments resource"""
        class SyncPayments:
            def __init__(self, async_payments, loop):
                self._async = async_payments
                self._loop = loop

            def create(self, **kwargs):
                return self._loop.run_until_complete(self._async.create(**kwargs))

            def get(self, transaction_id):
                return self._loop.run_until_complete(self._async.get(transaction_id))

            def refund(self, **kwargs):
                return self._loop.run_until_complete(self._async.refund(**kwargs))

        return SyncPayments(self.async_client.payments, self._loop)

    @property
    def subscriptions(self):
        """Sync subscriptions resource"""
        class SyncSubscriptions:
            def __init__(self, async_subs, loop):
                self._async = async_subs
                self._loop = loop

            def create(self, **kwargs):
                return self._loop.run_until_complete(self._async.create(**kwargs))

            def get(self, subscription_id):
                return self._loop.run_until_complete(self._async.get(subscription_id))

            def cancel(self, **kwargs):
                return self._loop.run_until_complete(self._async.cancel(**kwargs))

        return SyncSubscriptions(self.async_client.subscriptions, self._loop)

    @property
    def payment_links(self):
        """Sync payment links resource"""
        class SyncPaymentLinks:
            def __init__(self, async_links, loop):
                self._async = async_links
                self._loop = loop

            def create(self, **kwargs):
                return self._loop.run_until_complete(self._async.create(**kwargs))

        return SyncPaymentLinks(self.async_client.payment_links, self._loop)

    def close(self):
        """Close client"""
        self._run_async(self.async_client.close())