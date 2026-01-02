# Agent Playbook for `codeany-hub`

This repository is maintained with the help of AI coding assistants. The guidelines below keep interactions predictable, reproducible, and aligned with project goals.

## Golden rules

- **Preserve public API stability.** Never introduce breaking changes without an explicit migration note and version bump.
- **Prefer additions over modifications.** When backend behavior expands, add new optional arguments or models instead of altering existing ones.
- **Keep models tolerant.** All Pydantic models must inherit from `TolerantModel` (configured with `extra="allow"`). Unknown fields should never break deserialization.
- **Document reasoning.** When decisions are non-trivial, add succinct comments or docstrings explaining the trade-offs.

## Workflow expectations

1. **Plan before acting.** Outline the intended change (file list, new APIs, risks) and get user confirmation when the scope is ambiguous.
2. **Use apply_patch where practical.** Limit full file rewrites to generated or brand-new files.
3. **Install project requirements.** Use `pip install -r requirements.txt` to ensure runtime and tooling deps are available.
4. **Validate format and style.** Prefer `scripts/run_tests.sh` (runs `ruff` + `pytest`) before handing work back; otherwise, describe the validation you could not perform.
5. **Surface risks early.** Highlight edge cases, backwards-compatibility concerns, and missing test coverage in the final summary.
6. **Keep docs aligned.** Update `README.md` (and any relevant guides) whenever you add or change public SDK behaviour—especially new client methods or streaming patterns.

## Code patterns to follow

- **Transport pattern:** Reuse `codeany_hub.core.transport.Transport` for all outbound HTTP calls. Authentication refresh must always flow through `AuthStrategy`.
- **Error handling:** Wrap every HTTP call with `raise_for_response`. Resource clients should avoid try/except unless they augment context.
- **Pagination:** Return `Page[T]` models for paginated endpoints and expose helper iterators when they improve ergonomics.
- **Filters:** Builder APIs must be chainable, immutable (return `self` after copying state), and convert cleanly to query dictionaries via `.to_params()`.
- **Streaming endpoints:** Use `Transport.stream(...)` / `AsyncTransport.stream(...)` for SSE or chunked uploads to inherit retry/auth logic. Parse events with tolerant helpers and expose ergonomic generators.
- **Task assets:** When handling file uploads (statements, testsets, examples), accept flexible sources (paths, bytes, file objects) and normalise them via shared helpers so CLIs and tests remain straightforward.
- **Hub identifiers:** Backend routers expect `hub_name` (slug) segments. Models should normalise `slug`/`hub_name`/`name`, and clients must never rely on integer IDs or titles when constructing `/api/hubs/<slug>/...` paths.

## When unsure

- If API coverage in the backend differs from the existing clients, add a capability flag in `CapabilityProbe` and gate the new feature behind it.
- Ask for clarification when backend contracts are ambiguous or undocumented.
- Suggest tests or mocks whenever adding new request flows that rely on HTTP side effects.

## Release checklist

Before cutting a new release:

1. Update `pyproject.toml` version.
2. Review `CHANGELOG.md` (create if missing).
3. Run `scripts/run_tests.sh` (ruff + pytest) and any targeted integration tests (mocked HTTPX recommended).
4. Tag the release and publish to PyPI via `hatch build && twine upload dist/*`.

Following this playbook keeps the SDK reliable and future-proof while enabling high-quality AI-assisted contributions.
