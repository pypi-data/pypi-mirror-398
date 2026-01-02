# Scenario Playbooks

The snippets below mirror the repository's scenario-focused unit tests and
serve as templates for common operational flows.

## Competition status dashboard

```python
from codeany_hub import CodeanyClient
from codeany_hub.filters import CompetitionsFilter

with CodeanyClient.from_env() as client:
    hub = client.default_hub or client.hubs.list_mine()[0].slug
    competitions = client.competitions.list(
        hub,
        filter=CompetitionsFilter().visible(True).rated(True),
    )
    for comp in competitions.results:
        rating = client.ratings.status(hub, comp.id)
        print(comp.name, rating.status_enum)
```

## Async member synchronization

```python
from codeany_hub import AsyncCodeanyClient


async def sync_members() -> None:
    client = await AsyncCodeanyClient.from_env()
    try:
        hub = client.default_hub or "demo"
        members_page = await client.members.list(hub, per_page=200)
        for member in members_page.results:
            print(member.profile.username, member.role)
    finally:
        await client.aclose()
```

## Bulk submission audit

```python
from codeany_hub import CodeanyClient
from codeany_hub.filters import SubmissionsFilter
from codeany_hub.models import SubmissionVerdict

with CodeanyClient.from_env() as client:
    hub = client.default_hub or "demo"
    flt = (
        SubmissionsFilter()
        .verdict(SubmissionVerdict.WRONG_ANSWER, SubmissionVerdict.TIME_LIMIT)
        .per_page(100)
    )
    for submission in client.submissions.iter_all(hub, filter=flt):
        print(submission.id, submission.verdict_enum)
```
