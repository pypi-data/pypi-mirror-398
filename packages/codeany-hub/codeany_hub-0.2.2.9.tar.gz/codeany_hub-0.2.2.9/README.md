# Codeany Hub Python SDK

Modern, typed, and resilient Python SDK for the Codeany Hub APIs. This package wraps the REST endpoints under `/api/hubs/` (and related `/api/users/` authentication routes) and exposes a clean, Pythonic surface for managing hubs, members, tasks, competitions, submissions, ratings, judges, and imports.

> **Status:** Phase 6 of the public roadmap — ships CLI tooling, MCP builders, deep integration guides, and contract tests.

## Why this SDK

- **Pythonic façade:** Thin, well-typed clients that mirror the backend structure.
- **Authentication done right:** Composable strategies for SimpleJWT, hub login, and OAuth verification, with swapable token stores.
- **Typed but tolerant models:** Built on Pydantic v2 with `extra='allow'` to stay forward compatible with backend changes.
- **Productivity helpers:** Filter builders, pagination iterators, and pollers for long-running operations.
- **Escape hatches everywhere:** Raw param passthrough and access to raw responses for complex or experimental features.

## Installation

```bash
pip install codeany-hub
```

> Requires Python 3.9 or newer.

For a development setup (including linting and test tooling), install the bundled requirements:

```bash
pip install -r requirements.txt
```

## Quick start

```python
import os

from codeany_hub import CodeanyClient
from codeany_hub.filters import SubmissionsFilter
from codeany_hub.models import SubmissionOrdering, SubmissionVerdict

BASE_URL = os.getenv("CODEANY_BASE_URL", "https://codeany.org")
USERNAME = os.getenv("CODEANY_USERNAME", "alice")
PASSWORD = os.getenv("CODEANY_PASSWORD", "s3cret")
DEFAULT_HUB = os.getenv("CODEANY_HUB")

with CodeanyClient.with_simple_jwt(
    base_url=BASE_URL,
    username=USERNAME,
    password=PASSWORD,
) as client:
    hubs = client.hubs.list_mine()
    for hub in hubs:
        print(hub.slug, hub.display_name)

    target_hub = DEFAULT_HUB or (client.default_hub or (hubs[0].slug if hubs else None))
    if target_hub:
        flt = (
            SubmissionsFilter()
            .verdict(SubmissionVerdict.ACCEPTED)
            .ordering(SubmissionOrdering.CREATED_DESC)
            .per_page(50)
        )
        page = client.submissions.list(target_hub, filter=flt)
        for submission in page.results:
            print(submission.id, submission.verdict_enum)
```

See `examples/quickstart.py` for runnable snippets covering authentication, pagination, submissions filtering, polling, and the async client.

### Async quick start

```python
import asyncio

from codeany_hub import AsyncCodeanyClient


async def main() -> None:
    client = await AsyncCodeanyClient.from_env()
    try:
        hubs = await client.hubs.list_mine()
        for hub in hubs:
            print(hub.slug, hub.display_name)
    finally:
        await client.aclose()


asyncio.run(main())
```

## Authentication strategies

The SDK ships with pluggable strategies defined in `codeany_hub.core.auth`.

| Strategy | When to use | Token lifecycle |
| --- | --- | --- |
| `SimpleJwtAuth` | Global user login via `/api/users/` | Refreshes automatically using `/api/users/refresh` |
| `HubLoginAuth` | Project-scoped login via `/api/hubs/{hub}/login` | Refresh support if backend returns a refresh token |
| `OAuthBridge` | OAuth handoff for hubs | Completes `/verify-oauth-token` flow |

Choose a strategy via factory constructors:

```python
client = CodeanyClient.with_hub_login(
    base_url="https://codeany.org",
    hub="awesome-hub",
    username="janedoe",
    password="•••••••",
)
```

All strategies rely on a `TokenStore` implementation (`InMemoryTokenStore` by default). Bring your own storage by implementing the simple `TokenStore` interface.

