"""Billing module implementation."""

from __future__ import annotations

from typing import Any, Mapping

import requests

from ._base import BaseApiClient, HeaderProvider
from .utils.types import BillingPlan, BillingUsage, TransactionRecord
JsonDict = dict[str, Any]


class BillingClient(BaseApiClient):
    """Inspect plans, usage metrics, and billing transactions."""

    def __init__(
        self,
        *,
        api_url: str,
        session: requests.Session | None = None,
        header_provider: HeaderProvider,
    ) -> None:
        super().__init__(api_url=api_url, session=session, header_provider=header_provider)

    def get_plan(self, *, timeout: float | None = None) -> BillingPlan:
        """Return the current billing plan descriptor."""

        payload = self._request("GET", "/api/v1/billing/plan", timeout=timeout)
        data: JsonDict = self._extract_data(payload)
        return BillingPlan.model_validate(data)

    def get_plans(self, *, timeout: float | None = None) -> list[BillingPlan]:
        """List available billing plans."""

        payload = self._request("GET", "/api/v1/billing/plans", timeout=timeout)
        data = self._extract_data(payload)
        plans = data.get("items") if isinstance(data, dict) else data
        if isinstance(plans, list):
            return [BillingPlan.model_validate(item) for item in plans]
        if isinstance(plans, dict):
            return [BillingPlan.model_validate(plans)]
        return []

    def get_usage(
        self,
        *,
        period: str | None = None,
        timeout: float | None = None,
    ) -> BillingUsage:
        """Return the billing usage for the requested period."""

        params: dict[str, Any] = {}
        if period:
            params["period"] = period
        payload = self._request(
            "GET", "/api/v1/billing/usage", params=params, timeout=timeout
        )
        data: JsonDict = self._extract_data(payload)
        return BillingUsage.model_validate(data)

    def list_transactions(
        self,
        *,
        filters: Mapping[str, Any | None] | None = None,
        timeout: float | None = None,
    ) -> list[TransactionRecord]:
        """Return historical transaction records."""

        payload = self._request(
            "GET",
            "/api/v1/billing/transactions",
            params=dict(filters or {}),
            timeout=timeout,
        )
        data = self._extract_data(payload)
        if isinstance(data, list):
            return [TransactionRecord.model_validate(item) for item in data]
        if isinstance(data, dict):
            return [TransactionRecord.model_validate(data)]
        return []
