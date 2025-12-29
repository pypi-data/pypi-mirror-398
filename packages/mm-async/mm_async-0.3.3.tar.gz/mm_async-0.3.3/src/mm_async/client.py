"""Async HTTP client for Mattermost API."""

import logging
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import SecretStr

if TYPE_CHECKING:
    from .api import ChannelsAPI, PostsAPI, TeamsAPI, UsersAPI

from .exceptions import (
    MattermostAuthError,
    MattermostConnectionError,
    MattermostError,
    MattermostForbiddenError,
    MattermostNotFoundError,
    MattermostRateLimitError,
    MattermostServerError,
)
from .retry import with_retry

logger = logging.getLogger(__name__)


class AsyncMattermostClient:
    """
    Async HTTP client for Mattermost API.

    Usage:
        client = AsyncMattermostClient(
            url="https://mattermost.example.com",
            token="your-bot-token",
        )
        await client.connect()

        user = await client.get("/users/me")
        teams = await client.post("/teams/search", json={"term": "dev"})

        await client.close()

    Or with context manager:
        async with AsyncMattermostClient(url=..., token=...) as client:
            user = await client.get("/users/me")
    """

    def __init__(
        self,
        url: str,
        token: str | SecretStr,
        *,
        verify_ssl: bool = True,
        timeout: float = 30.0,
        connect_timeout: float = 10.0,
    ):
        """
        Initialize the client.

        Args:
            url: Mattermost server URL (e.g., "https://mm.example.com:8065")
            token: Bot or user access token (str or SecretStr for security)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            connect_timeout: Connection timeout in seconds
        """
        self._base_url = url.rstrip("/") + "/api/v4"
        # Store token as SecretStr for security (prevents accidental logging)
        self._token = token if isinstance(token, SecretStr) else SecretStr(token)
        self._verify_ssl = verify_ssl

        if not verify_ssl:
            logger.warning("SSL verification disabled - NOT RECOMMENDED for production")
        self._timeout = timeout
        self._connect_timeout = connect_timeout

        self._client: httpx.AsyncClient | None = None
        self._bot_user_id: str | None = None
        self._bot_teams: list[dict[str, Any]] | None = None

        # Lazy-initialized API namespaces
        self._users: "UsersAPI | None" = None
        self._teams: "TeamsAPI | None" = None
        self._channels: "ChannelsAPI | None" = None
        self._posts: "PostsAPI | None" = None

    async def connect(self) -> None:
        """Initialize the HTTP client and validate connection."""
        if self._client is not None:
            return

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._token.get_secret_value()}",
                "Content-Type": "application/json",
            },
            verify=self._verify_ssl,
            timeout=httpx.Timeout(self._timeout, connect=self._connect_timeout),
        )

        # Validate connection
        try:
            user = await self.get("/users/me")
            self._bot_user_id = user.get("id")
            logger.info("Connected to Mattermost as user ID: %s", self._bot_user_id)
        except Exception as e:
            await self.close()
            raise MattermostConnectionError(f"Failed to connect: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._bot_user_id = None
        self._bot_teams = None
        self._users = None
        self._teams = None
        self._channels = None
        self._posts = None

    async def __aenter__(self) -> "AsyncMattermostClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    # --- Properties ---

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._client is not None

    @property
    def bot_user_id(self) -> str | None:
        """Get cached bot user ID."""
        return self._bot_user_id

    # --- High-Level API Namespaces ---

    @property
    def users(self) -> "UsersAPI":
        """High-level Users API."""
        if self._users is None:
            from .api import UsersAPI
            self._users = UsersAPI(self)
        return self._users

    @property
    def teams(self) -> "TeamsAPI":
        """High-level Teams API."""
        if self._teams is None:
            from .api import TeamsAPI
            self._teams = TeamsAPI(self)
        return self._teams

    @property
    def channels(self) -> "ChannelsAPI":
        """High-level Channels API."""
        if self._channels is None:
            from .api import ChannelsAPI
            self._channels = ChannelsAPI(self)
        return self._channels

    @property
    def posts(self) -> "PostsAPI":
        """High-level Posts API."""
        if self._posts is None:
            from .api import PostsAPI
            self._posts = PostsAPI(self)
        return self._posts

    # --- Error Handling ---

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Convert HTTP errors to custom exceptions."""
        if response.is_success:
            return

        status = response.status_code
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}

        message = body.get("message", f"HTTP {status}")

        if status == 401:
            raise MattermostAuthError(message, status, body)
        elif status == 403:
            raise MattermostForbiddenError(message, status, body)
        elif status == 404:
            raise MattermostNotFoundError(message, status, body)
        elif status == 429:
            # Parse Retry-After header if present
            retry_after = None
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = float(retry_after_header)
                except ValueError:
                    pass  # Ignore non-numeric values
            raise MattermostRateLimitError(message, status, body, retry_after=retry_after)
        elif status >= 500:
            raise MattermostServerError(message, status, body)
        else:
            raise MattermostError(message, status, body)

    def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if not self._client:
            raise MattermostConnectionError("Client not connected. Call connect() first.")

    # --- HTTP Methods ---

    @with_retry()
    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """
        GET request with automatic retry.

        Args:
            endpoint: API endpoint (e.g., "/users/me")
            params: Query parameters

        Returns:
            Response JSON
        """
        self._ensure_connected()

        try:
            response = await self._client.get(endpoint, params=params)  # type: ignore[union-attr]
            self._raise_for_status(response)
            return response.json()
        except httpx.ConnectError as e:
            raise MattermostConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise MattermostConnectionError(f"Timeout: {e}") from e

    async def post(self, endpoint: str, json: dict[str, Any] | list[Any] | None = None) -> Any:
        """
        POST request (NO retry to avoid duplicates).

        Args:
            endpoint: API endpoint
            json: Request body

        Returns:
            Response JSON
        """
        self._ensure_connected()

        try:
            response = await self._client.post(endpoint, json=json)  # type: ignore[union-attr]
            self._raise_for_status(response)
            return response.json()
        except httpx.ConnectError as e:
            raise MattermostConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise MattermostConnectionError(f"Timeout: {e}") from e

    async def put(self, endpoint: str, json: dict[str, Any] | None = None) -> Any:
        """
        PUT request (NO retry).

        Args:
            endpoint: API endpoint
            json: Request body

        Returns:
            Response JSON
        """
        self._ensure_connected()

        try:
            response = await self._client.put(endpoint, json=json)  # type: ignore[union-attr]
            self._raise_for_status(response)
            return response.json()
        except httpx.ConnectError as e:
            raise MattermostConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise MattermostConnectionError(f"Timeout: {e}") from e

    @with_retry()
    async def delete(self, endpoint: str) -> Any:
        """
        DELETE request with automatic retry (idempotent).

        Args:
            endpoint: API endpoint

        Returns:
            Response JSON or {"status": "ok"}
        """
        self._ensure_connected()

        try:
            response = await self._client.delete(endpoint)  # type: ignore[union-attr]
            self._raise_for_status(response)
            if response.content:
                return response.json()
            return {"status": "ok"}
        except httpx.ConnectError as e:
            raise MattermostConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise MattermostConnectionError(f"Timeout: {e}") from e

    # --- Convenience Methods ---

    async def get_bot_user_id(self) -> str | None:
        """Get bot's user ID (cached after connect)."""
        if self._bot_user_id is None and self._client:
            user = await self.get("/users/me")
            self._bot_user_id = user.get("id")
        return self._bot_user_id

    async def get_bot_teams(self) -> list[dict[str, Any]]:
        """Get teams the bot belongs to (cached)."""
        if self._bot_teams is None:
            self._bot_teams = await self.get("/users/me/teams")
        return self._bot_teams or []
