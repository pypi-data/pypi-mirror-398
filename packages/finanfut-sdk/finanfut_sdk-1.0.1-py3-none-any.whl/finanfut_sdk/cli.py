"""Command-line interface for the FinanFut SDK."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .client import FinanFutClient
from .config import DEFAULT_API_URL, DEFAULT_CONFIG_PATH
from .utils.errors import FinanFutApiError


def main(argv: list[str | None] = None) -> int:
    """Entry point for the ``finanfut`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        _handle_init(Path(args.path) if args.path else DEFAULT_CONFIG_PATH)
        return 0

    if not args.command:
        parser.print_help()
        return 0

    try:
        client = FinanFutClient(
            api_key=args.api_key,
            application_id=args.application_id,
            api_url=args.api_url,
            dry_run=args.dry_run,
            config_path=args.config,
        )
    except Exception as exc:  # pragma: no cover - CLI helper
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.command == "interact":
            _handle_interact(client, args)
        elif args.command == "usage":
            _handle_usage(client, args)
        elif args.command == "agents" and getattr(args, "agents_command", None) == "list":
            _handle_agents_list(client, args)
        else:
            parser.print_help()
            return 1
    except FinanFutApiError as exc:
        print(f"API error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - runtime guard
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finanfut",
        description="FinanFut Intelligence command-line interface",
    )
    parser.add_argument("--api-key", dest="api_key", help="Override the API key used for this command.")
    parser.add_argument(
        "--application-id",
        dest="application_id",
        help="Override the application_id used for this command.",
    )
    parser.add_argument("--api-url", dest="api_url", help="Override the API base URL.")
    parser.add_argument(
        "--config",
        dest="config",
        help="Custom path to the FinanFut config file (defaults to ~/.finanfut/config.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Enable dry-run mode for the issued command.",
    )

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialise the FinanFut SDK configuration file.")
    init_parser.add_argument(
        "--path",
        help="Destination path for the generated config file (defaults to ~/.finanfut/config.json).",
    )

    interact_parser = subparsers.add_parser(
        "interact", help="Send a prompt to the FinanFut orchestrator."
    )
    interact_parser.add_argument("message", help="Prompt or query to send to FinanFut Intelligence.")
    interact_parser.add_argument("--agent-id", dest="agent_id", help="Application agent identifier.")
    interact_parser.add_argument("--intent-id", dest="intent_id", help="Intent identifier to target.")
    interact_parser.add_argument("--context-id", dest="context_id", help="Context document/session identifier.")

    usage_parser = subparsers.add_parser("usage", help="Display current billing usage.")
    usage_parser.add_argument(
        "--period",
        default="month",
        help="Usage period (e.g. day, week, month).",
    )

    agents_parser = subparsers.add_parser("agents", help="Inspect available agents.")
    agents_sub = agents_parser.add_subparsers(dest="agents_command")
    agents_list = agents_sub.add_parser("list", help="List agents accessible to the current application.")
    agents_list.add_argument(
        "--app-id",
        dest="agents_application_id",
        default=None,
        help="Optionally list agents for a specific application.",
    )

    return parser


def _handle_init(target_path: Path) -> None:
    print("FinanFut SDK configuration setup\n")
    api_key = input("API key: ").strip()
    application_id = input("Application ID: ").strip()
    api_url = input(f"API URL [{DEFAULT_API_URL}]: ").strip() or DEFAULT_API_URL

    payload: dict[str, Any] = {
        "api_key": api_key,
        "application_id": application_id,
        "api_url": api_url,
    }

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Configuration saved to {target_path}")


def _handle_interact(client: FinanFutClient, args: argparse.Namespace) -> None:
    response = client.interact.query(
        args.message,
        application_agent_id=args.agent_id,
        intent_id=args.intent_id,
        context_id=args.context_id,
    )

    print("Answer:\n" + str(response.answer))
    if response.tokens:
        tokens = response.tokens.model_dump(exclude_none=True)
        if tokens:
            print("\nToken usage:")
            for key, value in tokens.items():
                print(f"  {key}: {value}")
    if response.sandbox:
        print("\nSandbox mode: enabled")
    if response.actions:
        print("\nActions:")
        for action in response.actions:
            print(f"- {action.name}: {json.dumps(action.payload, indent=2)}")
    if response.meta:
        print("\nMeta:")
        print(json.dumps(response.meta, indent=2))


def _handle_usage(client: FinanFutClient, args: argparse.Namespace) -> None:
    usage = client.billing.get_usage(period=args.period)
    print(f"Period: {usage.period}")
    print(f"Tokens used: {usage.tokens_used}")
    print(f"Cost: {usage.cost}")


def _handle_agents_list(client: FinanFutClient, args: argparse.Namespace) -> None:
    agents = client.agents.list(application_id=args.agents_application_id)
    if not agents:
        print("No agents found.")
        return
    for agent in agents:
        line = f"{agent.agent_id} — {agent.name}"
        if agent.description:
            line += f" ({agent.description})"
        print(line)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
