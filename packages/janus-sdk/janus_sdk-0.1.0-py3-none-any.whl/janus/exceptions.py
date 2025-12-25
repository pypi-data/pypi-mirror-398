class JanusError(Exception):
    """Base exception for Janus SDK."""


class JanusConnectionError(JanusError):
    """Raised when unable to connect to Janus API."""


class JanusAuthError(JanusError):
    """Raised when authentication fails."""


class JanusRateLimitError(JanusError):
    """Raised when rate limit is exceeded."""
