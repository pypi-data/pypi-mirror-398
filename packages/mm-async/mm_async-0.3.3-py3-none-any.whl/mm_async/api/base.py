"""Base API class for Mattermost API modules."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mm_async.client import AsyncMattermostClient


class BaseAPI:
    """Base class for all API modules.

    Provides access to the underlying AsyncMattermostClient instance.
    """

    def __init__(self, client: "AsyncMattermostClient") -> None:
        """Initialize the API module.

        Args:
            client: The AsyncMattermostClient instance to use for API calls.
        """
        self._client = client
