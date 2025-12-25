"""Configuration helpers for the FinanFut SDK."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_API_URL = "https://finanfut-intelligence.onrender.com"
DEFAULT_CONFIG_PATH = Path.home() / ".finanfut" / "config.json"


def normalize_api_url(api_url: str) -> str:
    """Return a base API URL without duplicated path segments.

    Users sometimes set ``FINANFUT_API_URL`` to an already-versioned endpoint
    such as ``https://host/api/v1``. The SDK appends its own ``/api/v1``
    prefix when building requests, so we strip known suffixes to avoid calling
    paths like ``/api/v1/api/v1/interact``.
    """

    cleaned = api_url.rstrip("/")
    for suffix in ("/api/v1", "/api"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return cleaned.rstrip("/") or cleaned


def load_from_env(prefix: str = "FINANFUT_") -> dict[str, Any]:
    """Load SDK configuration from environment variables."""

    mapping = {
        "api_key": os.getenv(f"{prefix}API_KEY"),
        "application_id": os.getenv(f"{prefix}APPLICATION_ID"),
        "api_url": os.getenv(f"{prefix}API_URL"),
    }
    return {key: value for key, value in mapping.items() if value}


def load_from_file(path: Path | None = None) -> dict[str, Any]:
    """Load SDK configuration from the optional JSON file."""

    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return {}

    try:
        raw = config_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid FinanFut config file at {config_path}") from exc

    if not isinstance(data, dict):
        raise ValueError("FinanFut config file must contain a JSON object")

    allowed_keys = {"api_key", "application_id", "api_url"}
    return {key: value for key, value in data.items() if key in allowed_keys and value}


def merge_config(base: dict[str, Any | None] = None, override: dict[str, Any | None] = None) -> dict[str, Any]:
    """Merge configuration dictionaries into a final payload."""

    merged: dict[str, Any] = {}
    if base:
        merged.update({k: v for k, v in base.items() if v is not None})
    if override:
        merged.update({k: v for k, v in override.items() if v is not None})
    return merged


def load_config(
    *,
    api_key: str | None = None,
    application_id: str | None = None,
    api_url: str | None = None,
    config_path: Path | str | None = None,
) -> dict[str, str]:
    """Resolve the client configuration using the documented priority order."""

    file_config = load_from_file(Path(config_path) if config_path else None)
    env_config = load_from_env()

    merged = merge_config(file_config, env_config)
    merged = merge_config(
        merged,
        {"api_key": api_key, "application_id": application_id, "api_url": api_url},
    )

    if not merged.get("api_url"):
        merged["api_url"] = DEFAULT_API_URL

    merged["api_url"] = normalize_api_url(str(merged["api_url"]))

    if not merged.get("api_key") or not merged.get("application_id"):
        raise ValueError(
            "FinanFut API key and application_id are required. Provide them via the "
            "constructor, environment variables, or the ~/.finanfut/config.json file."
        )

    return merged  # type: ignore[return-value]
