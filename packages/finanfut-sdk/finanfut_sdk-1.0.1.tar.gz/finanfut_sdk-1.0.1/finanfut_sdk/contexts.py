"""Contexts module implementation."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Sequence, Union

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import (
    ContextDetail,
    ContextDocumentLink,
    ContextList,
    ContextSessionDetail,
    ContextSessionList,
    ContextSessionMessage,
)

DocumentReference = Union[str, Mapping[str, Any], ContextDocumentLink]


class ContextsClient(BaseApiClient):
    """Manage persistent contexts that aggregate document links."""

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
        offset: int = 0,
        limit: int = 50,
        timeout: float | None = None,
    ) -> ContextList:
        """Return paginated contexts for the authenticated application."""

        payload = self._request(
            "GET",
            "/api/v1/contexts",
            params={"offset": offset, "limit": limit},
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return ContextList.model_validate(data)

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        status: str | None = None,
        metadata: Mapping[str, Any | None] | None = None,
        documents: Sequence[DocumentReference | None] = None,
        timeout: float | None = None,
    ) -> ContextDetail:
        """Create a new context with optional linked documents."""

        body: MutableMapping[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if status is not None:
            body["status"] = status
        if metadata is not None:
            body["metadata"] = dict(metadata)
        if documents is not None:
            body["documents"] = self._normalize_documents(documents)

        payload = self._request("POST", "/api/v1/contexts", json=body, timeout=timeout)
        data = self._extract_data(payload)
        return ContextDetail.model_validate(data)

    def get(self, context_id: Union[str, ContextDetail], *, timeout: float | None = None) -> ContextDetail:
        """Retrieve a single context."""

        identifier = context_id.id if isinstance(context_id, ContextDetail) else context_id
        payload = self._request("GET", f"/api/v1/contexts/{identifier}", timeout=timeout)
        data = self._extract_data(payload)
        return ContextDetail.model_validate(data)

    def add_documents(
        self,
        context_id: Union[str, ContextDetail],
        documents: Sequence[DocumentReference],
        *,
        timeout: float | None = None,
    ) -> ContextDetail:
        """Attach additional documents to an existing context."""

        identifier = context_id.id if isinstance(context_id, ContextDetail) else context_id
        body = {"documents": self._normalize_documents(documents)}
        payload = self._request(
            "POST", f"/api/v1/contexts/{identifier}/documents", json=body, timeout=timeout
        )
        data = self._extract_data(payload)
        return ContextDetail.model_validate(data)

    def update(
        self,
        context_id: Union[str, ContextDetail],
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        metadata: Mapping[str, Any | None] | None = None,
        documents: Sequence[DocumentReference | None] = None,
        timeout: float | None = None,
    ) -> ContextDetail:
        """Update the context metadata or its associated documents."""

        identifier = context_id.id if isinstance(context_id, ContextDetail) else context_id
        body: MutableMapping[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if status is not None:
            body["status"] = status
        if metadata is not None:
            body["metadata"] = dict(metadata)
        if documents is not None:
            body["documents"] = self._normalize_documents(documents)

        payload = self._request(
            "PATCH",
            f"/api/v1/contexts/{identifier}",
            json=body,
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return ContextDetail.model_validate(data)

    def delete(self, context_id: Union[str, ContextDetail], *, timeout: float | None = None) -> None:
        """Remove a context and its document associations."""

        identifier = context_id.id if isinstance(context_id, ContextDetail) else context_id
        self._request(
            "DELETE",
            f"/api/v1/contexts/{identifier}",
            timeout=timeout,
            expect_json=False,
        )

    def _normalize_documents(self, documents: Sequence[DocumentReference]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for entry in documents:
            if isinstance(entry, ContextDocumentLink):
                normalized.append(
                    {
                        "document_id": str(entry.document_id),
                        "metadata": dict(entry.metadata),
                    }
                )
                continue
            if isinstance(entry, Mapping):
                document_id = entry.get("document_id") or entry.get("id")
                metadata = entry.get("metadata") or entry.get("metadata_")
                normalized.append(
                    {
                        "document_id": str(document_id),
                        "metadata": dict(metadata or {}),
                    }
                )
                continue
            normalized.append({"document_id": str(entry), "metadata": {}})
        return normalized


class ContextSessionsClient(BaseApiClient):
    """Manage runtime sessions that reuse existing contexts."""

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
        offset: int = 0,
        limit: int = 50,
        timeout: float | None = None,
    ) -> ContextSessionList:
        payload = self._request(
            "GET",
            "/api/v1/context-sessions",
            params={"offset": offset, "limit": limit},
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return ContextSessionList.model_validate(data)

    def create(
        self,
        *,
        name: str,
        context_id: str | None = None,
        status: str = "active",
        metadata: Mapping[str, Any | None] | None = None,
        timeout: float | None = None,
    ) -> ContextSessionDetail:
        body: MutableMapping[str, Any] = {"name": name, "status": status}
        if context_id is not None:
            body["context_id"] = context_id
        if metadata is not None:
            body["metadata"] = dict(metadata)
        payload = self._request("POST", "/api/v1/context-sessions", json=body, timeout=timeout)
        data = self._extract_data(payload)
        return ContextSessionDetail.model_validate(data)

    def get(self, session_id: str, *, timeout: float | None = None) -> ContextSessionDetail:
        payload = self._request(
            "GET", f"/api/v1/context-sessions/{session_id}", timeout=timeout
        )
        data = self._extract_data(payload)
        return ContextSessionDetail.model_validate(data)

    def add_message(
        self,
        session_id: str,
        *,
        agent_name: str,
        intent: str | None = None,
        role: str = "assistant",
        query: str | None = None,
        answer: str | None = None,
        tokens_used: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        context_id: str | None = None,
        metadata: Mapping[str, Any | None] | None = None,
        timeout: float | None = None,
    ) -> ContextSessionMessage:
        body: MutableMapping[str, Any] = {
            "agent_name": agent_name,
            "role": role,
            "tokens_used": tokens_used,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        if intent is not None:
            body["intent"] = intent
        if query is not None:
            body["query"] = query
        if answer is not None:
            body["answer"] = answer
        if context_id is not None:
            body["context_id"] = context_id
        if metadata is not None:
            body["metadata"] = dict(metadata)

        payload = self._request(
            "POST",
            f"/api/v1/context-sessions/{session_id}/messages",
            json=body,
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return ContextSessionMessage.model_validate(data)

    # Backwards compatibility alias
    append_message = add_message

    def delete(self, session_id: str, *, timeout: float | None = None) -> None:
        self._request(
            "DELETE",
            f"/api/v1/context-sessions/{session_id}",
            timeout=timeout,
            expect_json=False,
        )
