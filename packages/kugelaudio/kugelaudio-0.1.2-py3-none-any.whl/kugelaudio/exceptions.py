"""Exceptions for KugelAudio SDK."""

from typing import Optional


class KugelAudioError(Exception):
    """Base exception for KugelAudio SDK."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(KugelAudioError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class RateLimitError(KugelAudioError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class InsufficientCreditsError(KugelAudioError):
    """Raised when user has insufficient credits."""

    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(message, status_code=403)


class ValidationError(KugelAudioError):
    """Raised when request validation fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class ConnectionError(KugelAudioError):
    """Raised when connection to server fails."""

    def __init__(self, message: str = "Failed to connect to server"):
        super().__init__(message, status_code=503)

