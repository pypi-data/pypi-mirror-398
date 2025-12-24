class PandaAuthError(Exception):
    """Base class for authentication errors."""

    pass


class TokenNotFoundError(PandaAuthError):
    """Raised when the token file is missing."""

    pass


class TokenExpiredError(PandaAuthError):
    """Raised when the token has already expired."""

    pass


class TokenTooEarlyError(PandaAuthError):
    """Raised when attempting to refresh too early."""

    pass


class AuthConfigError(PandaAuthError):
    """Raised when fetching the auth or endpoint configuration fails."""

    pass


class TokenRefreshError(PandaAuthError):
    """Raised when token refresh fails."""

    pass
