import asyncio
import httpx
from typing import Optional, Dict, Any

from .exceptions import AuthenticationError, RateLimitError, ValidationError, APIError


# ============================================
# HTTP CLIENT
# ============================================

class HTTPClient:
    """
    HTTP client with automatic retries, timeout handling, and error handling.
    
    Features:
    - Automatic retry with exponential backoff
    - Per-request timeout override capability
    - Comprehensive error handling
    - Request timeout with detailed error context
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.onerouter.com",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize HTTP client.
        
        Args:
            api_key: API key for authentication
            base_url: API base URL
            timeout: Default request timeout in seconds (can be overridden per-request)
            max_retries: Number of retries for failed requests
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
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
        idempotency_key: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with automatic retry and timeout handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            idempotency_key: Idempotency key for idempotent operations
            timeout: Request timeout in seconds (overrides default if provided)
            
        Returns:
            Response data as dictionary
            
        Raises:
            AuthenticationError: On 401/403 responses
            RateLimitError: On 429 responses
            ValidationError: On 422 responses
            APIError: On other error responses or timeout
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        # Use provided timeout or fall back to default
        request_timeout = timeout or self.timeout

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=httpx.Timeout(request_timeout)
                )

                # Handle success
                if 200 <= response.status_code < 300:
                    return response.json()

                # Handle errors
                self._handle_error(response)

            except httpx.TimeoutException:
                # Include timeout context in error
                error_msg = (
                    f"Request timed out after {request_timeout}s "
                    f"on attempt {attempt + 1}/{self.max_retries}"
                )
                
                if attempt == self.max_retries - 1:
                    # Last attempt, raise error with full context
                    raise APIError(
                        error_msg,
                        status_code=408,
                        response={
                            "timeout_seconds": request_timeout,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                        }
                    ) from None
                
                # Retry with backoff
                await self._backoff(attempt)

            except httpx.NetworkError:
                if attempt == self.max_retries - 1:
                    raise APIError("Network error", status_code=503)
                await self._backoff(attempt)

        raise APIError("Max retries exceeded", status_code=503)

    def _handle_error(self, response: httpx.Response):
        """
        Parse error response and raise appropriate exception.
        
        Args:
            response: HTTP response object
            
        Raises:
            Appropriate error based on status code
        """
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
        """
        Exponential backoff between retries.
        
        Args:
            attempt: Retry attempt number (0-indexed)
        """
        delay = min(2 ** attempt, 10)  # Max 10 seconds
        await asyncio.sleep(delay)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()