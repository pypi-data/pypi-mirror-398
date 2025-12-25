"""Interact module for unified API calls."""

from __future__ import annotations

from typing import Any, Callable

import requests

from .utils.errors import map_api_error
from .utils.types import InteractionResponse, build_interaction_response

HeaderProvider = Callable[[dict[str, str | None]], dict[str, str]]


class InteractClient:
    """Client wrapper for the `/api/v1/interact` endpoint."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
        dry_run: bool = False,
    ) -> None:
        self._base_url = api_url.rstrip("/")
        self._session = session or requests.Session()
        self._header_provider = header_provider
        self._dry_run = dry_run

    def query(
        self,
        query: str,
        *,
        application_agent_id: str | None = None,
        intent_id: str | None = None,
        context_id: str | None = None,
        mode: str | None = None,
        execution_mode: str = "sync",
        stream: bool = False,
        extras: dict[str, Any | None] = None,
        timeout: float | None = None,
    ) -> InteractionResponse:
        """Execute a synchronous interaction request."""

        payload = self._build_payload(
            query=query,
            application_agent_id=application_agent_id,
            intent_id=intent_id,
            context_id=context_id,
            mode=mode,
            execution_mode=execution_mode,
            stream=stream,
            extras=extras,
        )

        response = self._execute(payload, timeout=timeout)
        data = response.get("data") or response
        meta = response.get("meta") or response.get("metadata") or {}
        return build_interaction_response(data, meta)

    def async_query(
        self,
        query: str,
        *,
        application_agent_id: str | None = None,
        intent_id: str | None = None,
        context_id: str | None = None,
        mode: str | None = None,
        extras: dict[str, Any | None] = None,
        timeout: float | None = None,
    ) -> str:
        """Start an asynchronous interaction and return a request identifier.

        The returned ``request_id`` can be consumed via :class:`RequestsClient`
        helpers such as :meth:`RequestsClient.wait`.
        """

        payload = self._build_payload(
            query=query,
            application_agent_id=application_agent_id,
            intent_id=intent_id,
            context_id=context_id,
            mode=mode,
            execution_mode="async",
            stream=False,
            extras=extras,
        )
        response = self._execute(payload, timeout=timeout)
        request_id = (
            (response.get("data") or {}).get("request_id")
            or (response.get("meta") or {}).get("request_id")
            or response.get("request_id")
        )
        if not request_id:
            raise map_api_error(500, {"error": {"message": "Backend response is missing request_id"}})
        return str(request_id)

    def stream(self, *_: Any, **__: Any) -> InteractionResponse:
        """Stream the interaction response back to the caller."""

        raise NotImplementedError("Streaming interactions are not yet supported.")

    def _build_payload(
        self,
        *,
        query: str,
        application_agent_id: str | None,
        intent_id: str | None,
        context_id: str | None,
        mode: str | None,
        execution_mode: str,
        stream: bool,
        extras: dict[str, Any | None],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query,
            "execution_mode": execution_mode,
            "stream": stream,
        }
        if mode is not None:
            payload["mode"] = mode
        if application_agent_id:
            payload["application_agent_id"] = application_agent_id
        if intent_id is not None:
            payload["intent_id"] = intent_id
        if context_id:
            payload["context_id"] = context_id
        if self._dry_run:
            payload["dry_run"] = True
        if extras is not None:
            payload["extras"] = extras
        return payload

    def _execute(self, payload: dict[str, Any], timeout: float | None) -> dict[str, Any]:
        url = f"{self._base_url}/api/v1/interact"
        try:
            response = self._session.post(
                url,
                json=payload,
                headers=self._header_provider(),
                timeout=timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise map_api_error(500, {"error": {"message": str(exc)}}) from exc

        return self._parse_response(response)

    def _parse_response(self, response: requests.Response) -> dict[str, Any]:
        try:
            if response.status_code == 204 or not response.content:
                payload: Any = {}
            else:
                payload = response.json()
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

        return payload
