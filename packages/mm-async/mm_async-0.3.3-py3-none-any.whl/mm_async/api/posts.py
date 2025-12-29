"""Posts API module for Mattermost post operations."""

from typing import Any

from mm_async.api.base import BaseAPI
from mm_async.exceptions import MattermostValidationError
from mm_async.models import Post


def _validate_id(value: str, name: str) -> None:
    """Validate that an ID is not empty."""
    if not value or not value.strip():
        raise MattermostValidationError(f"{name} cannot be empty")


class PostsAPI(BaseAPI):
    """API for managing Mattermost posts (messages)."""

    async def create(
        self, channel_id: str, message: str, root_id: str | None = None
    ) -> Post:
        """Create a new post in a channel.

        Args:
            channel_id: The ID of the channel to post in.
            message: The message content to post.
            root_id: Optional ID of the root post for threading.

        Returns:
            Post: The created post object.

        Raises:
            MattermostValidationError: If channel_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        payload: dict[str, Any] = {"channel_id": channel_id, "message": message}
        if root_id:
            payload["root_id"] = root_id
        data = await self._client.post("/posts", json=payload)
        return Post(**data)

    async def get_by_id(self, post_id: str) -> Post:
        """Get a post by ID.

        Args:
            post_id: The ID of the post to retrieve.

        Returns:
            Post: The post object.

        Raises:
            MattermostValidationError: If post_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(post_id, "post_id")
        data = await self._client.get(f"/posts/{post_id}")
        return Post(**data)

    async def get_for_channel(
        self, channel_id: str, page: int = 0, per_page: int = 60
    ) -> list[Post]:
        """Get posts for a channel (paginated, newest first).

        Args:
            channel_id: The ID of the channel.
            page: Page number (0-indexed).
            per_page: Number of posts per page (max 200).

        Returns:
            list[Post]: List of posts in the channel.

        Raises:
            MattermostValidationError: If channel_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(channel_id, "channel_id")
        data = await self._client.get(
            f"/channels/{channel_id}/posts",
            params={"page": page, "per_page": per_page},
        )
        # API returns {order: [...], posts: {...}} structure
        posts_dict = data.get("posts", {})
        order = data.get("order", [])
        return [Post(**posts_dict[post_id]) for post_id in order if post_id in posts_dict]

    async def update(self, post_id: str, message: str) -> Post:
        """Update a post's message.

        Args:
            post_id: The ID of the post to update.
            message: The new message content.

        Returns:
            Post: The updated post object.

        Raises:
            MattermostValidationError: If post_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(post_id, "post_id")
        data = await self._client.put(f"/posts/{post_id}/patch", json={"message": message})
        return Post(**data)

    async def delete(self, post_id: str) -> dict:
        """Delete a post.

        Args:
            post_id: The ID of the post to delete.

        Returns:
            dict: Status response.

        Raises:
            MattermostValidationError: If post_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(post_id, "post_id")
        return await self._client.delete(f"/posts/{post_id}")

    async def get_thread(self, post_id: str) -> list[Post]:
        """Get all posts in a thread.

        Args:
            post_id: The ID of the root post.

        Returns:
            list[Post]: List of posts in the thread (including root).

        Raises:
            MattermostValidationError: If post_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(post_id, "post_id")
        data = await self._client.get(f"/posts/{post_id}/thread")
        # API returns {order: [...], posts: {...}} structure
        posts_dict = data.get("posts", {})
        order = data.get("order", [])
        return [Post(**posts_dict[post_id]) for post_id in order if post_id in posts_dict]

    async def search(self, team_id: str, terms: str) -> list[Post]:
        """Search for posts in a team.

        Args:
            team_id: The ID of the team to search in.
            terms: The search terms (supports Mattermost search syntax).

        Returns:
            list[Post]: List of matching posts.

        Raises:
            MattermostValidationError: If team_id is empty.
            MattermostError: If the API request fails.
        """
        _validate_id(team_id, "team_id")
        data = await self._client.post(
            f"/teams/{team_id}/posts/search", json={"terms": terms}
        )
        # API returns {order: [...], posts: {...}} structure
        posts_dict = data.get("posts", {})
        order = data.get("order", [])
        return [Post(**posts_dict[post_id]) for post_id in order if post_id in posts_dict]
