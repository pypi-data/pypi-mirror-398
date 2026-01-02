"""Minimal usage examples for the Codeany Hub SDK."""

from __future__ import annotations

import asyncio
import os

from codeany_hub import AsyncCodeanyClient, CodeanyClient
from codeany_hub.filters import SubmissionsFilter
from codeany_hub.models import SubmissionOrdering, SubmissionVerdict


BASE_URL = os.getenv("CODEANY_BASE_URL", "https://hub.codeany.dev")
USERNAME = os.getenv("CODEANY_USERNAME", "alice")
PASSWORD = os.getenv("CODEANY_PASSWORD", "s3cret")
DEFAULT_HUB = os.getenv("CODEANY_HUB")


def main() -> None:
    """Run a synchronous workflow using the convenience factory."""

    with CodeanyClient.with_simple_jwt(
        base_url=BASE_URL,
        username=USERNAME,
        password=PASSWORD,
    ) as client:
        hubs = client.hubs.list_mine()
        print("Your hubs:")
        for hub in hubs:
            print(f"- {hub.slug} ({hub.display_name})")

        target = DEFAULT_HUB or (client.default_hub or (hubs[0].slug if hubs else None))
        if target:
            submissions = client.submissions.list(
                target,
                filter=(
                    SubmissionsFilter()
                    .verdict(SubmissionVerdict.ACCEPTED)
                    .ordering(SubmissionOrdering.CREATED_DESC)
                    .per_page(10)
                ),
            )
            print(f"\nRecent submissions for {target}:")
            for row in submissions.results:
                author = row.author.username if row.author else "unknown"
                print(f"#{row.id} {row.verdict_enum or row.verdict} by {author}")


async def async_main() -> None:
    """Mirror the pattern with the async client."""

    hub = DEFAULT_HUB or "awesome-hub"
    client = await AsyncCodeanyClient.with_hub_login(
        base_url=BASE_URL,
        hub=hub,
        username=USERNAME,
        password=PASSWORD,
    )
    try:
        hubs = await client.hubs.list_mine()
        print("Async hubs:")
        for hub in hubs:
            print(f"- {hub.slug} ({hub.display_name})")
    finally:
        await client.aclose()


if __name__ == "__main__":
    main()
    if os.getenv("CODEANY_RUN_ASYNC_EXAMPLE") == "1":
        asyncio.run(async_main())
