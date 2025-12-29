"""Pydantic models for Mattermost API responses."""

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Mattermost user model."""

    model_config = ConfigDict(extra="ignore")

    id: str
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    nickname: str | None = None
    position: str | None = None
    roles: str | None = None


class Team(BaseModel):
    """Mattermost team model."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    display_name: str
    type: str  # "O" (open) | "I" (invite-only)
    description: str | None = None


class Channel(BaseModel):
    """Mattermost channel model."""

    model_config = ConfigDict(extra="ignore")

    id: str
    team_id: str
    name: str
    display_name: str
    type: str  # "O" (public) | "P" (private) | "D" (direct) | "G" (group)
    header: str | None = None
    purpose: str | None = None


class Post(BaseModel):
    """Mattermost post model."""

    model_config = ConfigDict(extra="ignore")

    id: str
    channel_id: str
    user_id: str
    message: str
    root_id: str | None = None
    create_at: int | None = None
    update_at: int | None = None


class TeamMember(BaseModel):
    """Mattermost team member model."""

    model_config = ConfigDict(extra="ignore")

    team_id: str
    user_id: str
    roles: str
    delete_at: int | None = None
    scheme_admin: bool | None = None
    scheme_user: bool | None = None


class ChannelMember(BaseModel):
    """Mattermost channel member model."""

    model_config = ConfigDict(extra="ignore")

    channel_id: str
    user_id: str
    roles: str
    scheme_admin: bool | None = None
    scheme_user: bool | None = None
