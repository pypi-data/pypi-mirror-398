"""Channels API module for Mattermost channel operations."""

from typing import Any

from mm_async.api.base import BaseAPI
from mm_async.exceptions import MattermostNotFoundError, MattermostValidationError
from mm_async.models import Channel, ChannelMember


def _validate_id(value: str, name: str) -> None:
    """Validate that an ID is not empty."""
    if not value or not value.strip():
        raise MattermostValidationError(f"{name} cannot be empty")


def _validate_string(value: str, name: str) -> None:
    """Validate that a string is not empty."""
    if not value or not value.strip():
        raise MattermostValidationError(f"{name} cannot be empty")


class ChannelsAPI(BaseAPI):
    """API for managing Mattermost channels and channel members."""

    async def get_by_team(self, team_id: str) -> list[Channel]:
        """Get all channels for a team.

        Args:
            team_id: The ID of the team.

        Returns:
            list[Channel]: List of channels in the team.

        Raises:
            MattermostValidationError: If team_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        data = await self._client.get(f"/teams/{team_id}/channels")
        return [Channel(**channel) for channel in data]

    async def list_channels(
        self,
        team_id: str | None = None,
        page: int = 0,
        per_page: int = 100,
        include_deleted: bool = False,
    ) -> list[Channel]:
        """List all channels (requires manage_system permission).

        Unlike get_by_team(), this can return private channels even if
        the user is not a member. Requires System Admin privileges.

        Args:
            team_id: Optional team ID to filter channels.
            page: Page number (0-indexed).
            per_page: Results per page (max 200, default 100).
            include_deleted: Whether to include deleted channels.

        Returns:
            list[Channel]: List of channels.

        Raises:
            MattermostForbiddenError: If user lacks manage_system permission.
            MattermostError: If the API request fails.
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": min(per_page, 200),
        }
        if team_id:
            params["team_id"] = team_id
        if include_deleted:
            params["include_deleted"] = "true"

        data = await self._client.get("/channels", params=params)
        return [Channel(**channel) for channel in data]

    async def get_by_id(self, channel_id: str) -> Channel:
        """Get a channel by ID.

        Args:
            channel_id: The ID of the channel to retrieve.

        Returns:
            Channel: The channel object.

        Raises:
            MattermostValidationError: If channel_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        data = await self._client.get(f"/channels/{channel_id}")
        return Channel(**data)

    async def get_member(self, channel_id: str, user_id: str) -> ChannelMember:
        """Get a channel member by channel ID and user ID.

        Args:
            channel_id: The ID of the channel.
            user_id: The ID of the user.

        Returns:
            ChannelMember: The channel member object.

        Raises:
            MattermostValidationError: If channel_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        _validate_id(user_id, "user_id")
        data = await self._client.get(f"/channels/{channel_id}/members/{user_id}")
        return ChannelMember(**data)

    async def add_member(self, channel_id: str, user_id: str) -> ChannelMember:
        """Add a user to a channel.

        Args:
            channel_id: The ID of the channel.
            user_id: The ID of the user to add.

        Returns:
            ChannelMember: The created channel member object.

        Raises:
            MattermostValidationError: If channel_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        _validate_id(user_id, "user_id")
        data = await self._client.post(
            f"/channels/{channel_id}/members", json={"user_id": user_id}
        )
        return ChannelMember(**data)

    async def remove_member(self, channel_id: str, user_id: str) -> dict:
        """Remove a user from a channel.

        Args:
            channel_id: The ID of the channel.
            user_id: The ID of the user to remove.

        Returns:
            dict: Empty dict on success.

        Raises:
            MattermostValidationError: If channel_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        _validate_id(user_id, "user_id")
        return await self._client.delete(f"/channels/{channel_id}/members/{user_id}")

    async def set_admin(self, channel_id: str, user_id: str) -> bool:
        """Grant channel admin role to a user.

        Args:
            channel_id: The ID of the channel.
            user_id: The ID of the user.

        Returns:
            bool: True if the operation was successful.

        Raises:
            MattermostValidationError: If channel_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        _validate_id(user_id, "user_id")
        data = await self._client.put(
            f"/channels/{channel_id}/members/{user_id}/schemeRoles",
            json={"scheme_admin": True, "scheme_user": True},
        )
        return data.get("status") == "OK"

    async def remove_admin(self, channel_id: str, user_id: str) -> bool:
        """Remove channel admin role from a user.

        Args:
            channel_id: The ID of the channel.
            user_id: The ID of the user.

        Returns:
            bool: True if the operation was successful.

        Raises:
            MattermostValidationError: If channel_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        _validate_id(user_id, "user_id")
        data = await self._client.put(
            f"/channels/{channel_id}/members/{user_id}/schemeRoles",
            json={"scheme_admin": False, "scheme_user": True},
        )
        return data.get("status") == "OK"

    async def create_direct(self, user_ids: list[str]) -> Channel:
        """Create a direct message channel between users.

        Args:
            user_ids: List of user IDs (must be 2 users for DM, or more for group message).

        Returns:
            Channel: The created direct channel object.

        Raises:
            MattermostValidationError: If user_ids has fewer than 2 users or contains empty IDs.
            MattermostError: If the API request fails.
        """
        if not user_ids or len(user_ids) < 2:
            raise MattermostValidationError("user_ids must contain at least 2 user IDs")
        for i, uid in enumerate(user_ids):
            _validate_id(uid, f"user_ids[{i}]")
        data = await self._client.post("/channels/direct", json=user_ids)
        return Channel(**data)

    async def search(self, team_id: str, term: str) -> list[Channel]:
        """Search for channels in a team.

        Args:
            team_id: The ID of the team.
            term: The search term (channel name or display name).

        Returns:
            list[Channel]: List of matching channels.

        Raises:
            MattermostValidationError: If team_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        data = await self._client.post(
            f"/teams/{team_id}/channels/search", json={"term": term}
        )
        return [Channel(**channel) for channel in data]

    async def get_by_name(self, team_id: str, name: str) -> Channel | None:
        """Get a channel by name.

        Args:
            team_id: The ID of the team.
            name: The channel name (URL-safe identifier, not display_name).

        Returns:
            Channel if found, None if channel doesn't exist.

        Raises:
            MattermostValidationError: If team_id or name is empty.
            MattermostError: If the API request fails (except 404).
        """
        _validate_id(team_id, "team_id")
        _validate_string(name, "name")
        try:
            data = await self._client.get(f"/teams/{team_id}/channels/name/{name}")
            return Channel(**data)
        except MattermostNotFoundError:
            return None

    async def create(
        self,
        team_id: str,
        name: str,
        display_name: str,
        channel_type: str = "O",
        purpose: str = "",
        header: str = "",
    ) -> Channel:
        """Create a new channel.

        Args:
            team_id: The ID of the team.
            name: Unique channel name (URL-safe identifier).
            display_name: Display name shown in UI.
            channel_type: Channel type - "O" for public, "P" for private.
            purpose: Channel purpose (optional).
            header: Channel header (optional).

        Returns:
            Channel: The created channel object.

        Raises:
            MattermostValidationError: If team_id, name, or display_name is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        _validate_string(name, "name")
        _validate_string(display_name, "display_name")
        data = await self._client.post(
            "/channels",
            json={
                "team_id": team_id,
                "name": name,
                "display_name": display_name,
                "type": channel_type,
                "purpose": purpose,
                "header": header,
            },
        )
        return Channel(**data)

    async def delete(self, channel_id: str) -> dict:
        """Delete a channel.

        Args:
            channel_id: The ID of the channel to delete.

        Returns:
            dict: Status response.

        Raises:
            MattermostValidationError: If channel_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        return await self._client.delete(f"/channels/{channel_id}")

    async def get_members(
        self, channel_id: str, page: int = 0, per_page: int = 60
    ) -> list[ChannelMember]:
        """Get channel members (paginated).

        Args:
            channel_id: The ID of the channel.
            page: Page number (0-indexed).
            per_page: Number of members per page (max 200).

        Returns:
            list[ChannelMember]: List of channel members.

        Raises:
            MattermostValidationError: If channel_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        data = await self._client.get(
            f"/channels/{channel_id}/members",
            params={"page": page, "per_page": per_page},
        )
        return [ChannelMember(**member) for member in data]
