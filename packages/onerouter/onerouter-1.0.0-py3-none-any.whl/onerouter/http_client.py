import asyncio
import httpx
from typing import Optional, Dict, Any

from .exceptions import AuthenticationError, RateLimitError, ValidationError, APIError


# ============================================
# HTTP CLIENT
# ============================================

class HTTPClient:
    """HTTP client with automatic retries and error handling"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.onerouter.com",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "X-Platform-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "onerouter-python/1.0.0"
            }
        )

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retries"""
        url = f"{self.base_url}{endpoint}"
        headers = {}

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )

                # Handle success
                if 200 <= response.status_code < 300:
                    return response.json()

                # Handle errors
                self._handle_error(response)

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise APIError("Request timed out", status_code=504)
                await self._backoff(attempt)

            except httpx.NetworkError:
                if attempt == self.max_retries - 1:
                    raise APIError("Network error", status_code=503)
                await self._backoff(attempt)

        raise APIError("Max retries exceeded", status_code=503)

    def _handle_error(self, response: httpx.Response):
        """Parse error response and raise appropriate exception"""
        error_data = None
        try:
            error_data = response.json()
            message = error_data.get("detail", "Unknown error")
        except:
            message = response.text or "Unknown error"

        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {message}")
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError(f"Rate limit exceeded: {message}", retry_after=retry_after)
        elif response.status_code == 422:
            raise ValidationError(f"Validation error: {message}")
        else:
            raise APIError(message, status_code=response.status_code, response=error_data)

    async def _backoff(self, attempt: int):
        """Exponential backoff between retries"""
        delay = min(2 ** attempt, 10)  # Max 10 seconds
        await asyncio.sleep(delay)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()