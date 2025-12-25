"""Requests module interfaces."""

from __future__ import annotations

import time
from typing import Any, Callable

import requests

from .utils.errors import RequestTimeoutError, map_api_error
from .utils.types import InteractionResponse, build_interaction_response

HeaderProvider = Callable[[dict[str, str | None]], dict[str, str]]


class RequestsClient:
    """Inspect asynchronous requests triggered by the SDK."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        self._base_url = api_url.rstrip("/")
        self._session = session or requests.Session()
        self._header_provider = header_provider

    def get(self, request_id: str, *, timeout: float | None = None) -> dict[str, Any]:
        """Retrieve the status of a specific request."""

        return self._perform_get(f"/api/v1/requests/{request_id}", timeout=timeout)

    def events(self, request_id: str, *, timeout: float | None = None) -> list[dict[str, Any]]:
        """Return events emitted by a request."""

        payload = self._perform_get(
            f"/api/v1/requests/{request_id}/events",
            timeout=timeout,
        )
        data = payload.get("data") or []
        return data if isinstance(data, list) else []

    def wait(
        self,
        request_id: str,
        *,
        interval: float = 1.0,
        timeout: float = 60.0,
    ) -> InteractionResponse:
        """Block until a request finishes and return its payload."""

        deadline = time.monotonic() + timeout
        while True:
            payload = self.get(request_id)
            data = payload.get("data") or {}
            state = str(
                data.get("status")
                or data.get("state")
                or payload.get("status")
                or payload.get("state")
                or ""
            ).lower()

            if state in {"completed", "success", "succeeded", "done"}:
                response_payload = self._extract_response_payload(data)
                meta = payload.get("meta") or {}
                return build_interaction_response(response_payload, meta)

            if state in {"failed", "error", "cancelled"}:
                error_payload = payload.get("error") or data.get("error")
                raise map_api_error(500, {"error": error_payload or {"message": "Request failed"}})

            if time.monotonic() >= deadline:
                raise RequestTimeoutError(
                    f"Request {request_id} did not complete within {timeout} seconds"
                )

            time.sleep(max(interval, 0.1))

    def _perform_get(self, path: str, *, timeout: float | None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.get(url, headers=self._header_provider(), timeout=timeout)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise map_api_error(500, {"error": {"message": str(exc)}}) from exc

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

        if not isinstance(payload, dict):
            return {"data": payload}

        status_flag = str(payload.get("status") or "").lower()
        if status_flag in {"error", "failed", "failure"}:
            raise map_api_error(response.status_code, payload)

        return payload

    @staticmethod
    def _extract_response_payload(data: dict[str, Any]) -> dict[str, Any]:
        if isinstance(data.get("response"), dict):
            return data["response"]
        if isinstance(data.get("result"), dict):
            return data["result"]
        return data
