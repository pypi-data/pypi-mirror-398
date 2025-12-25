"""Primary client for the FinanFut Intelligence SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

from .auth import build_request_headers
from .config import load_config, normalize_api_url

if TYPE_CHECKING:  # pragma: no cover
    from .interact import InteractClient
    from .agents import AgentsClient
    from .intents import IntentsClient
    from .applications import ApplicationsClient
    from .memory import MemoryClient
    from .contexts import ContextsClient
    from .contexts import ContextSessionsClient
    from .documents import DocumentsClient
    from .billing import BillingClient
    from .requests import RequestsClient
    from .analytics import AnalyticsClient
    from .access_tokens import AccessTokensClient
    from .data_import import DataImportClient


class FinanFutClient:
    """High-level client entrypoint for FinanFut Intelligence."""

    def __init__(
        self,
        api_key: str | None = None,
        application_id: str | None = None,
        api_url: str | None = None,
        *,
        dry_run: bool = False,
        config_path: str | None = None,
    ) -> None:
        resolved = load_config(
            api_key=api_key,
            application_id=application_id,
            api_url=api_url,
            config_path=config_path,
        )

        self._api_key = resolved["api_key"]
        self._application_id = resolved["application_id"]
        self._api_url = normalize_api_url(resolved["api_url"])
        self._dry_run = dry_run

        self._session = requests.Session()
        self._interact_client: "InteractClient" | None = None
        self._requests_client: "RequestsClient" | None = None
        self._applications_client: "ApplicationsClient" | None = None
        self._agents_client: "AgentsClient" | None = None
        self._intents_client: "IntentsClient" | None = None
        self._memory_client: "MemoryClient" | None = None
        self._contexts_client: "ContextsClient" | None = None
        self._context_sessions_client: "ContextSessionsClient" | None = None
        self._billing_client: "BillingClient" | None = None
        self._analytics_client: "AnalyticsClient" | None = None
        self._access_tokens_client: "AccessTokensClient" | None = None
        self._documents_client: "DocumentsClient" | None = None
        self._data_import_client: "DataImportClient" | None = None

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def application_id(self) -> str:
        return self._application_id

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    def _build_headers(self, extra: dict[str, str | None] = None) -> dict[str, str]:
        """Return the merged headers for an API request."""

        merged: dict[str, str] = {}
        if self._dry_run:
            merged["X-Dry-Run"] = "true"
        if extra:
            merged.update(extra)
        return build_request_headers(self._api_key, self._application_id, merged or None)

    @classmethod
    def for_sandbox(cls, **kwargs: Any) -> "FinanFutClient":
        """Instantiate a sandbox client with ``dry_run`` enabled."""

        payload = dict(kwargs)
        payload["dry_run"] = True
        return cls(**payload)  # type: ignore[arg-type]

    @property
    def interact(self) -> "InteractClient":
        if self._interact_client is None:
            from .interact import InteractClient

            self._interact_client = InteractClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
                dry_run=self._dry_run,
            )
        return self._interact_client

    @property
    def agents(self) -> "AgentsClient":
        if self._agents_client is None:
            from .agents import AgentsClient

            self._agents_client = AgentsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._agents_client

    @property
    def intents(self) -> "IntentsClient":
        if self._intents_client is None:
            from .intents import IntentsClient

            self._intents_client = IntentsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._intents_client

    @property
    def applications(self) -> "ApplicationsClient":
        if self._applications_client is None:
            from .applications import ApplicationsClient

            self._applications_client = ApplicationsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._applications_client

    @property
    def memory(self) -> "MemoryClient":
        if self._memory_client is None:
            from .memory import MemoryClient

            self._memory_client = MemoryClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._memory_client

    @property
    def contexts(self) -> "ContextsClient":
        if self._contexts_client is None:
            from .contexts import ContextsClient

            self._contexts_client = ContextsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._contexts_client

    @property
    def context_sessions(self) -> "ContextSessionsClient":
        if self._context_sessions_client is None:
            from .contexts import ContextSessionsClient

            self._context_sessions_client = ContextSessionsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._context_sessions_client

    @property
    def billing(self) -> "BillingClient":
        if self._billing_client is None:
            from .billing import BillingClient

            self._billing_client = BillingClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._billing_client

    @property
    def requests(self) -> "RequestsClient":
        if self._requests_client is None:
            from .requests import RequestsClient

            self._requests_client = RequestsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._requests_client

    @property
    def analytics(self) -> "AnalyticsClient":
        if self._analytics_client is None:
            from .analytics import AnalyticsClient

            self._analytics_client = AnalyticsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._analytics_client

    @property
    def access_tokens(self) -> "AccessTokensClient":
        if self._access_tokens_client is None:
            from .access_tokens import AccessTokensClient

            self._access_tokens_client = AccessTokensClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._access_tokens_client

    @property
    def documents(self) -> "DocumentsClient":
        if self._documents_client is None:
            from .documents import DocumentsClient

            self._documents_client = DocumentsClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._documents_client

    @property
    def data_import(self) -> "DataImportClient":
        if self._data_import_client is None:
            from .data_import import DataImportClient

            self._data_import_client = DataImportClient(
                api_url=self._api_url,
                session=self._session,
                header_provider=self._build_headers,
            )
        return self._data_import_client
