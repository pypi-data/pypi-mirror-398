"""Integration tests for :class:`FinanFutClient` helpers."""

from __future__ import annotations

from finanfut_sdk.client import FinanFutClient


def test_client_exposes_documents_and_context_sessions() -> None:
    client = FinanFutClient(api_key="k", application_id="app", api_url="https://api")

    documents = client.documents
    sessions = client.context_sessions

    assert documents is client.documents
    assert sessions is client.context_sessions
    assert client.api_key == "k"
    assert client.application_id == "app"
