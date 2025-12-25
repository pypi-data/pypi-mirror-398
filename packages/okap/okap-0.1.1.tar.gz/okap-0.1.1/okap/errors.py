"""OKAP exceptions."""


class OkapError(Exception):
    """Base exception for OKAP errors."""
    pass


class AccessDeniedError(OkapError):
    """Raised when access is denied by user or vault."""
    
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


class VaultError(OkapError):
    """Raised when there's an error communicating with the vault."""
    pass


class TokenExpiredError(OkapError):
    """Raised when a token has expired."""
    pass


class RateLimitError(OkapError):
    """Raised when rate limit is exceeded."""
    pass


class SpendLimitError(OkapError):
    """Raised when spend limit is exceeded."""
    pass


class InvalidTokenError(OkapError):
    """Raised when token is invalid or revoked."""
    pass
