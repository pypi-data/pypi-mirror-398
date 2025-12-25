from __future__ import annotations

from unittest.mock import Mock

import requests

from finanfut_sdk.access_tokens import AccessTokensClient
from finanfut_sdk.analytics import AnalyticsClient
from finanfut_sdk.applications import ApplicationAgentsClient
from finanfut_sdk.billing import BillingClient
from finanfut_sdk.intents import IntentsClient
from finanfut_sdk.memory import MemoryRecordsClient
from finanfut_sdk.utils.types import AccessTokenCreateRequest
from tests.helpers import DummyResponse


def _headers(_: object | None = None) -> dict[str, str]:
    return {"Authorization": "Bearer test", "Content-Type": "application/json"}


def test_application_agents_list_uses_application_scope() -> None:
    payload = {"items": [], "total": 0, "limit": 50, "offset": 0}
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)

    client = ApplicationAgentsClient(
        api_url="https://api.example.com", session=session, header_provider=_headers
    )

    client.list("app-123")

    args, kwargs = session.request.call_args
    assert args[1].endswith("/api/v1/applications/app-123/agents")
    assert kwargs["params"]["limit"] == 50


def test_intents_list_with_application_agent_uses_nested_route() -> None:
    payload = {"items": []}
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)
    client = IntentsClient(api_url="https://api.example.com", session=session, header_provider=_headers)

    client.list("agent-1", application_id="app-1")

    path = session.request.call_args[0][1]
    assert "/api/v1/applications/app-1/agents/agent-1/intents" in path


def test_memory_query_targets_central_endpoint() -> None:
    payload = {"records": [], "total": 0}
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)
    client = MemoryRecordsClient(api_url="https://api.example.com", session=session, header_provider=_headers)

    client.query("app-1", "agent-2", query="search term")

    args, kwargs = session.request.call_args
    assert args[1].endswith("/api/v1/memory/records/query")
    assert kwargs["json"]["application_agent_id"] == "agent-2"


def test_billing_exposes_plans_listing() -> None:
    payload = {"items": [{"plan_id": "basic"}]}
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)
    client = BillingClient(api_url="https://api.example.com", session=session, header_provider=_headers)

    plans = client.get_plans()

    assert plans[0].plan_id == "basic"
    assert session.request.call_args[0][1].endswith("/api/v1/billing/plans")


def test_analytics_routes_use_new_prefix() -> None:
    payload = {"data": []}
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)
    client = AnalyticsClient(api_url="https://api.example.com", session=session, header_provider=_headers)

    client.logs()
    assert "/api/v1/analytics/logs" in session.request.call_args[0][1]


def test_access_token_creation_accepts_scopes() -> None:
    payload = {"token_id": "123", "description": "ci", "created_at": "now"}
    session = Mock(spec=requests.Session)
    session.request.return_value = DummyResponse(payload)
    client = AccessTokensClient(api_url="https://api.example.com", session=session, header_provider=_headers)

    request_payload = AccessTokenCreateRequest(description="ci", scopes=["read"])
    token = client.create(payload=request_payload)

    assert token.token_id == "123"
    assert session.request.call_args[1]["json"]["scopes"] == ["read"]
