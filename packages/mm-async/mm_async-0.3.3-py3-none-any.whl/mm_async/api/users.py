"""Users API module for Mattermost user operations."""

from typing import Any

from mm_async.api.base import BaseAPI
from mm_async.exceptions import MattermostNotFoundError, MattermostValidationError
from mm_async.models import User


def _validate_id(value: str, name: str) -> None:
    """Validate that an ID is not empty."""
    if not value or not value.strip():
        raise MattermostValidationError(f"{name} cannot be empty")


def _validate_string(value: str, name: str) -> None:
    """Validate that a string is not empty."""
    if not value or not value.strip():
        raise MattermostValidationError(f"{name} cannot be empty")


class UsersAPI(BaseAPI):
    """API for managing Mattermost users."""

    async def get_me(self) -> User:
        """Get the current authenticated user.

        Returns:
            User: The current user object.

        Raises:
            MattermostError: If the API request fails.
        """
        data = await self._client.get("/users/me")
        return User(**data)

    async def get_by_id(self, user_id: str) -> User:
        """Get a user by ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            User: The user object.

        Raises:
            MattermostValidationError: If user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(user_id, "user_id")
        data = await self._client.get(f"/users/{user_id}")
        return User(**data)

    async def search(self, term: str) -> list[User]:
        """Search for users by term.

        Args:
            term: The search term (username, email, or name).

        Returns:
            list[User]: List of matching users.

        Raises:
            MattermostError: If the API request fails.
        """
        data = await self._client.post("/users/search", json={"term": term})
        return [User(**user) for user in data]

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username.

        Args:
            username: The username (without @).

        Returns:
            User if found, None if user doesn't exist.

        Raises:
            MattermostValidationError: If username is empty.
            MattermostError: If the API request fails (except 404).
        """
        _validate_string(username, "username")
        clean_username = username.lstrip("@").strip()
        try:
            data = await self._client.get(f"/users/username/{clean_username}")
            return User(**data)
        except MattermostNotFoundError:
            return None

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email.

        Args:
            email: The user's email address.

        Returns:
            User if found, None if user doesn't exist.

        Raises:
            MattermostValidationError: If email is empty.
            MattermostError: If the API request fails (except 404).
        """
        _validate_string(email, "email")
        try:
            data = await self._client.get(f"/users/email/{email}")
            return User(**data)
        except MattermostNotFoundError:
            return None

    async def get_status(self, user_id: str) -> dict[str, Any]:
        """Get a user's status.

        Args:
            user_id: The ID of the user.

        Returns:
            dict: Status object with 'status', 'manual', 'last_activity_at'.

        Raises:
            MattermostValidationError: If user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(user_id, "user_id")
        return await self._client.get(f"/users/{user_id}/status")

    async def update(self, user_id: str, **fields: Any) -> User:
        """Update a user's fields.

        Args:
            user_id: The ID of the user to update.
            **fields: Fields to update (e.g., first_name, last_name, nickname).

        Returns:
            User: The updated user object.

        Raises:
            MattermostValidationError: If user_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(user_id, "user_id")
        data = await self._client.put(f"/users/{user_id}/patch", json=fields)
        return User(**data)
