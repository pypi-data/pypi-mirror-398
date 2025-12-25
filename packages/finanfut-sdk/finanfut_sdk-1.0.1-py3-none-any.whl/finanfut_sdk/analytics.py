"""Analytics and developer logs module."""

from __future__ import annotations

from typing import Any, Mapping

import requests

from ._base import BaseApiClient, HeaderProvider

JsonDict = dict[str, Any]


class AnalyticsClient(BaseApiClient):
    """Access developer logs and request analytics."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)

    def logs(
        self,
        *,
        filters: Mapping[str, Any | None] | None = None,
        timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        """Return developer logs for the current application."""

        payload = self._request(
            "GET",
            "/api/v1/analytics/logs",
            params=dict(filters or {}),
            timeout=timeout,
        )
        return self._coerce_list(self._extract_data(payload))

    def requests(
        self,
        *,
        filters: Mapping[str, Any | None] | None = None,
        timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        """Return developer request diagnostics."""

        payload = self._request(
            "GET",
            "/api/v1/analytics/requests",
            params=dict(filters or {}),
            timeout=timeout,
        )
        return self._coerce_list(self._extract_data(payload))

    def _coerce_list(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [dict(item) for item in data]
        if isinstance(data, dict):
            return [dict(data)]
        return []
