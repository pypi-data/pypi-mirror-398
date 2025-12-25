from unittest.mock import Mock

import requests

from finanfut_sdk.interact import InteractClient
from finanfut_sdk.intents import IntentsClient
from finanfut_sdk.utils.types import build_interaction_response, normalize_intent_payload
from tests.helpers import DummyResponse


def _headers(_: object | None = None) -> dict[str, str]:
    return {"Authorization": "Bearer test", "Content-Type": "application/json"}


def test_intent_roundtrip() -> None:
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(
        {
            "data": [
                {
                    "intent": {
                        "id": "intent-123",
                        "name": "generate",
                        "label": "Generate",
                        "application_agent_intent_id": "link-1",
                    }
                }
            ]
        }
    )

    intents_client = IntentsClient(
        api_url="https://api.example.com", session=session, header_provider=_headers
    )
    intents = intents_client.list(agent_id="agent-1")

    interact_payload = {
        "data": {
            "response": {
                "answer": "ok",
                "intent": {"id": "intent-123", "name": "generate", "label": "Generate"},
                "intent_id": "intent-123",
                "application_agent_intent_id": "link-1",
            },
            "request_id": "req-123",
        }
    }
    session.post.return_value = DummyResponse(interact_payload)

    interact_client = InteractClient(
        api_url="https://api.example.com", session=session, header_provider=_headers
    )
    response = interact_client.query(
        "hello",
        intent_id=intents[0].intent_id,
        application_agent_id="app-agent-1",
        extras={"foo": "bar"},
    )

    sent_payload = session.post.call_args.kwargs["json"]
    assert sent_payload["intent_id"] == "intent-123"
    assert response.intent_id == "intent-123"
    assert response.intent_label == "Generate"
    assert response.application_agent_intent_id == "link-1"


def test_interaction_response_preserves_identifiers() -> None:
    payload = {
        "result": {
            "answer": "hola",
            "intent": {
                "intent": {
                    "id": "intent-999",
                    "name": "generate",
                    "label": "Generator",
                    "application_agent_intent_id": "link-9",
                },
                "intent_id": None,
            },
            "intent_id": None,
            "intent_label": None,
        },
        "request_id": "req-999",
    }

    response = build_interaction_response(payload, {"request_id": "req-999"})

    assert response.intent_id == "intent-999"
    assert response.intent_name == "generate"
    assert response.intent_label == "Generator"
    assert response.application_agent_intent_id == "link-9"


def test_payload_builder_includes_intent_id() -> None:
    client = InteractClient(
        api_url="https://api.example.com", session=Mock(spec=requests.Session), header_provider=_headers
    )

    payload = client._build_payload(
        query="hola",
        application_agent_id="agent-1",
        intent_id="intent-1",
        context_id=None,
        mode=None,
        execution_mode="sync",
        stream=False,
        extras={"metadata": {"x": 1}},
    )

    assert payload["intent_id"] == "intent-1"
    assert payload["application_agent_id"] == "agent-1"
    assert payload["extras"] == {"metadata": {"x": 1}}
    assert payload["execution_mode"] == "sync"


def test_normalize_intent_payload_merges_nested_correctly() -> None:
    normalized = normalize_intent_payload(
        {
            "intent_id": None,
            "name": None,
            "label": None,
            "application_agent_intent_id": None,
            "intent": {
                "id": "backend-id",
                "name": "generate",
                "label": "Backend Label",
                "application_agent_intent_id": "link-123",
                "application_agent_id": "agent-5",
            },
            "description": "from-wrapper",
        }
    )

    assert normalized is not None
    assert normalized["intent_id"] == "backend-id"
    assert normalized["id"] == "backend-id"
    assert normalized["application_agent_intent_id"] == "link-123"
    assert normalized["application_agent_id"] == "agent-5"
    assert normalized["name"] == "generate"
    assert normalized["label"] == "Backend Label"
    assert normalized["description"] == "from-wrapper"


def test_available_intents_extracted_correctly() -> None:
    payload = {
        "response": {
            "answer": "ok",
            "available_intents": [
                {
                    "intent": {
                        "id": "intent-a",
                        "name": "generate",
                        "label": "Generate",
                        "application_agent_intent_id": "link-a",
                    }
                },
                {"id": "intent-b", "name": "classify", "label": "Classify"},
            ],
            "available_intent_names": [],
        },
        "request_id": "req-available",
    }
    meta = {"token_usage": {"total_tokens": 4}}

    response = build_interaction_response(payload, meta)

    assert [intent.intent_id for intent in response.available_intents] == ["intent-a", "intent-b"]
    assert response.available_intent_names == ["generate", "classify"]
    assert response.meta["token_usage"] == {"total_tokens": 4}
