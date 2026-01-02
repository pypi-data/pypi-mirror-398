# MCP Integration Guide

This guide covers Phase 6 functionality: CLI tooling, configuration helpers, and
consent-aware factories that simplify embedding the SDK inside Model Context
Protocol (MCP) servers.

## 1. Load configuration

```python
from codeany_hub.config import load_env

config = load_env()
print(config.base_url)
```

- Use `load_env_file("src/.env")` to preload secrets.
- The generated `ClientConfig` can create sync/async clients without touching
  `os.environ`.

## 2. Ask for user consent (recommended)

```python
from codeany_hub.integrations.mcp import MCPClientBuilder

builder = MCPClientBuilder()

def prompt_user(message: str) -> bool:
    return input(f"{message} [y/N] ").strip().lower() == "y"

with builder.build_sync_client(prompt_user) as client:
    for hub in client.hubs.list_mine():
        print(hub.slug)
```

If the user rejects consent, a `ConsentRejectedError` is raised and the calling
tool should abort gracefully.

## 3. Use the CLI for diagnostics

Install the package (or run it in virtualenv) and execute:

```bash
codeany-hub --env-file src/.env probe
codeany-hub list-hubs --json
```

The CLI reuses the same environment variables (`CODEANY_*`) and surfaces
capabilities or resource lists—ideal for verifying MCP connectivity.

## 4. Contract tests

The test suite now includes CLI and integration fixtures (`tests/test_cli.py`,
`tests/test_mcp.py`). Mirror these patterns when writing additional contract
tests for your MCP server to ensure the builder honors consent prompts and
environment overlays.
