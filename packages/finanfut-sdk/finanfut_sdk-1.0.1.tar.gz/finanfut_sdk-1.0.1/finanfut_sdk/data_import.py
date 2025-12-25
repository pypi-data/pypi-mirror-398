"""Helpers for transient CSV ingestion and contract transformations."""

from __future__ import annotations

import base64
import copy
from pathlib import Path
from typing import Any, Mapping

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import (
    DataTransformResponse,
    TabularPreview,
    TransientCSVUpload,
)


class DataImportClient(BaseApiClient):
    """Utilities to preview CSV content and transform it to contract JSON."""

    _TRANSIENT_UPLOAD_PATH = "/api/v1/agents/document-qa/transient-upload"
    _PUBLIC_REQUESTS_PATH = "/api/v1/public/requests"

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)

    # ------------------------------------------------------------------
    # Transient CSV uploads
    # ------------------------------------------------------------------
    def upload_transient_csv(
        self,
        *,
        file_path: str | Path | None = None,
        content: bytes | str | None = None,
        text: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        preview_rows: int | None = None,
        timeout: float | None = None,
    ) -> TransientCSVUpload:
        """Upload a CSV as a transient payload and obtain a preview.

        The backend accepts either a multipart file (``file_path``/``content``) or
        pasted text (``text``). When ``content`` is provided directly, the SDK
        base64-encodes it to mirror the JSON upload path.
        """

        provided = [value for value in (file_path, content, text) if value is not None]
        if len(provided) != 1:
            raise ValueError("Provide exactly one of file_path, content, or text")

        params: dict[str, Any] = {}
        if preview_rows is not None:
            params["preview_rows"] = preview_rows

        files_payload: dict[str, Any] | None = None
        json_payload: dict[str, Any] | None = None

        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"CSV not found: {path}")
            resolved_name = file_name or path.name
            resolved_mime = mime_type or "text/csv"
            files_payload = {"file": (resolved_name, path.read_bytes(), resolved_mime)}
        elif isinstance(content, bytes):
            encoded = base64.b64encode(content).decode("utf-8")
            json_payload = {
                "content_base64": encoded,
                "file_name": file_name or "data.csv",
                "mime_type": mime_type or "text/csv",
            }
        elif isinstance(content, str):
            encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            json_payload = {
                "content_base64": encoded,
                "file_name": file_name or "data.csv",
                "mime_type": mime_type or "text/csv",
            }
        elif text is not None:
            json_payload = {
                "text_content": text,
                "file_name": file_name or "pasted-text.csv",
                "mime_type": mime_type or "text/csv",
            }

        payload = self._request(
            "POST",
            self._TRANSIENT_UPLOAD_PATH,
            params=params,
            files=files_payload,
            json=json_payload,
            timeout=timeout,
        )
        data = self._extract_data(payload)
        return TransientCSVUpload.model_validate(data)

    # ------------------------------------------------------------------
    # Transformations
    # ------------------------------------------------------------------
    def transform_data(
        self,
        *,
        application_id: str,
        intent_id: str,
        transient_csv: Mapping[str, Any] | TransientCSVUpload,
        prompt: str = "Transforma el CSV al contracte JSON",
        agent_slug: str | None = "data_transformer_agent",
        agent_id: str | None = None,
        application_agent_id: str | None = None,
        contract_document_id: str | None = None,
        contract_name: str | None = None,
        parameters: dict[str, Any] | None = None,
        stream: bool = False,
        timeout: float | None = None,
    ) -> DataTransformResponse:
        """Invoke the ``transform_data`` intent via the public API endpoint."""

        effective_parameters: dict[str, Any] = copy.deepcopy(parameters or {})
        effective_parameters["transient_csv"] = self._sanitize_transient_csv_payload(
            transient_csv
        )
        if contract_document_id is not None:
            effective_parameters["target_contract_document_id"] = contract_document_id
        if contract_name is not None:
            effective_parameters["target_contract_name"] = contract_name

        payload: dict[str, Any] = {
            "application_id": application_id,
            "prompt": prompt,
            "intent_id": intent_id,
            "parameters": effective_parameters,
            "stream": stream,
        }
        if agent_slug is not None:
            payload["agent_slug"] = agent_slug
        if agent_id is not None:
            payload["agent_id"] = agent_id
        if application_agent_id is not None:
            payload["application_agent_id"] = application_agent_id

        response = self._request(
            "POST",
            self._PUBLIC_REQUESTS_PATH,
            json=payload,
            timeout=timeout,
        )
        data = self._extract_data(response)
        if not isinstance(data, Mapping):
            return DataTransformResponse(response=data)
        return DataTransformResponse.from_public_api_payload(data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sanitize_transient_csv_payload(
        transient_csv: Mapping[str, Any] | TransientCSVUpload,
        *,
        preview_row_limit: int = 20,
    ) -> dict[str, Any]:
        """Strip heavy preview fields to mirror backend sanitization."""

        if isinstance(transient_csv, TransientCSVUpload):
            payload: dict[str, Any] = transient_csv.model_dump(exclude_none=True)
        else:
            payload = dict(transient_csv)

        payload.pop("content_base64", None)
        payload.pop("raw_content", None)
        preview = payload.get("preview")
        if isinstance(preview, Mapping):
            preview_model = TabularPreview.model_validate(preview)
            trimmed_rows = preview_model.rows_sample[: max(preview_row_limit, 1)]
            payload["preview"] = {
                "columns": preview_model.columns,
                "rows_sample": trimmed_rows,
            }
            if preview_model.row_count is not None:
                payload["preview"]["row_count"] = preview_model.row_count
        return payload


__all__ = ["DataImportClient"]
