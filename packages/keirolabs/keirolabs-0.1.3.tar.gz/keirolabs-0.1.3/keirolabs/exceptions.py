"""
KEIRO SDK Exceptions
"""


class KeiroError(Exception):
    """Base exception for all KEIRO SDK errors"""
    pass


class KeiroAPIError(KeiroError):
    """Raised when an API request fails"""
    pass


class KeiroAuthError(KeiroError):
    """Raised when authentication fails (invalid API key)"""
    pass


class KeiroRateLimitError(KeiroError):
    """Raised when rate limit is exceeded or out of credits"""
    pass


class KeiroValidationError(KeiroError):
    """Raised when request validation fails"""
    pass


class KeiroConnectionError(KeiroError):
    """Raised when connection to API fails"""
    pass
