from typing import Optional, Dict


# ============================================
# EXCEPTIONS
# ============================================

class OneRouterError(Exception):
    """Base exception for all OneRouter errors"""
    pass


class AuthenticationError(OneRouterError):
    """API key is invalid or missing"""
    pass


class RateLimitError(OneRouterError):
    """Rate limit exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ValidationError(OneRouterError):
    """Request validation failed"""
    pass


class APIError(OneRouterError):
    """Generic API error"""
    def __init__(self, message: str, status_code: int, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response