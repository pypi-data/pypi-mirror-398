# API Reference

**mm-async v0.3.3** - Async HTTP client for Mattermost API

This document provides comprehensive API reference for all classes, methods, models, and exceptions in the mm-async library.

---

## Table of Contents

1. [AsyncMattermostClient](#asyncmattermostclient)
2. [UsersAPI](#usersapi)
3. [TeamsAPI](#teamsapi)
4. [ChannelsAPI](#channelsapi)
5. [PostsAPI](#postsapi)
6. [Models](#models)
7. [Exceptions](#exceptions)
8. [Retry Logic](#retry-logic)

---

## AsyncMattermostClient

The main client class for interacting with the Mattermost API. Provides low-level HTTP methods and high-level API namespace properties.

### Constructor

```python
AsyncMattermostClient(
    url: str,
    token: str | SecretStr,
    *,
    verify_ssl: bool = True,
    timeout: float = 30.0,
    connect_timeout: float = 10.0,
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | Required | Mattermost server URL (e.g., `"https://mm.example.com:8065"`) |
| `token` | `str \| SecretStr` | Required | Bot or user access token. Can be a plain string or Pydantic `SecretStr` for security |
| `verify_ssl` | `bool` | `True` | Whether to verify SSL certificates. Set to `False` only for development/testing |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `connect_timeout` | `float` | `10.0` | Connection timeout in seconds |

#### Example

```python
from mm_async import AsyncMattermostClient

# Basic usage
client = AsyncMattermostClient(
    url="https://mattermost.example.com",
    token="your-bot-token",
)

# With custom timeouts and disabled SSL verification (not recommended for production)
client = AsyncMattermostClient(
    url="https://mattermost.example.com",
    token="your-bot-token",
    verify_ssl=False,
    timeout=60.0,
    connect_timeout=15.0,
)
```

---

### Connection Management

#### `connect()`

Initialize the HTTP client and validate connection by fetching the authenticated user.

```python
async def connect() -> None
```

**Raises:**
- `MattermostConnectionError` - If connection fails or authentication is invalid

**Example:**

```python
client = AsyncMattermostClient(url="...", token="...")
await client.connect()
```

---

#### `close()`

Close the HTTP client and clean up resources.

```python
async def close() -> None
```

**Example:**

```python
await client.close()
```

---

#### Context Manager Usage

The client supports async context manager protocol for automatic connection management.

```python
async with AsyncMattermostClient(url="...", token="...") as client:
    # Client is automatically connected
    user = await client.users.get_me()
    # Client is automatically closed when exiting the context
```

---

### Properties

#### `is_connected`

Check if the client is currently connected.

```python
@property
def is_connected() -> bool
```

**Returns:** `bool` - `True` if connected, `False` otherwise

---

#### `bot_user_id`

Get the cached bot user ID (populated after `connect()`).

```python
@property
def bot_user_id() -> str | None
```

**Returns:** `str | None` - The bot's user ID or `None` if not connected

---

#### `users`

Access the Users API namespace.

```python
@property
def users() -> UsersAPI
```

**Returns:** `UsersAPI` instance

**Example:**

```python
user = await client.users.get_me()
results = await client.users.search("john")
```

---

#### `teams`

Access the Teams API namespace.

```python
@property
def teams() -> TeamsAPI
```

**Returns:** `TeamsAPI` instance

**Example:**

```python
team = await client.teams.get_by_name("developers")
members = await client.teams.get_members(team.id)
```

---

#### `channels`

Access the Channels API namespace.

```python
@property
def channels() -> ChannelsAPI
```

**Returns:** `ChannelsAPI` instance

**Example:**

```python
channels = await client.channels.get_by_team(team_id)
await client.channels.add_member(channel_id, user_id)
```

---

#### `posts`

Access the Posts API namespace.

```python
@property
def posts() -> PostsAPI
```

**Returns:** `PostsAPI` instance

**Example:**

```python
post = await client.posts.create(channel_id, "Hello, world!")
posts = await client.posts.get_for_channel(channel_id)
```

---

### HTTP Methods

Low-level HTTP methods for direct API access. These are used internally by the high-level API namespaces.

#### `get()`

Perform a GET request with automatic retry.

```python
async def get(
    endpoint: str,
    params: dict[str, Any] | None = None
) -> Any
```

**Parameters:**
- `endpoint` (`str`) - API endpoint path (e.g., `"/users/me"`)
- `params` (`dict[str, Any] | None`) - Query parameters

**Returns:** Parsed JSON response

**Raises:**
- `MattermostConnectionError` - Connection or timeout error
- `MattermostError` and subclasses - HTTP errors

**Example:**

```python
user = await client.get("/users/me")
teams = await client.get("/teams", params={"page": 0, "per_page": 100})
```

---

#### `post()`

Perform a POST request (no automatic retry to avoid duplicates).

```python
async def post(
    endpoint: str,
    json: dict[str, Any] | None = None
) -> Any
```

**Parameters:**
- `endpoint` (`str`) - API endpoint path
- `json` (`dict[str, Any] | None`) - Request body as JSON

**Returns:** Parsed JSON response

**Raises:**
- `MattermostConnectionError` - Connection or timeout error
- `MattermostError` and subclasses - HTTP errors

**Example:**

```python
teams = await client.post("/teams/search", json={"term": "dev"})
post = await client.post("/posts", json={
    "channel_id": "abc123",
    "message": "Hello!"
})
```

---

#### `put()`

Perform a PUT request (no automatic retry).

```python
async def put(
    endpoint: str,
    json: dict[str, Any] | None = None
) -> Any
```

**Parameters:**
- `endpoint` (`str`) - API endpoint path
- `json` (`dict[str, Any] | None`) - Request body as JSON

**Returns:** Parsed JSON response

**Raises:**
- `MattermostConnectionError` - Connection or timeout error
- `MattermostError` and subclasses - HTTP errors

**Example:**

```python
updated_user = await client.put("/users/user123/patch", json={
    "first_name": "John",
    "last_name": "Doe"
})
```

---

#### `delete()`

Perform a DELETE request with automatic retry (idempotent).

```python
async def delete(endpoint: str) -> Any
```

**Parameters:**
- `endpoint` (`str`) - API endpoint path

**Returns:** Parsed JSON response or `{"status": "ok"}` if no response body

**Raises:**
- `MattermostConnectionError` - Connection or timeout error
- `MattermostError` and subclasses - HTTP errors

**Example:**

```python
await client.delete("/posts/post123")
await client.delete("/channels/channel123")
```

---

### Convenience Methods

#### `get_bot_user_id()`

Get the bot's user ID (cached after first call).

```python
async def get_bot_user_id() -> str | None
```

**Returns:** `str | None` - The bot's user ID or `None` if not connected

---

#### `get_bot_teams()`

Get all teams the bot belongs to (cached after first call).

```python
async def get_bot_teams() -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - List of team objects

---

## UsersAPI

High-level API for managing Mattermost users. Access via `client.users`.

### Methods

#### `get_me()`

Get the current authenticated user.

```python
async def get_me() -> User
```

**Returns:** `User` - The current user object

**Raises:**
- `MattermostError` - If the API request fails

**Example:**

```python
user = await client.users.get_me()
print(f"Logged in as: {user.username}")
```

---

#### `get_by_id()`

Get a user by ID.

```python
async def get_by_id(user_id: str) -> User
```

**Parameters:**
- `user_id` (`str`) - The ID of the user to retrieve

**Returns:** `User` - The user object

**Raises:**
- `MattermostValidationError` - If `user_id` is empty
- `MattermostNotFoundError` - If user doesn't exist
- `MattermostError` - If the API request fails

**Example:**

```python
user = await client.users.get_by_id("abc123xyz")
print(f"User: {user.username} ({user.email})")
```

---

#### `search()`

Search for users by term (username, email, or name).

```python
async def search(term: str) -> list[User]
```

**Parameters:**
- `term` (`str`) - The search term

**Returns:** `list[User]` - List of matching users (may be empty)

**Raises:**
- `MattermostError` - If the API request fails

**Example:**

```python
users = await client.users.search("john")
for user in users:
    print(f"{user.username}: {user.first_name} {user.last_name}")
```

---

#### `get_by_username()`

Get a user by username.

```python
async def get_by_username(username: str) -> User | None
```

**Parameters:**
- `username` (`str`) - The username (with or without `@` prefix)

**Returns:** `User | None` - User object if found, `None` if user doesn't exist

**Raises:**
- `MattermostValidationError` - If `username` is empty
- `MattermostError` - If the API request fails (except 404)

**Example:**

```python
user = await client.users.get_by_username("john.doe")
if user:
    print(f"Found user: {user.id}")
else:
    print("User not found")
```

---

#### `get_by_email()`

Get a user by email address.

```python
async def get_by_email(email: str) -> User | None
```

**Parameters:**
- `email` (`str`) - The user's email address

**Returns:** `User | None` - User object if found, `None` if user doesn't exist

**Raises:**
- `MattermostValidationError` - If `email` is empty
- `MattermostError` - If the API request fails (except 404)

**Example:**

```python
user = await client.users.get_by_email("john.doe@example.com")
if user:
    print(f"Found user: {user.username}")
```

---

#### `get_status()`

Get a user's current status.

```python
async def get_status(user_id: str) -> dict[str, Any]
```

**Parameters:**
- `user_id` (`str`) - The ID of the user

**Returns:** `dict[str, Any]` - Status object with keys:
  - `status` (`str`) - One of: `"online"`, `"offline"`, `"away"`, `"dnd"`
  - `manual` (`bool`) - Whether status was manually set
  - `last_activity_at` (`int`) - Unix timestamp of last activity

**Raises:**
- `MattermostValidationError` - If `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
status = await client.users.get_status(user_id)
print(f"Status: {status['status']}")
```

---

#### `update()`

Update a user's fields.

```python
async def update(user_id: str, **fields: Any) -> User
```

**Parameters:**
- `user_id` (`str`) - The ID of the user to update
- `**fields` (`Any`) - Fields to update (e.g., `first_name`, `last_name`, `nickname`, `position`)

**Returns:** `User` - The updated user object

**Raises:**
- `MattermostValidationError` - If `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
updated_user = await client.users.update(
    user_id,
    first_name="John",
    last_name="Doe",
    nickname="Johnny"
)
```

---

## TeamsAPI

High-level API for managing Mattermost teams and team members. Access via `client.teams`.

### Methods

#### `search()`

Search for teams by term (team name or display name).

```python
async def search(term: str) -> list[Team]
```

**Parameters:**
- `term` (`str`) - The search term

**Returns:** `list[Team]` - List of matching teams (may be empty)

**Raises:**
- `MattermostError` - If the API request fails

**Example:**

```python
teams = await client.teams.search("dev")
for team in teams:
    print(f"{team.name}: {team.display_name}")
```

---

#### `get_by_id()`

Get a team by ID.

```python
async def get_by_id(team_id: str) -> Team
```

**Parameters:**
- `team_id` (`str`) - The ID of the team to retrieve

**Returns:** `Team` - The team object

**Raises:**
- `MattermostValidationError` - If `team_id` is empty
- `MattermostNotFoundError` - If team doesn't exist
- `MattermostError` - If the API request fails

**Example:**

```python
team = await client.teams.get_by_id("abc123xyz")
print(f"Team: {team.display_name}")
```

---

#### `get_by_name()`

Get a team by name (URL-safe identifier).

```python
async def get_by_name(name: str) -> Team | None
```

**Parameters:**
- `name` (`str`) - The team name (not `display_name`)

**Returns:** `Team | None` - Team object if found, `None` if team doesn't exist

**Raises:**
- `MattermostValidationError` - If `name` is empty
- `MattermostError` - If the API request fails (except 404)

**Example:**

```python
team = await client.teams.get_by_name("developers")
if team:
    print(f"Found team: {team.display_name}")
```

---

#### `get_all()`

Get all teams (paginated).

```python
async def get_all(
    page: int = 0,
    per_page: int = 60
) -> list[Team]
```

**Parameters:**
- `page` (`int`) - Page number (0-indexed). Default: `0`
- `per_page` (`int`) - Number of teams per page (max 200). Default: `60`

**Returns:** `list[Team]` - List of teams

**Raises:**
- `MattermostError` - If the API request fails

**Example:**

```python
# Get first page
teams = await client.teams.get_all()

# Get second page with 100 teams per page
teams = await client.teams.get_all(page=1, per_page=100)
```

---

#### `create()`

Create a new team.

```python
async def create(
    name: str,
    display_name: str,
    team_type: str = "O"
) -> Team
```

**Parameters:**
- `name` (`str`) - Unique team name (URL-safe identifier, lowercase, no spaces)
- `display_name` (`str`) - Display name shown in UI
- `team_type` (`str`) - Team type: `"O"` for open, `"I"` for invite-only. Default: `"O"`

**Returns:** `Team` - The created team object

**Raises:**
- `MattermostValidationError` - If `name` or `display_name` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
team = await client.teams.create(
    name="engineering",
    display_name="Engineering Team",
    team_type="O"
)
print(f"Created team: {team.id}")
```

---

#### `get_member()`

Get a team member by team ID and user ID.

```python
async def get_member(team_id: str, user_id: str) -> TeamMember
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `user_id` (`str`) - The ID of the user

**Returns:** `TeamMember` - The team member object

**Raises:**
- `MattermostValidationError` - If `team_id` or `user_id` is empty
- `MattermostNotFoundError` - If member doesn't exist
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.teams.get_member(team_id, user_id)
print(f"Roles: {member.roles}")
print(f"Admin: {member.scheme_admin}")
```

---

#### `get_members()`

Get team members (paginated).

```python
async def get_members(
    team_id: str,
    page: int = 0,
    per_page: int = 60
) -> list[TeamMember]
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `page` (`int`) - Page number (0-indexed). Default: `0`
- `per_page` (`int`) - Number of members per page (max 200). Default: `60`

**Returns:** `list[TeamMember]` - List of team members

**Raises:**
- `MattermostValidationError` - If `team_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
members = await client.teams.get_members(team_id)
for member in members:
    print(f"User: {member.user_id}, Admin: {member.scheme_admin}")
```

---

#### `add_member()`

Add a user to a team.

```python
async def add_member(team_id: str, user_id: str) -> TeamMember
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `user_id` (`str`) - The ID of the user to add

**Returns:** `TeamMember` - The created team member object

**Raises:**
- `MattermostValidationError` - If `team_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.teams.add_member(team_id, user_id)
print(f"Added user {member.user_id} to team {member.team_id}")
```

---

#### `remove_member()`

Remove a user from a team.

```python
async def remove_member(team_id: str, user_id: str) -> dict
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `user_id` (`str`) - The ID of the user to remove

**Returns:** `dict` - Empty dict on success

**Raises:**
- `MattermostValidationError` - If `team_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
await client.teams.remove_member(team_id, user_id)
```

---

#### `set_admin()`

Grant team admin role to a user.

```python
async def set_admin(team_id: str, user_id: str) -> TeamMember
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `user_id` (`str`) - The ID of the user

**Returns:** `TeamMember` - The updated team member object

**Raises:**
- `MattermostValidationError` - If `team_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.teams.set_admin(team_id, user_id)
print(f"Admin status: {member.scheme_admin}")
```

---

#### `remove_admin()`

Remove team admin role from a user (user remains a team member).

```python
async def remove_admin(team_id: str, user_id: str) -> TeamMember
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `user_id` (`str`) - The ID of the user

**Returns:** `TeamMember` - The updated team member object

**Raises:**
- `MattermostValidationError` - If `team_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.teams.remove_admin(team_id, user_id)
print(f"Admin status: {member.scheme_admin}")  # Should be False
```

---

## ChannelsAPI

High-level API for managing Mattermost channels and channel members. Access via `client.channels`.

### Methods

#### `get_by_team()`

Get all channels for a team.

```python
async def get_by_team(team_id: str) -> list[Channel]
```

**Parameters:**
- `team_id` (`str`) - The ID of the team

**Returns:** `list[Channel]` - List of channels in the team

**Raises:**
- `MattermostValidationError` - If `team_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
channels = await client.channels.get_by_team(team_id)
for channel in channels:
    print(f"{channel.name}: {channel.display_name}")
```

---

#### `list_channels()`

List all channels including private ones (requires System Admin).

```python
async def list_channels(
    team_id: str | None = None,
    page: int = 0,
    per_page: int = 100,
    include_deleted: bool = False,
) -> list[Channel]
```

**Parameters:**
- `team_id` (`str | None`) - Optional team ID to filter channels. Default: `None`
- `page` (`int`) - Page number (0-indexed). Default: `0`
- `per_page` (`int`) - Results per page (max 200). Default: `100`
- `include_deleted` (`bool`) - Whether to include deleted channels. Default: `False`

**Returns:** `list[Channel]` - List of channels

**Raises:**
- `MattermostForbiddenError` - If user lacks `manage_system` permission
- `MattermostError` - If the API request fails

**Note:** This method requires `manage_system` permission (System Admin). Unlike `get_by_team()`, it can return private channels where the bot is not a member.

**Example:**

```python
# List all channels (System Admin only)
all_channels = await client.channels.list_channels()

# List channels for a specific team
team_channels = await client.channels.list_channels(team_id="abc123")

# With pagination
channels = await client.channels.list_channels(page=0, per_page=50)

# Include deleted channels
channels = await client.channels.list_channels(include_deleted=True)
```

---

#### `get_by_id()`

Get a channel by ID.

```python
async def get_by_id(channel_id: str) -> Channel
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel to retrieve

**Returns:** `Channel` - The channel object

**Raises:**
- `MattermostValidationError` - If `channel_id` is empty
- `MattermostNotFoundError` - If channel doesn't exist
- `MattermostError` - If the API request fails

**Example:**

```python
channel = await client.channels.get_by_id("abc123xyz")
print(f"Channel: {channel.display_name} (Type: {channel.type})")
```

---

#### `get_by_name()`

Get a channel by name within a team.

```python
async def get_by_name(team_id: str, name: str) -> Channel | None
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `name` (`str`) - The channel name (URL-safe identifier, not `display_name`)

**Returns:** `Channel | None` - Channel object if found, `None` if channel doesn't exist

**Raises:**
- `MattermostValidationError` - If `team_id` or `name` is empty
- `MattermostError` - If the API request fails (except 404)

**Example:**

```python
channel = await client.channels.get_by_name(team_id, "general")
if channel:
    print(f"Found channel: {channel.display_name}")
```

---

#### `search()`

Search for channels in a team.

```python
async def search(team_id: str, term: str) -> list[Channel]
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `term` (`str`) - The search term (channel name or display name)

**Returns:** `list[Channel]` - List of matching channels (may be empty)

**Raises:**
- `MattermostValidationError` - If `team_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
channels = await client.channels.search(team_id, "engineering")
for channel in channels:
    print(f"{channel.name}: {channel.display_name}")
```

---

#### `create()`

Create a new channel.

```python
async def create(
    team_id: str,
    name: str,
    display_name: str,
    channel_type: str = "O",
    purpose: str = "",
    header: str = "",
) -> Channel
```

**Parameters:**
- `team_id` (`str`) - The ID of the team
- `name` (`str`) - Unique channel name (URL-safe identifier, lowercase, no spaces)
- `display_name` (`str`) - Display name shown in UI
- `channel_type` (`str`) - Channel type: `"O"` for public, `"P"` for private. Default: `"O"`
- `purpose` (`str`) - Channel purpose (optional). Default: `""`
- `header` (`str`) - Channel header (optional). Default: `""`

**Returns:** `Channel` - The created channel object

**Raises:**
- `MattermostValidationError` - If `team_id`, `name`, or `display_name` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
channel = await client.channels.create(
    team_id=team_id,
    name="project-alpha",
    display_name="Project Alpha",
    channel_type="P",
    purpose="Discussion for Project Alpha",
    header="Project Alpha | Status: Active"
)
print(f"Created channel: {channel.id}")
```

---

#### `create_direct()`

Create a direct message channel between users.

```python
async def create_direct(user_ids: list[str]) -> Channel
```

**Parameters:**
- `user_ids` (`list[str]`) - List of user IDs (must contain at least 2 users)

**Returns:** `Channel` - The created direct channel object (type will be `"D"` for DM or `"G"` for group)

**Raises:**
- `MattermostValidationError` - If `user_ids` has fewer than 2 users or contains empty IDs
- `MattermostError` - If the API request fails

**Example:**

```python
# Create direct message between two users
dm_channel = await client.channels.create_direct([user1_id, user2_id])

# Create group message with multiple users
group_channel = await client.channels.create_direct([user1_id, user2_id, user3_id])
```

---

#### `delete()`

Delete a channel.

```python
async def delete(channel_id: str) -> dict
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel to delete

**Returns:** `dict` - Status response

**Raises:**
- `MattermostValidationError` - If `channel_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
await client.channels.delete(channel_id)
```

---

#### `get_member()`

Get a channel member by channel ID and user ID.

```python
async def get_member(channel_id: str, user_id: str) -> ChannelMember
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel
- `user_id` (`str`) - The ID of the user

**Returns:** `ChannelMember` - The channel member object

**Raises:**
- `MattermostValidationError` - If `channel_id` or `user_id` is empty
- `MattermostNotFoundError` - If member doesn't exist
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.channels.get_member(channel_id, user_id)
print(f"Roles: {member.roles}")
print(f"Admin: {member.scheme_admin}")
```

---

#### `get_members()`

Get channel members (paginated).

```python
async def get_members(
    channel_id: str,
    page: int = 0,
    per_page: int = 60
) -> list[ChannelMember]
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel
- `page` (`int`) - Page number (0-indexed). Default: `0`
- `per_page` (`int`) - Number of members per page (max 200). Default: `60`

**Returns:** `list[ChannelMember]` - List of channel members

**Raises:**
- `MattermostValidationError` - If `channel_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
members = await client.channels.get_members(channel_id)
for member in members:
    print(f"User: {member.user_id}, Admin: {member.scheme_admin}")
```

---

#### `add_member()`

Add a user to a channel.

```python
async def add_member(channel_id: str, user_id: str) -> ChannelMember
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel
- `user_id` (`str`) - The ID of the user to add

**Returns:** `ChannelMember` - The created channel member object

**Raises:**
- `MattermostValidationError` - If `channel_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.channels.add_member(channel_id, user_id)
print(f"Added user {member.user_id} to channel {member.channel_id}")
```

---

#### `remove_member()`

Remove a user from a channel.

```python
async def remove_member(channel_id: str, user_id: str) -> dict
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel
- `user_id` (`str`) - The ID of the user to remove

**Returns:** `dict` - Empty dict on success

**Raises:**
- `MattermostValidationError` - If `channel_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
await client.channels.remove_member(channel_id, user_id)
```

---

#### `set_admin()`

Grant channel admin role to a user.

```python
async def set_admin(channel_id: str, user_id: str) -> ChannelMember
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel
- `user_id` (`str`) - The ID of the user

**Returns:** `ChannelMember` - The updated channel member object

**Raises:**
- `MattermostValidationError` - If `channel_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.channels.set_admin(channel_id, user_id)
print(f"Admin status: {member.scheme_admin}")
```

---

#### `remove_admin()`

Remove channel admin role from a user (user remains a channel member).

```python
async def remove_admin(channel_id: str, user_id: str) -> ChannelMember
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel
- `user_id` (`str`) - The ID of the user

**Returns:** `ChannelMember` - The updated channel member object

**Raises:**
- `MattermostValidationError` - If `channel_id` or `user_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
member = await client.channels.remove_admin(channel_id, user_id)
print(f"Admin status: {member.scheme_admin}")  # Should be False
```

---

## PostsAPI

High-level API for managing Mattermost posts (messages). Access via `client.posts`.

### Methods

#### `create()`

Create a new post in a channel.

```python
async def create(
    channel_id: str,
    message: str,
    root_id: str | None = None
) -> Post
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel to post in
- `message` (`str`) - The message content to post
- `root_id` (`str | None`) - Optional ID of the root post for threading. Default: `None`

**Returns:** `Post` - The created post object

**Raises:**
- `MattermostValidationError` - If `channel_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
# Create a regular post
post = await client.posts.create(channel_id, "Hello, world!")

# Create a threaded reply
reply = await client.posts.create(
    channel_id,
    "This is a reply",
    root_id=original_post_id
)
```

---

#### `get_by_id()`

Get a post by ID.

```python
async def get_by_id(post_id: str) -> Post
```

**Parameters:**
- `post_id` (`str`) - The ID of the post to retrieve

**Returns:** `Post` - The post object

**Raises:**
- `MattermostValidationError` - If `post_id` is empty
- `MattermostNotFoundError` - If post doesn't exist
- `MattermostError` - If the API request fails

**Example:**

```python
post = await client.posts.get_by_id("abc123xyz")
print(f"Message: {post.message}")
print(f"Author: {post.user_id}")
```

---

#### `get_for_channel()`

Get posts for a channel (paginated, newest first).

```python
async def get_for_channel(
    channel_id: str,
    page: int = 0,
    per_page: int = 60
) -> list[Post]
```

**Parameters:**
- `channel_id` (`str`) - The ID of the channel
- `page` (`int`) - Page number (0-indexed). Default: `0`
- `per_page` (`int`) - Number of posts per page (max 200). Default: `60`

**Returns:** `list[Post]` - List of posts in the channel (newest first)

**Raises:**
- `MattermostValidationError` - If `channel_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
posts = await client.posts.get_for_channel(channel_id)
for post in posts:
    print(f"{post.user_id}: {post.message}")
```

---

#### `get_thread()`

Get all posts in a thread.

```python
async def get_thread(post_id: str) -> list[Post]
```

**Parameters:**
- `post_id` (`str`) - The ID of the root post

**Returns:** `list[Post]` - List of posts in the thread (including the root post)

**Raises:**
- `MattermostValidationError` - If `post_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
thread = await client.posts.get_thread(root_post_id)
print(f"Thread has {len(thread)} posts")
for post in thread:
    print(f"  {post.user_id}: {post.message}")
```

---

#### `search()`

Search for posts in a team.

```python
async def search(team_id: str, terms: str) -> list[Post]
```

**Parameters:**
- `team_id` (`str`) - The ID of the team to search in
- `terms` (`str`) - The search terms (supports Mattermost search syntax)

**Returns:** `list[Post]` - List of matching posts

**Raises:**
- `MattermostValidationError` - If `team_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
# Simple search
posts = await client.posts.search(team_id, "project alpha")

# Advanced search with operators
posts = await client.posts.search(team_id, "from:john urgent")
```

---

#### `update()`

Update a post's message content.

```python
async def update(post_id: str, message: str) -> Post
```

**Parameters:**
- `post_id` (`str`) - The ID of the post to update
- `message` (`str`) - The new message content

**Returns:** `Post` - The updated post object

**Raises:**
- `MattermostValidationError` - If `post_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
updated_post = await client.posts.update(
    post_id,
    "Updated message content"
)
```

---

#### `delete()`

Delete a post.

```python
async def delete(post_id: str) -> dict
```

**Parameters:**
- `post_id` (`str`) - The ID of the post to delete

**Returns:** `dict` - Status response

**Raises:**
- `MattermostValidationError` - If `post_id` is empty
- `MattermostError` - If the API request fails

**Example:**

```python
await client.posts.delete(post_id)
```

---

## Models

Pydantic models for type-safe API responses. All models use `ConfigDict(extra="ignore")` to ignore unknown fields from the API.

### User

Represents a Mattermost user.

```python
class User(BaseModel):
    id: str
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    nickname: str | None = None
    position: str | None = None
    roles: str | None = None
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique user ID |
| `username` | `str` | Yes | Username (unique, no spaces) |
| `email` | `str \| None` | No | Email address |
| `first_name` | `str \| None` | No | First name |
| `last_name` | `str \| None` | No | Last name |
| `nickname` | `str \| None` | No | Nickname |
| `position` | `str \| None` | No | Job position/title |
| `roles` | `str \| None` | No | Space-separated roles (e.g., `"system_user system_admin"`) |

---

### Team

Represents a Mattermost team.

```python
class Team(BaseModel):
    id: str
    name: str
    display_name: str
    type: str  # "O" (open) | "I" (invite-only)
    description: str | None = None
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique team ID |
| `name` | `str` | Yes | Team name (URL-safe identifier) |
| `display_name` | `str` | Yes | Display name shown in UI |
| `type` | `str` | Yes | Team type: `"O"` (open) or `"I"` (invite-only) |
| `description` | `str \| None` | No | Team description |

---

### Channel

Represents a Mattermost channel.

```python
class Channel(BaseModel):
    id: str
    team_id: str
    name: str
    display_name: str
    type: str  # "O" (public) | "P" (private) | "D" (direct) | "G" (group)
    header: str | None = None
    purpose: str | None = None
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique channel ID |
| `team_id` | `str` | Yes | Parent team ID |
| `name` | `str` | Yes | Channel name (URL-safe identifier) |
| `display_name` | `str` | Yes | Display name shown in UI |
| `type` | `str` | Yes | Channel type: `"O"` (public), `"P"` (private), `"D"` (direct), `"G"` (group) |
| `header` | `str \| None` | No | Channel header text |
| `purpose` | `str \| None` | No | Channel purpose/description |

---

### Post

Represents a Mattermost post (message).

```python
class Post(BaseModel):
    id: str
    channel_id: str
    user_id: str
    message: str
    root_id: str | None = None
    create_at: int | None = None
    update_at: int | None = None
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique post ID |
| `channel_id` | `str` | Yes | Parent channel ID |
| `user_id` | `str` | Yes | Author user ID |
| `message` | `str` | Yes | Message content |
| `root_id` | `str \| None` | No | Root post ID (for threaded replies) |
| `create_at` | `int \| None` | No | Creation timestamp (Unix milliseconds) |
| `update_at` | `int \| None` | No | Last update timestamp (Unix milliseconds) |

---

### TeamMember

Represents a user's membership in a team.

```python
class TeamMember(BaseModel):
    team_id: str
    user_id: str
    roles: str
    delete_at: int | None = None
    scheme_admin: bool | None = None
    scheme_user: bool | None = None
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `team_id` | `str` | Yes | Team ID |
| `user_id` | `str` | Yes | User ID |
| `roles` | `str` | Yes | Space-separated roles |
| `delete_at` | `int \| None` | No | Deletion timestamp (Unix milliseconds), `0` if not deleted |
| `scheme_admin` | `bool \| None` | No | Whether user is a team admin |
| `scheme_user` | `bool \| None` | No | Whether user is a team member |

---

### ChannelMember

Represents a user's membership in a channel.

```python
class ChannelMember(BaseModel):
    channel_id: str
    user_id: str
    roles: str
    scheme_admin: bool | None = None
    scheme_user: bool | None = None
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel_id` | `str` | Yes | Channel ID |
| `user_id` | `str` | Yes | User ID |
| `roles` | `str` | Yes | Space-separated roles |
| `scheme_admin` | `bool \| None` | No | Whether user is a channel admin |
| `scheme_user` | `bool \| None` | No | Whether user is a channel member |

---

## Exceptions

Hierarchical exception system for different error types. All exceptions inherit from `MattermostError`.

### Exception Hierarchy

```
MattermostError (base)
├── MattermostAuthError (401)
├── MattermostForbiddenError (403)
├── MattermostNotFoundError (404)
├── MattermostRateLimitError (429)
├── MattermostServerError (5xx)
└── MattermostConnectionError (connection/timeout)

MattermostValidationError (inherits from ValueError, not MattermostError)
```

---

### MattermostError

Base exception for all Mattermost API errors.

```python
class MattermostError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    )
```

**Attributes:**
- `message` (`str`) - Error message
- `status_code` (`int | None`) - HTTP status code (if applicable)
- `response_body` (`dict[str, Any] | None`) - Full response body from API

**Example:**

```python
try:
    await client.get("/invalid/endpoint")
except MattermostError as e:
    print(f"Error: {e}")
    print(f"Status: {e.status_code}")
    print(f"Response: {e.response_body}")
```

---

### MattermostAuthError

Authentication failed (HTTP 401).

**Common causes:**
- Invalid or expired token
- Missing authentication header
- Token for different server

**Example:**

```python
try:
    await client.connect()
except MattermostAuthError as e:
    print(f"Authentication failed: {e}")
    # Status code will be 401
```

---

### MattermostForbiddenError

Permission denied (HTTP 403).

**Common causes:**
- Insufficient permissions for the operation
- Token doesn't have required scope
- User not member of team/channel

**Example:**

```python
try:
    await client.teams.set_admin(team_id, user_id)
except MattermostForbiddenError as e:
    print(f"Permission denied: {e}")
    # Status code will be 403
```

---

### MattermostNotFoundError

Resource not found (HTTP 404).

**Common causes:**
- Resource doesn't exist
- Invalid ID
- User doesn't have access to resource

**Example:**

```python
try:
    user = await client.users.get_by_id("invalid_id")
except MattermostNotFoundError as e:
    print(f"User not found: {e}")
    # Status code will be 404
```

---

### MattermostRateLimitError

Rate limit exceeded (HTTP 429).

```python
class MattermostRateLimitError(MattermostError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
        retry_after: float | None = None,
    )
```

**Additional Attributes:**
- `retry_after` (`float | None`) - Seconds to wait before retrying (from `Retry-After` header)

**Common causes:**
- Too many requests in a short time
- Exceeded API rate limits

**Example:**

```python
try:
    for i in range(1000):
        await client.users.get_me()
except MattermostRateLimitError as e:
    print(f"Rate limited: {e}")
    if e.retry_after:
        print(f"Retry after {e.retry_after} seconds")
    # Status code will be 429
```

---

### MattermostServerError

Server error (HTTP 5xx).

**Common status codes:**
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable
- `504` - Gateway Timeout

**Example:**

```python
try:
    await client.get("/some/endpoint")
except MattermostServerError as e:
    print(f"Server error: {e}")
    print(f"Status: {e.status_code}")
    # Status code will be 500-599
```

---

### MattermostConnectionError

Connection or timeout error (not HTTP-related).

**Common causes:**
- Network connection failed
- Server unreachable
- Timeout exceeded
- DNS resolution failed

**Example:**

```python
try:
    client = AsyncMattermostClient(
        url="https://invalid-server.example.com",
        token="token"
    )
    await client.connect()
except MattermostConnectionError as e:
    print(f"Connection failed: {e}")
```

---

### MattermostValidationError

Invalid parameter value (raised before API call).

**Inherits from:** `ValueError` (not `MattermostError`)

**Common causes:**
- Empty required parameter
- Invalid format
- Out-of-range value

**Example:**

```python
try:
    await client.users.get_by_id("")  # Empty user_id
except MattermostValidationError as e:
    print(f"Validation error: {e}")
    # Message: "user_id cannot be empty"
```

---

## Retry Logic

The client implements automatic retry with exponential backoff for certain operations.

### Retry Behavior

**Methods with retry:**
- `GET` requests - Safe to retry (idempotent)
- `DELETE` requests - Safe to retry (idempotent)

**Methods without retry:**
- `POST` requests - Not retried to avoid duplicate creates
- `PUT` requests - Not retried to avoid duplicate updates

**Retryable errors:**
- `MattermostServerError` with status codes: `500`, `502`, `503`, `504`
- `MattermostRateLimitError` (429)
- `MattermostConnectionError` (connection/timeout issues)

**Non-retryable errors:**
- `MattermostAuthError` (401) - Fix authentication and retry manually
- `MattermostForbiddenError` (403) - Fix permissions and retry manually
- `MattermostNotFoundError` (404) - Resource doesn't exist, retrying won't help
- `MattermostValidationError` - Fix parameters and retry manually

---

### Retry Configuration

The retry decorator (`@with_retry`) accepts the following parameters:

```python
@with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_attempts` | `int` | `3` | Maximum number of retry attempts (including the first attempt) |
| `base_delay` | `float` | `1.0` | Initial delay in seconds before first retry |
| `max_delay` | `float` | `30.0` | Maximum delay between retries (cap for exponential backoff) |
| `exponential_base` | `float` | `2.0` | Base for exponential backoff calculation |

---

### Backoff Strategy

The retry logic uses **exponential backoff with jitter**:

1. **Delay calculation:**
   ```
   delay = min(base_delay * (exponential_base ^ (attempt - 1)), max_delay)
   ```

2. **Jitter addition:**
   ```
   jitter = random(0, delay * 0.1)
   sleep_time = delay + jitter
   ```

3. **Example delays** (with default settings):
   - Attempt 1: `1.0s + jitter` (0-0.1s)
   - Attempt 2: `2.0s + jitter` (0-0.2s)
   - Attempt 3: `4.0s + jitter` (0-0.4s)

---

### Rate Limit Handling

For `MattermostRateLimitError` (429), the retry logic honors the `Retry-After` header if present:

```python
if retry_after_header:
    sleep_time = min(retry_after, max_delay)
    await asyncio.sleep(sleep_time)
```

This ensures compliance with the server's rate limit policy.

---

### Usage Example

```python
# Automatic retry for GET requests
try:
    # Will retry up to 3 times on connection errors or 5xx
    user = await client.get("/users/me")
except MattermostError as e:
    # Failed after 3 attempts
    print(f"Failed: {e}")

# POST requests do NOT retry
try:
    # Will fail immediately on connection error (no retry)
    post = await client.post("/posts", json={"channel_id": "...", "message": "..."})
except MattermostConnectionError as e:
    # No automatic retry - handle manually
    print(f"Connection failed: {e}")
```

---

### Manual Retry

For operations that don't automatically retry (POST, PUT), you can implement manual retry:

```python
import asyncio
from mm_async import MattermostConnectionError, MattermostServerError

async def create_post_with_retry(client, channel_id, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.posts.create(channel_id, message)
        except (MattermostConnectionError, MattermostServerError) as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

# Usage
post = await create_post_with_retry(client, channel_id, "Hello!")
```

---

## Complete Usage Example

Here's a comprehensive example demonstrating all major API features:

```python
import asyncio
from mm_async import (
    AsyncMattermostClient,
    MattermostAuthError,
    MattermostNotFoundError,
)


async def main():
    # Initialize client
    client = AsyncMattermostClient(
        url="https://mattermost.example.com",
        token="your-bot-token",
        verify_ssl=True,
        timeout=30.0,
    )

    try:
        # Connect and authenticate
        await client.connect()
        print(f"Connected as user: {client.bot_user_id}")

        # --- Users API ---
        me = await client.users.get_me()
        print(f"My username: {me.username}")

        users = await client.users.search("john")
        for user in users:
            print(f"Found: {user.username} ({user.email})")

        # --- Teams API ---
        teams = await client.teams.search("engineering")
        if teams:
            team = teams[0]
            print(f"Team: {team.display_name}")

            # Get team members
            members = await client.teams.get_members(team.id)
            print(f"Members: {len(members)}")

            # Add user to team
            user = await client.users.get_by_username("alice")
            if user:
                await client.teams.add_member(team.id, user.id)
                print(f"Added {user.username} to {team.name}")

        # --- Channels API ---
        channels = await client.channels.search(team.id, "general")
        if channels:
            channel = channels[0]
            print(f"Channel: {channel.display_name}")

            # Add user to channel
            if user:
                await client.channels.add_member(channel.id, user.id)
                print(f"Added {user.username} to {channel.name}")

            # --- Posts API ---
            post = await client.posts.create(
                channel.id,
                "Hello from mm-async!"
            )
            print(f"Created post: {post.id}")

            # Create threaded reply
            reply = await client.posts.create(
                channel.id,
                "This is a reply",
                root_id=post.id
            )
            print(f"Created reply: {reply.id}")

            # Get channel posts
            posts = await client.posts.get_for_channel(channel.id, per_page=10)
            for p in posts:
                print(f"  {p.user_id}: {p.message[:50]}")

    except MattermostAuthError as e:
        print(f"Authentication failed: {e}")
    except MattermostNotFoundError as e:
        print(f"Resource not found: {e}")
    finally:
        # Clean up
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Advanced Patterns

### Pagination

For APIs that support pagination, use a loop to fetch all results:

```python
async def get_all_team_members(client, team_id):
    """Fetch all team members across all pages."""
    all_members = []
    page = 0
    per_page = 100

    while True:
        members = await client.teams.get_members(
            team_id,
            page=page,
            per_page=per_page
        )
        if not members:
            break
        all_members.extend(members)
        page += 1

    return all_members
```

---

### Error Handling

Use specific exception types for precise error handling:

```python
from mm_async import (
    MattermostAuthError,
    MattermostForbiddenError,
    MattermostNotFoundError,
    MattermostValidationError,
)

async def safe_get_user(client, username):
    """Get user by username with comprehensive error handling."""
    try:
        user = await client.users.get_by_username(username)
        if user:
            return user
        else:
            print(f"User '{username}' not found")
            return None
    except MattermostValidationError as e:
        print(f"Invalid username format: {e}")
    except MattermostAuthError as e:
        print(f"Authentication failed: {e}")
    except MattermostForbiddenError as e:
        print(f"Permission denied: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None
```

---

### Batch Operations

Process multiple items efficiently:

```python
async def add_users_to_team(client, team_id, usernames):
    """Add multiple users to a team."""
    for username in usernames:
        user = await client.users.get_by_username(username)
        if user:
            try:
                await client.teams.add_member(team_id, user.id)
                print(f"Added {username}")
            except Exception as e:
                print(f"Failed to add {username}: {e}")
        else:
            print(f"User {username} not found")
```

---

### Context Manager Best Practices

Always use async context manager for automatic cleanup:

```python
async def send_notification(url, token, channel_id, message):
    """Send a notification and ensure cleanup."""
    async with AsyncMattermostClient(url=url, token=token) as client:
        await client.posts.create(channel_id, message)
        # Client automatically closed on exit
```

---

## Migration from v0.2.x

If upgrading from v0.2.x, note these changes:

1. **Pydantic models:** All API methods now return Pydantic models instead of raw dicts
2. **Validation:** Empty parameters now raise `MattermostValidationError` before making API calls
3. **Type hints:** Full type hints throughout for better IDE support
4. **Retry logic:** Retry behavior is now documented and consistent

**Migration example:**

```python
# v0.2.x
user = await client.get("/users/me")
username = user["username"]  # Dict access

# v0.3.0
user = await client.users.get_me()
username = user.username  # Attribute access (Pydantic model)
```

---

## Support and Contribution

For issues, questions, or contributions, please visit the project repository.

**Version:** 0.3.3
**License:** MIT
**Python:** >= 3.11
**Dependencies:** httpx >= 0.28.0, pydantic >= 2.0.0
