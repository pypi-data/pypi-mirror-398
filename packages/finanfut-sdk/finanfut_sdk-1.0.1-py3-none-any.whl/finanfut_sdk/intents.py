"""Intents module implementation."""

from __future__ import annotations

from typing import Any

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import Intent, normalize_intent_payload


class IntentsClient(BaseApiClient):
    """Interact with available intents."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)

    def list(
        self,
        agent_id: str,
        application_id: str | None = None,
        *,
        timeout: float | None = None,
    ) -> list[Intent]:
        """Return all intents registered for an agent.

        If ``application_id`` is provided, the application-scoped endpoint is used.
        """

        path = (
            f"/api/v1/applications/{application_id}/agents/{agent_id}/intents"
            if application_id
            else f"/api/v1/agents/{agent_id}/intents"
        )
        payload = self._request("GET", path, timeout=timeout)
        data = self._extract_data(payload)
        items = self._coerce_items(data)
        intents: list[Intent] = []
        for item in items:
            normalized = self._normalize_intent_payload(item)
            if normalized is None:
                continue
            intents.append(Intent.model_validate(normalized))
        return intents

    @staticmethod
    def _coerce_items(payload: Any) -> list[Any]:
        """Extract intent collections from varying backend payload shapes."""

        if isinstance(payload, dict):
            if "intents" in payload and isinstance(payload["intents"], list):
                return payload["intents"]
            if "items" in payload and isinstance(payload["items"], list):
                return payload["items"]
            return [payload]
        if isinstance(payload, list):
            return payload
        return []

    @staticmethod
    def _normalize_intent_payload(item: Any) -> dict[str, Any | None]:
        """Flatten nested intent payloads so SDK models receive full metadata."""

        return normalize_intent_payload(item)
