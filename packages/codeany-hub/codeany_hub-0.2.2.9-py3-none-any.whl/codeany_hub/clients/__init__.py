"""Resource clients exposed by :class:`CodeanyClient`."""

from .base import AsyncBaseClient, BaseClient
from .competitions import AsyncCompetitionsClient, CompetitionsClient
from .hubs import AsyncHubsClient, HubsClient
from .imports import AsyncImportsClient, ImportsClient
from .judge import AsyncJudgeClient, JudgeClient
from .mcq import AsyncMCQClient, MCQClient
from .members import AsyncMembersClient, MembersClient
from .ratings import AsyncRatingsClient, RatingsClient
from .submissions import AsyncSubmissionsClient, SubmissionsClient
from .tasks import AsyncTasksClient, TasksClient
from .users import AsyncUsersClient, UsersClient

__all__ = [
    "AsyncBaseClient",
    "AsyncCompetitionsClient",
    "AsyncHubsClient",
    "AsyncImportsClient",
    "AsyncJudgeClient",
    "AsyncMCQClient",
    "AsyncMembersClient",
    "AsyncRatingsClient",
    "AsyncSubmissionsClient",
    "AsyncTasksClient",
    "AsyncUsersClient",
    "BaseClient",
    "CompetitionsClient",
    "HubsClient",
    "ImportsClient",
    "JudgeClient",
    "MCQClient",
    "MembersClient",
    "RatingsClient",
    "SubmissionsClient",
    "TasksClient",
    "UsersClient",
]
