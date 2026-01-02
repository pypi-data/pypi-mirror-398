class ZenithAuthError(Exception):
    """Base exception for all ZenithAuth errors."""
    pass

class InvalidCredentialsError(ZenithAuthError):
    pass

class TokenExpiredError(ZenithAuthError):
    pass

class RevokedTokenError(ZenithAuthError):
    pass

class InsufficientPermissionsError(ZenithAuthError):
    pass