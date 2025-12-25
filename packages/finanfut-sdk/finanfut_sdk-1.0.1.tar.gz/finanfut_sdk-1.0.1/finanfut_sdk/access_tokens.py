"""Access tokens module implementation."""

from __future__ import annotations

from typing import Any, Union

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import AccessToken, AccessTokenCreateRequest, AccessTokenListResponse


class AccessTokensClient(BaseApiClient):
    """Manage rotating access tokens for the current account."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)

    def list(self, *, timeout: float | None = None) -> AccessTokenListResponse:
        """Return all active access tokens."""

        payload = self._request("GET", "/api/v1/access-tokens", timeout=timeout)
        data = self._extract_data(payload)
        if isinstance(data, list):
            data = {"items": data}
        return AccessTokenListResponse.model_validate(data)

    def create(
        self,
        description: str | None = None,
        scopes: list[str | None] = None,
        payload: AccessTokenCreateRequest | dict[str, Any | None] | None = None,
        *,
        timeout: float | None = None,
    ) -> AccessToken:
        """Create and return a new access token descriptor."""

        if payload is not None:
            body = (
                payload.model_dump(exclude_none=True)
                if isinstance(payload, AccessTokenCreateRequest)
                else {k: v for k, v in dict(payload).items() if v is not None}
            )
        else:
            body = {"description": description, "scopes": scopes or []}
        api_payload = self._request(
            "POST", "/api/v1/access-tokens", json=body or None, timeout=timeout
        )
        data: dict[str, Any] = self._extract_data(api_payload)
        return AccessToken.model_validate(data)

    def revoke(self, token_id: str, *, timeout: float | None = None) -> None:
        """Revoke an existing access token."""

        self._request(
            "DELETE", f"/api/v1/access-tokens/{token_id}", timeout=timeout, expect_json=False
        )
