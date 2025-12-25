"""Documents client implementation."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, Union

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import (
    DocumentAnswer,
    DocumentDetail,
    DocumentFile,
    DocumentParsedResponse,
    DocumentProcessingResponse,
    DocumentRunsResponse,
    DocumentType,
    DocumentTypeDetail,
)

Payload = dict[str, Any]


class DocumentsClient(BaseApiClient):
    """Manage the document QA pipeline and processing endpoints."""

    _DOCUMENT_QA_BASE = "/api/v1/agents/document-qa"
    _DOCUMENT_PIPELINE_BASE = "/api/v1/documents"

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
        status: str | None = None,
        limit: int | None = None,
        timeout: float | None = None,
    ) -> list[DocumentFile]:
        """Return the latest documents for the current application."""

        params: dict[str, Any] = {}
        if application_id is not None:
            params["application_id"] = application_id
        if status is not None:
            params["document_status"] = status
        if limit is not None:
            params["limit"] = limit
        payload = self._request(
            "GET", f"{self._DOCUMENT_PIPELINE_BASE}", params=params, timeout=timeout
        )
        data = self._extract_data(payload)
        if isinstance(data, list):
            return [DocumentFile.model_validate(item) for item in data]
        if isinstance(data, dict):
            return [DocumentFile.model_validate(data)]
        return []

    def upload(
        self,
        *,
        file_path: Union[str, Path | None] = None,
        content: Union[str, bytes | None] = None,
        text: str | None = None,
        document_id: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        auto_classify: bool = True,
        classification_dry_run: bool = False,
        document_type: str | None = None,
        timeout: float | None = None,
    ) -> DocumentDetail:
        """Upload a document either from disk, raw bytes, or pasted text."""

        files_payload: dict[str, Any | None] = None
        json_payload: dict[str, Any | None] = None
        data_payload: dict[str, Any | None] = None

        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Document not found: {path}")
            resolved_name = file_name or path.name
            resolved_mime = mime_type or mimetypes.guess_type(resolved_name)[0] or "application/octet-stream"
            files_payload = {"file": (resolved_name, path.read_bytes(), resolved_mime)}
            data_payload = {"id": document_id} if document_id else None
        elif content is not None:
            raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
            resolved_name = file_name or "document"
            resolved_mime = mime_type or mimetypes.guess_type(resolved_name)[0] or "application/octet-stream"
            files_payload = {"file": (resolved_name, raw_bytes, resolved_mime)}
            data_payload = {"id": document_id} if document_id else None
        elif text is not None:
            if not text.strip():
                raise ValueError("text content cannot be empty")
            json_payload = {
                "text_content": text,
                "file_name": file_name or "pasted-text.txt",
                "mime_type": mime_type or "text/plain",
            }
            if document_id:
                json_payload["id"] = document_id
        else:
            raise ValueError("file_path, content, or text must be provided")

        params = {
            "auto_classify": str(bool(auto_classify)).lower(),
            "classification_dry_run": str(bool(classification_dry_run)).lower(),
        }

        document_type_key = "document_type_override"
        if document_type is not None:
            if json_payload is not None:
                json_payload[document_type_key] = document_type
            if files_payload is not None:
                if data_payload is None:
                    data_payload = {}
                data_payload[document_type_key] = document_type
            params[document_type_key] = document_type

        response = self._request(
            "POST",
            f"{self._DOCUMENT_QA_BASE}/files",
            json=json_payload,
            data=data_payload,
            files=files_payload,
            params=params,
            timeout=timeout,
        )
        data = self._extract_data(response)
        return DocumentDetail.model_validate(data)

    def get(
        self,
        document_id: str,
        *,
        include_binary: bool = False,
        timeout: float | None = None,
    ) -> DocumentDetail:
        payload = self._request(
            "GET",
            f"{self._DOCUMENT_QA_BASE}/files/{document_id}",
            params={"include_binary": str(bool(include_binary)).lower()},
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return DocumentDetail.model_validate(data)

    def delete(self, document_id: str, *, timeout: float | None = None) -> None:
        self._request(
            "DELETE",
            f"{self._DOCUMENT_QA_BASE}/files/{document_id}",
            timeout=timeout,
            expect_json=False,
        )

    def ask(
        self,
        document_id: str,
        question: str,
        *,
        timeout: float | None = None,
    ) -> DocumentAnswer:
        payload = self._request(
            "POST",
            f"{self._DOCUMENT_QA_BASE}/query",
            json={"document_id": document_id, "question": question},
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return DocumentAnswer.model_validate(data)

    def process(
        self,
        document_id: str,
        *,
        reprocess: bool = False,
        document_type_override: str | None = None,
        timeout: float | None = None,
    ) -> DocumentProcessingResponse:
        body: Payload = {
            "document_id": document_id,
            "reprocess": reprocess,
        }
        if document_type_override is not None:
            body["document_type_override"] = document_type_override
        payload = self._request(
            "POST",
            f"{self._DOCUMENT_PIPELINE_BASE}/process",
            json=body,
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return DocumentProcessingResponse.model_validate(data)

    def list_processing_runs(
        self, document_id: str, *, timeout: float | None = None
    ) -> DocumentRunsResponse:
        payload = self._request(
            "GET",
            f"{self._DOCUMENT_PIPELINE_BASE}/{document_id}/runs",
            timeout=timeout,
        )
        data = self._extract_data(payload)
        if isinstance(data, list):
            data = {"runs": data}
        return DocumentRunsResponse.model_validate(data)

    def get_parsed(
        self, document_id: str, *, timeout: float | None = None
    ) -> DocumentParsedResponse:
        payload = self._request(
            "GET",
            f"{self._DOCUMENT_PIPELINE_BASE}/{document_id}/parsed",
            timeout=timeout,
        )
        data = self._extract_data(payload)
        if isinstance(data, dict) and "record" not in data:
            data = {"record": data}
        return DocumentParsedResponse.model_validate(data)

    def list_types(self, *, timeout: float | None = None) -> list[DocumentType]:
        payload = self._request(
            "GET",
            f"{self._DOCUMENT_PIPELINE_BASE}/document-pipeline/types",
            timeout=timeout,
        )
        data = self._extract_data(payload)
        items = (data.get("items") if isinstance(data, dict) else data) or []
        return [DocumentType.model_validate(item) for item in items]

    def get_type(
        self, type_identifier: str, *, timeout: float | None = None
    ) -> DocumentTypeDetail:
        payload = self._request(
            "GET",
            f"{self._DOCUMENT_PIPELINE_BASE}/document-pipeline/types/{type_identifier}",
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return DocumentTypeDetail.model_validate(data)

