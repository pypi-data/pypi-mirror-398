"""Hub domain models."""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, Field

from .common import ISODateTime, TolerantModel


class Hub(TolerantModel):
    id: int | None = None
    slug: str = Field(validation_alias=AliasChoices("slug", "hub_name", "name"))
    display_name: str | None = None
    description: str | None = None
    created_at: ISODateTime | None = None
    updated_at: ISODateTime | None = None
    is_public: bool | None = None


class Profile(TolerantModel):
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar: str | None = None
    bio: str | None = None


class ProfileHub(TolerantModel):
    hub: Hub | None = None
    profile: Profile | None = None
    role: str | None = None
    permissions: list[str] | None = None
    joined_at: ISODateTime | None = None


class HubRegistration(TolerantModel):
    hub: Hub
    profile: Profile
    status: str | None = None
    extra: dict[str, Any] | None = None
