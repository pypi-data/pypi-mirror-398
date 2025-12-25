from __future__ import annotations

from unittest.mock import Mock

import requests

from finanfut_sdk.requests import RequestsClient
from tests.helpers import DummyResponse


def _headers(_: object | None = None) -> dict[str, str]:
    return {"Authorization": "Bearer test", "Content-Type": "application/json"}


def test_requests_client_accepts_success_status_flag() -> None:
    payload = {"status": "success", "data": {"response": {"answer": "ok"}}}
    session = Mock(spec=requests.Session)
    session.get.return_value = DummyResponse(payload)

    client = RequestsClient(api_url="https://api.example.com", session=session, header_provider=_headers)

    result = client.get("req-1")

    assert result["status"] == "success"
    assert result["data"]["response"]["answer"] == "ok"
