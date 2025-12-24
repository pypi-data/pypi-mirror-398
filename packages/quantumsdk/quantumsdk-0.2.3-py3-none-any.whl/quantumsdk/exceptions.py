from __future__ import annotations

from typing import Any, Optional


class QuantumSDKError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class ClientInitializationError(QuantumSDKError):
    """Raised when the HTTP client fails to initialize properly."""


class AuthenticationError(QuantumSDKError):
    """Raised when authentication fails or credentials are invalid."""


class ValidationError(QuantumSDKError):
    """Raised when the API reports validation issues."""


class NotFoundError(QuantumSDKError):
    """Raised when a requested resource is not found."""


class ConflictError(QuantumSDKError):
    """Raised when the API reports a conflict (HTTP 409)."""


class ServerError(QuantumSDKError):
    """Raised for 5xx server-side errors."""


class TransportError(QuantumSDKError):
    """Raised for lower-level transport issues (network errors, timeouts, etc.)."""