> **Note:** `HubLoginAuth` tolerates backend responses that return the JWT under either an `access` or `token` key. Whichever field is present gets persisted to the configured `TokenStore`, so you can interoperate with older hubs without extra glue code.

## Transport customization

The shared `Transport` powers every client request. You can enable retries, structured logging, and request/response hooks without leaving application code:

```python
from codeany_hub.core import TransportHooks

events: list[str] = []

hooks = TransportHooks(
    on_request=[lambda ctx: events.append(f"{ctx.method} {ctx.path} #{ctx.attempt}")],
    on_response=[lambda ctx: events.append(f"→ {ctx.response.status_code} in {ctx.duration:.3f}s")],
)

client = CodeanyClient(
    "https://codeany.org",
    auth=...,  # any AuthStrategy
    retries=2,
    retry_backoff=0.5,
    hooks=hooks,
    log_requests=True,
)
```

For long-running uploads (e.g. testset archives) the transport exposes `transport.stream(...)`, returning an iterator of decoded text chunks while maintaining the same retry and auth semantics. The async transport mirrors this capability with `await transport.stream(...)`, yielding an async iterator.

Async clients accept the same knobs plus `async_hooks` for `async def` handlers.

## Documentation

Extended guides live under [`docs/`](docs/index.md):

- [Getting Started](docs/quickstart.md) – environment bootstrapping and first calls.
- [Retry Policies & Hooks](docs/retry-policies.md) – plug in custom resilience strategies.
- [Scenario Playbooks](docs/scenarios.md) – multi-step workflows ready to adapt to your hubs.
- [MCP Integration Guide](docs/mcp.md) – consent-aware builders, CLI usage, and contract testing tips.

## Command-line interface

Install the package (or the development requirements) and run:

```bash
codeany-hub --env-file src/.env probe
codeany-hub list-hubs --json
```

By default the CLI reads `CODEANY_*` variables; `--env-file` loads an `.env`
file before instantiating clients. The `probe` command prints capability data,
while `list-hubs` enumerates accessible hubs (plain text or JSON).

## Using the SDK from MCP tools

Many Model Context Protocol (MCP) tools embed Python clients to orchestrate remote services. To integrate `codeany-hub` safely:

1. **Install the SDK inside your MCP runtime.** Either vendor the package (`pip install codeany-hub`) or point the tool’s virtual environment at `requirements.txt` so lint/test helpers remain available.
2. **Provide credentials via environment variables.**
   - Required: `CODEANY_BASE_URL`, `CODEANY_USERNAME`, `CODEANY_PASSWORD`
   - Optional: `CODEANY_HUB`, `CODEANY_TOKEN_STORE_PATH`, `CODEANY_RETRIES`, `CODEANY_LOG_REQUESTS`, etc.
   - When an MCP session is user-facing, ask the operator to confirm use of stored secrets (display a yes/no prompt) before the tool consumes them. Abort on rejection.
3. **Instantiate the client inside your tool handler.**
   ```python
   from codeany_hub import CodeanyClient

   def list_hubs_tool() -> list[str]:
       client = CodeanyClient.from_env()
       try:
           return [hub.slug for hub in client.hubs.list_mine()]
       finally:
           client.close()
   ```
   For async handlers, use `AsyncCodeanyClient.from_env()` within an async context.
4. **Respect token storage and consent flows.** If you persist refresh tokens (e.g., by setting `CODEANY_TOKEN_STORE_PATH`), ensure the MCP application lets end users approve or revoke storage. Provide a clear “Disconnect” option that deletes the token file.
5. **Log responsibly.** Avoid printing access tokens or request payloads that might contain PII. Use transport hooks to emit high-level telemetry only after the user consents.
6. **Keep the tool updated.** Re-run `pip install -r requirements.txt` (or your lock-step manager) when the SDK is bumped, and execute `scripts/run_tests.sh` inside your MCP development environment before redeploying.

> **Sensitive operations:** Always surface a prompt when a tool intends to mutate hubs (create tasks, delete submissions, trigger ratings). Give users the option to accept or reject the action, and only proceed on explicit approval.

