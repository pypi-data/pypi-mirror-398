import asyncio
from typing import Optional

from .client import OneRouter


# ============================================
# SYNC WRAPPER (for non-async code)
# ============================================

class OneRouterSync:
    """
    Synchronous wrapper for OneRouter async client.
    
    Provides a synchronous interface for applications that don't use async/await.
    Properly manages event loop creation and cleanup to avoid resource leaks.
    
    Usage:
        client = OneRouterSync(api_key="sk-...")
        try:
            result = client.payments.create(...)
        finally:
            client.close()
    """

    def __init__(self, api_key: str, **kwargs):
        """
        Initialize sync wrapper.
        
        Args:
            api_key: OneRouter API key
            **kwargs: Additional arguments passed to OneRouter client
        """
        self.async_client = OneRouter(api_key=api_key, **kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._own_loop = False

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get or create event loop.
        
        Strategy:
        1. Try to get running loop (Python 3.10+ compatible)
        2. If no running loop, create new one and track ownership
        3. Reuse created loop for subsequent calls
        
        Returns:
            Event loop instance
        """
        if self._loop is None:
            try:
                # Try to get currently running loop (thread-safe)
                self._loop = asyncio.get_running_loop()
                self._own_loop = False  # We don't own it
            except RuntimeError:
                # No running loop in this thread, create new one
                self._loop = asyncio.new_event_loop()
                self._own_loop = True  # We own it, must close it
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run_async(self, coro):
        """
        Run async coroutine synchronously.
        
        Args:
            coro: Coroutine to execute
            
        Returns:
            Result from coroutine
        """
        loop = self._get_loop()
        return loop.run_until_complete(coro)

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

        return SyncPayments(self.async_client.payments, self._get_loop())

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

        return SyncSubscriptions(self.async_client.subscriptions, self._get_loop())

    @property
    def payment_links(self):
        """Sync payment links resource"""
        class SyncPaymentLinks:
            def __init__(self, async_links, loop):
                self._async = async_links
                self._loop = loop

            def create(self, **kwargs):
                return self._loop.run_until_complete(self._async.create(**kwargs))

        return SyncPaymentLinks(self.async_client.payment_links, self._get_loop())

    def close(self):
        """
        Close client and cleanup resources.
        
        - Closes async client
        - Only closes event loop if we created it
        - Safe to call multiple times
        """
        try:
            self._run_async(self.async_client.close())
        finally:
            # Only close loop if we created it
            if self._own_loop and self._loop and not self._loop.is_closed():
                self._loop.close()
                self._loop = None