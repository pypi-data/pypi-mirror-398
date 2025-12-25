"""Authentication helpers for FinanFut SDK."""

from __future__ import annotations

from typing import Mapping

SDK_NAME = "finanfut-sdk-python"
SDK_VERSION = "0.1.0"
SDK_LANG = "python"


def build_auth_headers(api_key: str, application_id: str) -> dict[str, str]:
    """Construct authentication headers for API requests."""

    return {
        "Authorization": f"Bearer {api_key}",
        "X-Application-Id": application_id,
    }


def build_sdk_headers() -> dict[str, str]:
    """Return default SDK headers identifying the client."""

    return {
        "X-SDK-Lang": SDK_LANG,
        "X-SDK-Version": SDK_VERSION,
        "X-SDK-Name": SDK_NAME,
    }


def build_base_headers() -> dict[str, str]:
    """Return the standard base headers shared across all requests."""

    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def build_request_headers(
    api_key: str, application_id: str, extra: Mapping[str, str | None] | None = None
) -> dict[str, str]:
    """Combine base, auth, SDK, and optional headers into a single mapping."""

    headers = {**build_base_headers(), **build_sdk_headers(), **build_auth_headers(api_key, application_id)}
    if extra:
        headers.update(dict(extra))
    return headers
