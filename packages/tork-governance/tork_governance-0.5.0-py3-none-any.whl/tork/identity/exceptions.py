"""
Custom exceptions for identity management.
"""


class InvalidTokenError(Exception):
    """Base exception for invalid tokens."""
    pass


class ExpiredTokenError(InvalidTokenError):
    """Exception for expired tokens."""
    pass


class RevokedTokenError(InvalidTokenError):
    """Exception for revoked tokens."""
    pass
