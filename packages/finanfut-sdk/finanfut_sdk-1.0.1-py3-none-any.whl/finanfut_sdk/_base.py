"""Shared HTTP utilities for API clients."""

from __future__ import annotations

from typing import Any, Callable, Mapping

import requests

from .utils.errors import map_api_error

HeaderProvider = Callable[[dict[str, str | None]], dict[str, str]]


class BaseApiClient:
    """Base class wiring the HTTP session, headers and error handling."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None,
        header_provider: HeaderProvider,
    ) -> None:
        self._base_url = api_url.rstrip("/")
        self._session = session or requests.Session()
        self._header_provider = header_provider

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any | None] | None = None,
        json: Mapping[str, Any | None] | None = None,
        data: Mapping[str, Any | None] | None = None,
        files: Mapping[str, Any | None] | None = None,
        headers: dict[str, str | None] | None = None,
        timeout: float | None = None,
        expect_json: bool = True,
    ) -> Any:
        url = f"{self._base_url}{path}"
        resolved_headers = dict(self._header_provider(headers))
        if files:
            # Multipart requests must not send an explicit JSON content-type header.
            resolved_headers.pop("Content-Type", None)
        filtered_params = {k: v for k, v in (params or {}).items() if v is not None}
        try:
            response = self._session.request(
                method,
                url,
                params=filtered_params or None,
                json=json,
                data=data,
                files=files,
                headers=resolved_headers,
                timeout=timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise map_api_error(500, {"error": {"message": str(exc)}}) from exc

        if not expect_json:
            if response.status_code >= 400:
                raise map_api_error(response.status_code, self._error_payload(response))
            return {}

        if response.status_code == 204 or not response.content:
            if response.status_code >= 400:
                raise map_api_error(response.status_code, self._error_payload(response))
            return {}

        try:
            payload: Any = response.json()
        except ValueError:
            text_body = (response.text or "").strip()
            payload = {} if not text_body else text_body

        if response.status_code >= 400:
            error_payload: Any = payload
            if not isinstance(error_payload, dict):
                error_payload = {"error": {"message": str(error_payload)}}
            raise map_api_error(response.status_code, error_payload)

        if isinstance(payload, (dict, list)):
            return payload

        return {"data": payload}

    @staticmethod
    def _error_payload(response: requests.Response) -> dict[str, Any]:
        message = response.text or f"Request failed with status code {response.status_code}"
        return {"error": {"message": message}}

    @staticmethod
    def _extract_data(payload: Any) -> Any:
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload
