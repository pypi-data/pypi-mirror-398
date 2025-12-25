from __future__ import annotations

from unittest.mock import Mock

import requests

from finanfut_sdk.interact import InteractClient
from tests.helpers import DummyResponse


def _headers(_: object | None = None) -> dict[str, str]:
    return {"Authorization": "Bearer test", "Content-Type": "application/json"}


def test_interact_query_preserves_extras_envelope() -> None:
    payload = {"data": {"answer": "ok"}}
    session = Mock(spec=requests.Session)
    session.post.return_value = DummyResponse(payload)

    client = InteractClient(
        api_url="https://api.example.com", session=session, header_provider=_headers
    )

    client.query("hello", extras={"metadata": {"agent_key": "post_generator"}})

    sent_payload = session.post.call_args.kwargs["json"]
    assert sent_payload["extras"] == {"metadata": {"agent_key": "post_generator"}}
    assert "metadata" not in sent_payload


def test_interact_query_keeps_execution_mode_when_modality_set() -> None:
    payload = {"data": {"answer": "ok"}}
    session = Mock(spec=requests.Session)
    session.post.return_value = DummyResponse(payload)

    client = InteractClient(
        api_url="https://api.example.com", session=session, header_provider=_headers
    )

    client.query("hola", mode="text")

    sent_payload = session.post.call_args.kwargs["json"]
    assert sent_payload["execution_mode"] == "sync"
    assert sent_payload["mode"] == "text"


def test_interact_query_parses_complex_response_payload() -> None:
    payload = {
        "request_id": "req-123",
        "result": {
            "answer": {"content": "Hola"},
            "metadata": {
                "agent_key": "post_generator",
                "requested_intent": "generate",
                "intent_responses": [
                    {
                        "intent": "generate_post",
                        "parameters": {"tone": "friendly"},
                        "result": {"content": "Hola"},
                        "raw_model_output": {"logprobs": []},
                    }
                ],
            },
            "tokens_used": 381,
            "actions": [
                {"name": "publish", "payload": {"channel": "social", "status": "queued"}}
            ],
            "context_used": [{"source": "memory"}],
            "application_agent_id": "fa52d162-01fc-499a-8fa3-9c370a0fca7a",
            "agent_id": "agent-1",
            "intent_id": "aafc2bfb-902b-492d-909d-77ca318286d5",
        },
        "meta": {"token_usage": {"total_tokens": 20}},
    }

    session = Mock(spec=requests.Session)
    session.post.return_value = DummyResponse(payload)
    client = InteractClient(
        api_url="https://api.example.com", session=session, header_provider=_headers
    )

    response = client.query("hola")

    assert response.answer and response.answer.content == "Hola"
    assert response.metadata["agent_key"] == "post_generator"
    assert response.tokens and response.tokens.total_tokens == 381
    assert response.tokens_used == 381
    assert response.context_used == [{"source": "memory"}]
    assert response.application_agent_id == "fa52d162-01fc-499a-8fa3-9c370a0fca7a"
    assert response.agent_id == "agent-1"
    assert response.intent_id == "aafc2bfb-902b-492d-909d-77ca318286d5"
    assert response.available_intent_names == ["generate_post"]
    assert response.intent_responses[0].raw_model_output == {"logprobs": []}
    assert response.request_id == "req-123"
    assert response.meta == {"token_usage": {"total_tokens": 20}}
    assert response.raw["answer"]["content"] == "Hola"


def test_interact_async_query_sets_execution_mode() -> None:
    payload = {"data": {"request_id": "req-async"}}
    session = Mock(spec=requests.Session)
    session.post.return_value = DummyResponse(payload)

    client = InteractClient(
        api_url="https://api.example.com", session=session, header_provider=_headers
    )

    request_id = client.async_query("hola", extras={"mode": "text"})

    sent_payload = session.post.call_args.kwargs["json"]
    assert sent_payload["execution_mode"] == "async"
    assert sent_payload["extras"] == {"mode": "text"}
    assert request_id == "req-async"
