"""Tests for contexts and context session clients."""

from __future__ import annotations

from unittest.mock import Mock

import requests

from finanfut_sdk.contexts import ContextSessionsClient, ContextsClient
from tests.helpers import DummyResponse


def _headers(_: object | None = None) -> dict[str, str]:
    return {"Authorization": "Bearer test", "Content-Type": "application/json"}


def test_context_creation_normalizes_document_inputs() -> None:
    response_payload = {
        "id": "9c3da51f-d65a-4f0d-bf5c-e61741d61234",
        "application_id": "0fc34ab5-0386-4d40-9866-8ded87826242",
        "name": "Research",
        "status": "active",
        "metadata_": {},
        "document_count": 1,
        "documents": [
            {
                "document_id": "45e889e8-8a02-4fd3-8f85-d76fb84ce185",
                "metadata_": {"tag": "finance"},
                "position": 0,
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(response_payload)

    client = ContextsClient(
        api_url="https://api.example.com",
        session=session,
        header_provider=_headers,
    )

    context = client.create(
        name="Research",
        documents=[
            "45e889e8-8a02-4fd3-8f85-d76fb84ce185",
            {
                "document_id": "7d5bb6d7-4f2b-41fc-99e3-2fc5f3f041f3",
                "metadata": {"tag": "fx"},
            },
        ],
    )

    assert context.name == "Research"
    args, kwargs = session.request.call_args
    assert args[0] == "POST"
    payload = kwargs["json"]
    assert (
        payload["documents"][0]["document_id"]
        == "45e889e8-8a02-4fd3-8f85-d76fb84ce185"
    )
    assert payload["documents"][1]["metadata"]["tag"] == "fx"


def test_context_session_message_append_sends_metadata() -> None:
    message_payload = {
        "id": "b9f13bb0-55c3-4542-88ce-21a8fba6aa12",
        "session_id": "e77fb3ff-39ec-4db5-9fc4-08e848d0fa8b",
        "context_id": "9c3da51f-d65a-4f0d-bf5c-e61741d61234",
        "agent_name": "analyst",
        "intent": "summarize",
        "role": "assistant",
        "tokens_used": 15,
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "metadata_": {"source": "qa"},
        "created_at": "2024-01-01T00:00:00Z",
    }
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(message_payload)

    client = ContextSessionsClient(
        api_url="https://api.example.com",
        session=session,
        header_provider=_headers,
    )

    message = client.add_message(
        "e77fb3ff-39ec-4db5-9fc4-08e848d0fa8b",
        agent_name="analyst",
        intent="summarize",
        query="What changed?",
        answer="Rates moved",
        tokens_used=15,
        prompt_tokens=10,
        completion_tokens=5,
        metadata={"source": "qa"},
    )

    assert message.agent_name == "analyst"
    args, kwargs = session.request.call_args
    assert args[0] == "POST"
    assert kwargs["json"]["metadata"]["source"] == "qa"
