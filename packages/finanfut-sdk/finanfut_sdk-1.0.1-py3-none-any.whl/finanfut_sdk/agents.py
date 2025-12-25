"""Agents module implementation."""

from __future__ import annotations

from typing import Any

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import Agent


class AgentsClient(BaseApiClient):
    """Interact with registered agents."""

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
        *,
        application_id: str | None = None,
        timeout: float | None = None,
    ) -> list[Agent]:
        """Return all agents available for the application."""

        path = (
            f"/api/v1/applications/{application_id}/agents"
            if application_id
            else "/api/v1/agents"
        )
        payload = self._request("GET", path, timeout=timeout)
        data = self._extract_data(payload)
        if isinstance(data, list):
            return [Agent.model_validate(item) for item in data]
        if isinstance(data, dict):
            return [Agent.model_validate(data)]
        return []

    def get(
        self,
        agent_id: str,
        *,
        application_id: str | None = None,
        timeout: float | None = None,
    ) -> Agent:
        """Retrieve a single agent by identifier."""

        path = (
            f"/api/v1/applications/{application_id}/agents/{agent_id}"
            if application_id
            else f"/api/v1/agents/{agent_id}"
        )
        payload = self._request("GET", path, timeout=timeout)
        data: dict[str, Any] = self._extract_data(payload)
        return Agent.model_validate(data)
