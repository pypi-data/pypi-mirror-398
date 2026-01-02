"""Command line interface for the Codeany Hub SDK."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .config import load_env, load_env_file
from .client import CodeanyClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codeany Hub SDK CLI")
    parser.add_argument("--env-file", help="Path to .env file to load before running commands.")
    parser.add_argument("--env-prefix", default="CODEANY_", help="Environment variable prefix (default: CODEANY_).")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("probe", help="Fetch capability information via /api/docs.json.")

    list_hubs = subparsers.add_parser("list-hubs", help="List hubs accessible to the authenticated user.")
    list_hubs.add_argument("--json", action="store_true", help="Output as JSON instead of plain text.")

    subparsers.add_parser("show-config", help="Print the resolved client configuration.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.env_file:
        load_env_file(args.env_file)

    try:
        config = load_env(prefix=args.env_prefix)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if args.command == "show-config":
        print(json.dumps(config.to_env(args.env_prefix), indent=2))
        return 0

    with CodeanyClient.from_env(prefix=args.env_prefix) as client:
        if args.command == "probe":
            capabilities = client.refresh_capabilities()
            print(json.dumps(capabilities, indent=2))
            return 0

        if args.command == "list-hubs":
            hubs = client.hubs.list_mine()
            if args.json:
                payload: list[dict[str, Any]] = [
                    {"slug": hub.slug, "display_name": hub.display_name} for hub in hubs
                ]
                print(json.dumps(payload, indent=2))
            else:
                for hub in hubs:
                    print(f"{hub.slug}\t{hub.display_name or ''}")
            return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
