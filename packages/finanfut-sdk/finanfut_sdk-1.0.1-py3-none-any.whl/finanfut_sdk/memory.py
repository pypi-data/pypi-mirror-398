"""Memory module implementation."""

from __future__ import annotations

from typing import Any, Mapping, Union

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import MemoryQueryResponse, MemoryRecord, MemorySettings
Payload = dict[str, Any]


class MemorySettingsClient(BaseApiClient):
    """Manage application-level memory settings."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)

    def get(self, application_id: str, *, timeout: float | None = None) -> MemorySettings:
        path = f"/api/v1/memory/settings/{application_id}"
        payload = self._request("GET", path, timeout=timeout)
        data: Payload = self._extract_data(payload)
        return MemorySettings.model_validate(data)

    def update(
        self,
        application_id: str,
        settings: Union[MemorySettings, Mapping[str, Any]],
        *,
        timeout: float | None = None,
    ) -> MemorySettings:
        path = f"/api/v1/memory/settings/{application_id}"
        body = self._coerce_payload(settings)
        payload = self._request("PUT", path, json=body, timeout=timeout)
        data: Payload = self._extract_data(payload)
        return MemorySettings.model_validate(data)

    def _coerce_payload(
        self, settings: Union[MemorySettings, Mapping[str, Any]]
    ) -> dict[str, Any]:
        if isinstance(settings, MemorySettings):
            return settings.model_dump(exclude_none=True)
        return {k: v for k, v in dict(settings).items() if v is not None}

class MemoryRecordsClient(BaseApiClient):
    """Manage memory records for each application agent."""

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
        application_id: str,
        application_agent_id: str,
        *,
        timeout: float | None = None,
    ) -> list[MemoryRecord]:
        path = self._records_path(application_id, application_agent_id)
        payload = self._request("GET", path, timeout=timeout)
        data = self._extract_data(payload)
        records_payload = data.get("records") if isinstance(data, dict) else data
        if isinstance(records_payload, list):
            return [MemoryRecord.model_validate(item) for item in records_payload]
        if isinstance(records_payload, dict):
            return [MemoryRecord.model_validate(records_payload)]
        return []

    def query(
        self,
        application_id: str,
        application_agent_id: str,
        query: str,
        *,
        timeout: float | None = None,
    ) -> MemoryQueryResponse:
        payload = self._request(
            "POST",
            "/api/v1/memory/records/query",
            json={
                "application_id": application_id,
                "application_agent_id": application_agent_id,
                "query": query,
            },
            timeout=timeout,
        )
        data = self._extract_data(payload)
        if isinstance(data, list):
            data = {"records": data}
        return MemoryQueryResponse.model_validate(data)

    def create(
        self,
        application_id: str,
        application_agent_id: str,
        record: Union[MemoryRecord, Mapping[str, Any]],
        *,
        timeout: float | None = None,
    ) -> MemoryRecord:
        path = self._records_path(application_id, application_agent_id)
        body = self._coerce_payload(record)
        payload = self._request("POST", path, json=body, timeout=timeout)
        data: Payload = self._extract_data(payload)
        return MemoryRecord.model_validate(data)

    def delete(
        self,
        application_id: str,
        application_agent_id: str,
        record_id: str,
        *,
        timeout: float | None = None,
    ) -> None:
        path = f"{self._records_path(application_id, application_agent_id)}/{record_id}"
        self._request("DELETE", path, timeout=timeout, expect_json=False)

    def _records_path(self, application_id: str, application_agent_id: str) -> str:
        return f"/api/v1/memory/records/{application_id}/{application_agent_id}"

    def _coerce_payload(
        self, record: Union[MemoryRecord, Mapping[str, Any]]
    ) -> dict[str, Any]:
        if isinstance(record, MemoryRecord):
            return record.model_dump(exclude_none=True)
        return {k: v for k, v in dict(record).items() if v is not None}



class MemoryClient:
    """Entry point for memory operations."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        self._settings = MemorySettingsClient(
            api_url=api_url, session=session, header_provider=header_provider
        )
        self._records = MemoryRecordsClient(
            api_url=api_url, session=session, header_provider=header_provider
        )

    @property
    def settings(self) -> MemorySettingsClient:
        return self._settings

    @property
    def records(self) -> MemoryRecordsClient:
        return self._records
