"""Error hierarchy for the FinanFut SDK."""

from __future__ import annotations

from typing import Any


class FinanFutApiError(Exception):
    """Base exception for all API related errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(FinanFutApiError):
    """Raised when authentication fails."""


class RateLimitError(FinanFutApiError):
    """Raised when API rate limits are exceeded."""


class BillingError(FinanFutApiError):
    """Raised for billing-related issues."""


class ValidationError(FinanFutApiError):
    """Raised for invalid payloads or parameters."""


class ServerError(FinanFutApiError):
    """Raised when the FinanFut backend reports an error."""


class RequestTimeoutError(FinanFutApiError):
    """Raised when polling for an asynchronous request exceeds the timeout."""


class PermissionError(FinanFutApiError):
    """Raised when the caller is authenticated but not authorized."""


class NotFoundError(FinanFutApiError):
    """Raised when a requested resource cannot be located."""


class ValidationConflictError(ValidationError):
    """Raised when the backend reports a conflict for the payload."""


def map_api_error(status_code: int, payload: dict[str, Any | None] = None) -> FinanFutApiError:
    """Map backend error payloads to the SDK's typed exceptions."""

    error_data: dict[str, Any] = {}
    if isinstance(payload, dict):
        if isinstance(payload.get("error"), dict):
            error_data = payload["error"].copy()
        else:
            error_data = payload.copy()

    message = error_data.get("message") or error_data.get("detail")
    if not message:
        message = f"Request failed with status code {status_code}"

    error_code = (error_data.get("code") or "").lower()

    if status_code == 401:
        return AuthenticationError(message, status_code)
    if status_code == 403:
        return PermissionError(message, status_code)
    if status_code == 402 or error_code == "billing_error":
        return BillingError(message, status_code)
    if status_code == 429 or error_code == "rate_limit":
        return RateLimitError(message, status_code)
    if status_code == 404:
        return NotFoundError(message, status_code)
    if status_code == 409:
        return ValidationConflictError(message, status_code)
    if status_code == 400 or error_code == "validation_error":
        return ValidationError(message, status_code)
    if status_code >= 500:
        return ServerError(message, status_code)
    return FinanFutApiError(message, status_code)
