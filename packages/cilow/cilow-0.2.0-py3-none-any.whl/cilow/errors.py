"""
Cilow SDK Error Classes
"""


class CilowError(Exception):
    """Base exception for Cilow SDK errors"""
    pass


class ConnectionError(CilowError):
    """Failed to connect to Cilow API"""
    pass


class AuthenticationError(CilowError):
    """Authentication failed"""
    pass


class NotFoundError(CilowError):
    """Resource not found"""
    pass


class ValidationError(CilowError):
    """Request validation failed"""
    pass


class RateLimitError(CilowError):
    """Rate limit exceeded"""
    pass
