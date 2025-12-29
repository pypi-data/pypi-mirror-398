"""Teams API module for Mattermost team operations."""

from mm_async.api.base import BaseAPI
from mm_async.exceptions import MattermostNotFoundError, MattermostValidationError
from mm_async.models import Team, TeamMember


def _validate_id(value: str, name: str) -> None:
    """Validate that an ID is not empty."""
    if not value or not value.strip():
        raise MattermostValidationError(f"{name} cannot be empty")


def _validate_string(value: str, name: str) -> None:
    """Validate that a string is not empty."""
    if not value or not value.strip():
        raise MattermostValidationError(f"{name} cannot be empty")


class TeamsAPI(BaseAPI):
    """API for managing Mattermost teams and team members."""

    async def search(self, term: str) -> list[Team]:
        """Search for teams by term.

        Args:
            term: The search term (team name or display name).

        Returns:
            list[Team]: List of matching teams.

        Raises:
            MattermostError: If the API request fails.
        """
        data = await self._client.post("/teams/search", json={"term": term})
        return [Team(**team) for team in data]

    async def get_by_id(self, team_id: str) -> Team:
        """Get a team by ID.

        Args:
            team_id: The ID of the team to retrieve.

        Returns:
            Team: The team object.

        Raises:
            MattermostValidationError: If team_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        data = await self._client.get(f"/teams/{team_id}")
        return Team(**data)

    async def get_member(self, team_id: str, user_id: str) -> TeamMember:
        """Get a team member by team ID and user ID.

        Args:
            team_id: The ID of the team.
            user_id: The ID of the user.

        Returns:
            TeamMember: The team member object.

        Raises:
            MattermostValidationError: If team_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        _validate_id(user_id, "user_id")
        data = await self._client.get(f"/teams/{team_id}/members/{user_id}")
        return TeamMember(**data)

    async def add_member(self, team_id: str, user_id: str) -> TeamMember:
        """Add a user to a team.

        Args:
            team_id: The ID of the team.
            user_id: The ID of the user to add.

        Returns:
            TeamMember: The created team member object.

        Raises:
            MattermostValidationError: If team_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        _validate_id(user_id, "user_id")
        data = await self._client.post(
            f"/teams/{team_id}/members", json={"team_id": team_id, "user_id": user_id}
        )
        return TeamMember(**data)

    async def remove_member(self, team_id: str, user_id: str) -> dict:
        """Remove a user from a team.

        Args:
            team_id: The ID of the team.
            user_id: The ID of the user to remove.

        Returns:
            dict: Empty dict on success.

        Raises:
            MattermostValidationError: If team_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        _validate_id(user_id, "user_id")
        return await self._client.delete(f"/teams/{team_id}/members/{user_id}")

    async def set_admin(self, team_id: str, user_id: str) -> bool:
        """Grant team admin role to a user.

        Args:
            team_id: The ID of the team.
            user_id: The ID of the user.

        Returns:
            bool: True if the operation was successful.

        Raises:
            MattermostValidationError: If team_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        _validate_id(user_id, "user_id")
        data = await self._client.put(
            f"/teams/{team_id}/members/{user_id}/schemeRoles",
            json={"scheme_admin": True, "scheme_user": True},
        )
        return data.get("status") == "OK"

    async def remove_admin(self, team_id: str, user_id: str) -> bool:
        """Remove team admin role from a user.

        Args:
            team_id: The ID of the team.
            user_id: The ID of the user.

        Returns:
            bool: True if the operation was successful.

        Raises:
            MattermostValidationError: If team_id or user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        _validate_id(user_id, "user_id")
        data = await self._client.put(
            f"/teams/{team_id}/members/{user_id}/schemeRoles",
            json={"scheme_admin": False, "scheme_user": True},
        )
        return data.get("status") == "OK"

    async def get_all(self, page: int = 0, per_page: int = 60) -> list[Team]:
        """Get all teams (paginated).

        Args:
            page: Page number (0-indexed).
            per_page: Number of teams per page (max 200).

        Returns:
            list[Team]: List of teams.

        Raises:
            MattermostError: If the API request fails.
        """
        data = await self._client.get(
            "/teams", params={"page": page, "per_page": per_page}
        )
        return [Team(**team) for team in data]

    async def get_by_name(self, name: str) -> Team | None:
        """Get a team by name.

        Args:
            name: The team name (URL-safe identifier, not display_name).

        Returns:
            Team if found, None if team doesn't exist.

        Raises:
            MattermostValidationError: If name is empty.
            MattermostError: If the API request fails (except 404).
        """
        _validate_string(name, "name")
        try:
            data = await self._client.get(f"/teams/name/{name}")
            return Team(**data)
        except MattermostNotFoundError:
            return None

    async def get_members(
        self, team_id: str, page: int = 0, per_page: int = 60
    ) -> list[TeamMember]:
        """Get team members (paginated).

        Args:
            team_id: The ID of the team.
            page: Page number (0-indexed).
            per_page: Number of members per page (max 200).

        Returns:
            list[TeamMember]: List of team members.

        Raises:
            MattermostValidationError: If team_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        data = await self._client.get(
            f"/teams/{team_id}/members", params={"page": page, "per_page": per_page}
        )
        return [TeamMember(**member) for member in data]

    async def create(
        self, name: str, display_name: str, team_type: str = "O"
    ) -> Team:
        """Create a new team.

        Args:
            name: Unique team name (URL-safe identifier).
            display_name: Display name shown in UI.
            team_type: Team type - "O" for open, "I" for invite-only.

        Returns:
            Team: The created team object.

        Raises:
            MattermostValidationError: If name or display_name is empty.
            MattermostError: If the API request fails.
        """
        _validate_string(name, "name")
        _validate_string(display_name, "display_name")
        data = await self._client.post(
            "/teams",
            json={"name": name, "display_name": display_name, "type": team_type},
        )
        return Team(**data)