## Running tests locally

Install the dev requirements (see above), then execute:

```bash
scripts/run_tests.sh
```

The script runs `ruff` followed by `pytest`. Pass additional pytest arguments after the script name, e.g. `scripts/run_tests.sh tests/test_scenarios.py`.

## Clients overview

Each resource area is implemented as a dedicated client under `codeany_hub.clients`. The top-level `CodeanyClient` wires them together (and `AsyncCodeanyClient` mirrors the same attributes with awaitable methods):

- `client.users`: authentication helpers (obtain/refresh tokens, hub login/register, OAuth verification).
- `client.hubs`: CRUD for hubs, membership management, profile updates, permission changes.
- `client.tasks`: Task lifecycle, settings, limits, multilingual statements, testsets, visibility toggles.
- `client.mcq`: Multiple-choice configuration for tasks.
- `client.competitions`: Listing, creation, update, languages, leaderboard.
- `client.submissions`: Hub and competition submission listings with builder-based filters.
- `client.ratings`: Trigger ratings, track statuses, configure options, poll progress.
- `client.imports`: Start and monitor CSES imports.
- `client.judge`: Submission rejudge operations.

All clients share the same `Transport`, gaining authenticated requests, automatic refresh on 401, standard error handling, and consistent timeout behavior.

> **Hub slugs only:** Every hub-scoped endpoint expects the hub slug (`hub_name` in the Django routes). The `Hub` model automatically normalises `slug`, `hub_name`, or legacy `name` fields, so you can always pass `hub.slug` straight into `client.tasks.*` without juggling IDs or titles. Task payloads that embed a bare slug under `hub` are also coerced into lightweight `Hub` objects, so `task.hub.slug` is always safe to read.

## Task management quick tour

The task client centralises everything required to curate competitive programming tasks:

```python
# Discover tasks before drilling into statements/testsets
page = client.tasks.list("awesome-hub", page=1, page_size=20, filters={"search": "sum"})
for task in page.results:
    print(task.id, task.slug, task.visibility_enum)

limits = client.tasks.get_limits("awesome-hub", task_id=42)
client.tasks.update_limits("awesome-hub", 42, time_limit=2000, memory_limit=256)

# Upsert multilingual statements and upload inline assets
client.tasks.upsert_statement_lang(
    "awesome-hub",
    42,
    lang="en",
    payload={
        "title": "Two Sum",
        "statements": "Find the indices...",
        "statements_type": "markdown",
    },
)
image_url = client.tasks.upload_statement_image(
    "awesome-hub",
    42,
    file="docs/images/two-sum.png",
)
# Legacy `client.tasks.update_statement(...)` now proxies the same endpoint; include `lang` in the payload or pass `lang=\"en\"` explicitly because numeric statement IDs are ignored by the backend.

# Manage judge data
page = client.tasks.list_testsets("awesome-hub", 42, page=1, page_size=5)
primary_testset = client.tasks.create_testset("awesome-hub", 42, index=0)
for event in client.tasks.upload_testset_zip(
    "awesome-hub",
    42,
    primary_testset.id,
    zip_path="fixtures/testset.zip",
):
    print(event.status, event.message)

# Maintain examples
client.tasks.set_examples(
    "awesome-hub",
    42,
    inputs=["2\n1 1"],
    outputs=["1"],
)

# Inspect / mutate structural metadata
current_type = client.tasks.get_type("awesome-hub", 42)
if current_type["type"] != "batch":
    client.tasks.update_type("awesome-hub", 42, {"type": "batch"})
client.tasks.update_interactor("awesome-hub", 42, {"interactor": "/* C++ code */", "language": "cpp"})
client.tasks.upsert_grader("awesome-hub", 42, {"programming_language": "python", "code": "def grade(): ..."})
checker = client.tasks.get_checker("awesome-hub", 42)
if checker["checker_type"] != "single_or_multiple_double_ignore_whitespaces":
    client.tasks.update_checker(
        "awesome-hub",
        42,
        {"checker_type": "single_or_multiple_double_ignore_whitespaces", "precision": 9},
    )
