# Getting Started

This guide expands on the repository quick start by focusing on environment
driven configuration, recommended defaults, and first calls.

## Configure credentials

```bash
export CODEANY_BASE_URL="https://hub.codeany.dev"
export CODEANY_USERNAME="alice"
export CODEANY_PASSWORD="s3cret"
# Optional extras
export CODEANY_HUB="awesome-hub"
export CODEANY_LOG_REQUESTS=1
export CODEANY_RETRIES=2
export CODEANY_RETRY_BACKOFF=0.3
```

## Instantiate clients

```python
from codeany_hub import AsyncCodeanyClient, CodeanyClient

# Synchronous client using the env helper.
client = CodeanyClient.from_env()

# Async client mirrors the same knobs when awaited.
async_client = await AsyncCodeanyClient.from_env()
```

## Make first calls

```python
from codeany_hub.filters import SubmissionsFilter
from codeany_hub.models import SubmissionOrdering

with CodeanyClient.from_env() as client:
    hubs = client.hubs.list_mine()
    if hubs:
        first = hubs[0].slug
        page = client.submissions.list(
            first,
            filter=(
                SubmissionsFilter()
                .ordering(SubmissionOrdering.CREATED_DESC)
                .per_page(100)
            ),
        )
        for row in page.results:
            print(row.id, row.verdict_enum)
```

## What’s next?

- Explore [retry policies & hooks](./retry-policies.md) to instrument outbound
  traffic.
- Walk through [scenario playbooks](./scenarios.md) for multi-step workflows.
