"""Unit tests validating the documents client."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import requests

from finanfut_sdk.documents import DocumentsClient
from tests.helpers import DummyResponse


def _headers(_: object | None = None) -> dict[str, str]:
    return {"Authorization": "Bearer test", "Content-Type": "application/json"}


def test_upload_reads_file_and_encodes_payload(tmp_path: Path) -> None:
    sample = tmp_path / "report.txt"
    sample.write_text("hello world", encoding="utf-8")
    payload = {
        "id": "6ba7b814-9dad-4f3c-91b5-426614174000",
        "file_name": "report.txt",
        "mime_type": "text/plain",
        "status": "processed",
        "chunk_count": 1,
    }
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)

    client = DocumentsClient(
        api_url="https://api.example.com",
        session=session,
        header_provider=_headers,
    )

    document = client.upload(file_path=sample)

    assert document.file_name == "report.txt"
    assert document.status == "processed"

    args, kwargs = session.request.call_args
    assert args[0] == "POST"
    assert args[1].endswith("/api/v1/documents/upload")
    file_tuple = kwargs["files"]["file"]
    assert file_tuple[0] == "report.txt"
    assert file_tuple[1].decode("utf-8") == "hello world"


def test_list_documents_handles_plain_list_response() -> None:
    payload = [
        {
            "id": "7dc95b24-3f60-4ad2-bf6f-255b6e60f8b7",
            "file_name": "report.txt",
            "mime_type": "text/plain",
            "status": "processed",
            "chunk_count": 4,
        }
    ]
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)

    client = DocumentsClient(
        api_url="https://api.example.com",
        session=session,
        header_provider=_headers,
    )

    documents = client.list()

    assert len(documents) == 1
    assert documents[0].file_name == "report.txt"
    session.request.assert_called_once()