```

Streaming uploads surface a generator of server-sent events. Use `stream=False` if you only care about the terminal state.

`TaskStatements`, `TaskExamples`, `TestSetDetail`, and `TestSetUploadEvent` models (all tolerant Pydantic models) make it easy to validate responses while remaining forward compatible with backend changes.

> **Checkers:** `TasksClient.update_checker` accepts any backend-supported `checker_type` (e.g., `compare_lines_ignore_whitespaces.cpp`, `single_or_multiple_double_ignore_whitespaces.cpp`, `single_or_multiple_int64_ignore_whitespaces.cpp`, `single_or_multiple_yes_or_no_case_insensitive.cpp`, `single_yes_or_no_case_insensitive.cpp`) and lets you supply custom checker source via `checker`/`checker_language` when using `custom_checker`.

## Filters and pagination

Complex endpoints expose dedicated filter builders (e.g., `SubmissionsFilter`, `CompetitionsFilter`). These helpers are chainable and produce validated query parameter dictionaries via `.to_params()`. Paginated responses implement `Page[T]` models, and the helper `iter_pages` lets you transparently iterate over all results.

```python
from codeany_hub.filters.submissions import SubmissionsFilter

flt = (
    SubmissionsFilter()
    .verdict("AC")
    .score_between(50, 100)
    .per_page(200)
)

page = client.submissions.list("awesome-hub", filter=flt)
for submission in page.results:
    print(submission.id, submission.verdict)
```

## Environment configuration

For CLI tools and local scripts you can bootstrap the client directly from environment variables:

```bash
export CODEANY_BASE_URL="https://codeany.org"
export CODEANY_AUTH=hub_login
export CODEANY_HUB=awesome-hub
export CODEANY_USERNAME=alice
export CODEANY_PASSWORD=s3cret
export CODEANY_TOKEN_STORE_PATH="$HOME/.cache/codeany/tokens.json"
```

```python
from codeany_hub import CodeanyClient

client = CodeanyClient.from_env()
```

Use `AsyncCodeanyClient.from_env()` for async workflows. Optional knobs such as `CODEANY_FETCH_DOCS`, `CODEANY_RETRIES`, and `CODEANY_LOG_REQUESTS` tune transport behaviour without code changes.

## Error handling

Errors are normalized by `codeany_hub.core.errors`. Responses with status `>= 400` raise typed exceptions:

- `NotFoundError` (404)
- `ValidationError` (400)
- `RateLimitError` (429)
- `AuthError` (401/403)
- `ApiError` (generic fallback)

Each exception exposes the HTTP status, a user-friendly message, and the raw payload.

## Roadmap

- ✅ **Phase 1:** Synchronous `CodeanyClient`, resource coverage, composable filters.
- ✅ **Phase 2:** Async transport + `AsyncCodeanyClient`, capability probing, file-based token stores.
- ✅ **Phase 3:** Request/response hooks, structured logging, configurable retries.
- ✅ **Phase 4:** First-class enums for verdicts/statuses, typed statement/editorial models, env bootstrapping.
- ✅ **Phase 5:** Rich documentation site, scenario-driven integration tests, and pluggable retry policies.
- ✅ **Phase 6:** Deep integration guides, CLI helpers, and end-to-end contract tests.
- 🔭 **Phase 7:** Add MCP-ready webhooks, streaming endpoints, and code generation recipes.

## TODO

- [x] Add asynchronous transport and `AsyncCodeanyClient` mirroring the sync surface.
- [x] Expose request/response hook integrations and configurable retry logic.
- [x] Formalize verdict/status enums and expand typed models for statements/editorials.
- [x] Add support for environment-based configuration.
- [x] Provide scenario-level tests with `pytest-httpx` covering multi-step task/competition flows.
- [x] Publish an extended documentation site with richer guides and examples.

## Contributing

1. Clone the repository and install dependencies in a virtual environment.
2. Run `pip install -e ".[dev]"`.
3. Execute `ruff check .` and `pytest` before opening a PR.
