"""Applications module implementation."""

from __future__ import annotations

from typing import Any

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import Application, ApplicationAgent, ApplicationAgentList


class ApplicationAgentsClient(BaseApiClient):
    """Manage application-scoped agent resources."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)

    def list(
        self, application_id: str, *, offset: int = 0, limit: int = 50, timeout: float | None = None
    ) -> ApplicationAgentList:
        """Return agents configured for a specific application."""

        payload = self._request(
            "GET",
            f"/api/v1/applications/{application_id}/agents",
            params={"offset": offset, "limit": limit},
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return ApplicationAgentList.model_validate(data)

    def get(
        self, application_id: str, application_agent_id: str, *, timeout: float | None = None
    ) -> ApplicationAgent:
        """Fetch a single application agent."""

        payload = self._request(
            "GET",
            f"/api/v1/applications/{application_id}/agents/{application_agent_id}",
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return ApplicationAgent.model_validate(data)


class ApplicationsClient(BaseApiClient):
    """Manage applications linked to the account."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)
        self._agents = ApplicationAgentsClient(
            api_url=api_url, session=session, header_provider=header_provider
        )

    def list(self, *, timeout: float | None = None) -> list[Application]:
        """List available applications for the API key."""

        payload = self._request("GET", "/api/v1/applications", timeout=timeout)
        data = self._extract_data(payload)
        if isinstance(data, list):
            return [Application.model_validate(item) for item in data]
        if isinstance(data, dict):
            return [Application.model_validate(data)]
        return []

    def get(self, application_id: str, *, timeout: float | None = None) -> Application:
        """Fetch a single application by identifier."""

        payload = self._request(
            "GET", f"/api/v1/applications/{application_id}", timeout=timeout
        )
        data: dict[str, Any] = self._extract_data(payload)
        return Application.model_validate(data)

    @property
    def agents(self) -> ApplicationAgentsClient:
        """Access application-specific agent helpers."""

        return self._agents
