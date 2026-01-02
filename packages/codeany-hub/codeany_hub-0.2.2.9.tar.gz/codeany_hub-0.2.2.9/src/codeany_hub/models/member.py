"""Member-related models."""

from __future__ import annotations

from .common import ISODateTime, TolerantModel
from .hub import Hub, Profile


class MemberProfile(TolerantModel):
    username: str
    display_name: str | None = None
    email: str | None = None
    avatar: str | None = None
    phone: str | None = None
    biography: str | None = None
    location: str | None = None
    updated_at: ISODateTime | None = None


class Member(TolerantModel):
    hub: Hub | None = None
    profile: Profile | None = None
    member_profile: MemberProfile | None = None
    permissions: list[str] | None = None
    role: str | None = None
    joined_at: ISODateTime | None = None
