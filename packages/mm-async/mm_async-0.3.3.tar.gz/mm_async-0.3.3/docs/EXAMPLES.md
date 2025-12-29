# mm-async Client Examples

Practical examples for using the mm-async Mattermost API client (v0.3.0).

## Table of Contents

- [Basic Usage](#basic-usage)
- [User Operations](#user-operations)
- [Team Management](#team-management)
- [Channel Operations](#channel-operations)
- [Messaging](#messaging)
- [Error Handling](#error-handling)
- [Advanced Patterns](#advanced-patterns)

---

## Basic Usage

### Creating and Configuring Client

```python
from mm_async import AsyncMattermostClient

# Basic client configuration
client = AsyncMattermostClient(
    url="https://mattermost.example.com",
    token="your-bot-token",
)

# With custom timeouts and SSL settings
client = AsyncMattermostClient(
    url="https://mattermost.example.com:8065",
    token="your-bot-token",
    verify_ssl=True,  # Verify SSL certificates (default: True)
    timeout=30.0,     # Request timeout in seconds
    connect_timeout=10.0,  # Connection timeout in seconds
)
```

### Using Async Context Manager

```python
import asyncio
from mm_async import AsyncMattermostClient

async def main():
    # Recommended: use context manager for automatic cleanup
    async with AsyncMattermostClient(
        url="https://mattermost.example.com",
        token="your-bot-token",
    ) as client:
        # Client is automatically connected
        me = await client.users.get_me()
        print(f"Connected as: {me.username}")
        # Client is automatically closed when exiting the context

# Run the async function
asyncio.run(main())
```

### Manual Connection Management

```python
async def main():
    client = AsyncMattermostClient(
        url="https://mattermost.example.com",
        token="your-bot-token",
    )

    # Explicitly connect
    await client.connect()

    try:
        # Use the client
        me = await client.users.get_me()
        print(f"Bot User ID: {me.id}")
    finally:
        # Always close when done
        await client.close()
```

### Getting Current Authenticated User

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Get the bot/user account information
    me = await client.users.get_me()

    print(f"Username: {me.username}")
    print(f"Email: {me.email}")
    print(f"First Name: {me.first_name}")
    print(f"Last Name: {me.last_name}")
    print(f"Roles: {me.roles}")

    # Access the cached bot user ID
    bot_id = client.bot_user_id
    print(f"Cached Bot ID: {bot_id}")
```

---

## User Operations

### Search Users by Term

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Search by username, email, or name
    users = await client.users.search("john")

    for user in users:
        print(f"Found: {user.username} ({user.email})")
```

### Get User by Username (with @ handling)

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Works with or without @ prefix
    user = await client.users.get_by_username("@johndoe")

    if user:
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Display Name: {user.first_name} {user.last_name}")
    else:
        print("User not found")
```

### Get User by Email

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    user = await client.users.get_by_email("john.doe@example.com")

    if user:
        print(f"Found user: {user.username}")
        print(f"Nickname: {user.nickname}")
    else:
        print("No user with that email")
```

### Get User by ID

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    user_id = "abc123def456"
    user = await client.users.get_by_id(user_id)

    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
```

### Check User Online Status

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    user_id = "abc123def456"
    status = await client.users.get_status(user_id)

    print(f"Status: {status['status']}")  # "online", "offline", "away", "dnd"
    print(f"Manual: {status['manual']}")  # True if manually set
    print(f"Last Activity: {status.get('last_activity_at', 'N/A')}")
```

### Update User Fields

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    user_id = "abc123def456"

    # Update one or more fields
    updated_user = await client.users.update(
        user_id,
        first_name="Jane",
        last_name="Smith",
        nickname="jsmith",
    )

    print(f"Updated: {updated_user.first_name} {updated_user.last_name}")
```

---

## Team Management

### List All Teams with Pagination

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Get first page (default: page 0, 60 teams per page)
    teams = await client.teams.get_all(page=0, per_page=60)

    for team in teams:
        print(f"Team: {team.display_name} ({team.name})")
        print(f"  Type: {'Open' if team.type == 'O' else 'Invite-only'}")
        print(f"  ID: {team.id}")

    # Get next page
    next_teams = await client.teams.get_all(page=1, per_page=60)
```

### Search Teams

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Search by team name or display name
    teams = await client.teams.search("engineering")

    for team in teams:
        print(f"Found: {team.display_name}")
```

### Get Team by Name

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Get team by URL-safe name (not display_name)
    team = await client.teams.get_by_name("engineering-team")

    if team:
        print(f"Team Display Name: {team.display_name}")
        print(f"Team ID: {team.id}")
    else:
        print("Team not found")
```

### Create New Team

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Create an open team
    new_team = await client.teams.create(
        name="dev-team",  # URL-safe identifier
        display_name="Development Team",
        team_type="O",  # "O" for open, "I" for invite-only
    )

    print(f"Created team: {new_team.display_name}")
    print(f"Team ID: {new_team.id}")
```

### Add Team Member

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"
    user_id = "user_def456"

    member = await client.teams.add_member(team_id, user_id)

    print(f"Added user {member.user_id} to team {member.team_id}")
    print(f"Roles: {member.roles}")
```

### Remove Team Member

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"
    user_id = "user_def456"

    result = await client.teams.remove_member(team_id, user_id)
    print("User removed from team")
```

### Grant Team Admin Role

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"
    user_id = "user_def456"

    # Make user a team admin
    member = await client.teams.set_admin(team_id, user_id)
    print(f"User is now team admin: {member.scheme_admin}")
```

### Revoke Team Admin Role

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"
    user_id = "user_def456"

    # Remove admin privileges (keep as regular member)
    member = await client.teams.remove_admin(team_id, user_id)
    print(f"Admin role removed. Is admin: {member.scheme_admin}")
```

### Get Team Members

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"

    # Get team members with pagination
    members = await client.teams.get_members(team_id, page=0, per_page=100)

    for member in members:
        print(f"User ID: {member.user_id}")
        print(f"  Admin: {member.scheme_admin}")
        print(f"  Roles: {member.roles}")
```

---

## Channel Operations

### List Channels in a Team

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"

    channels = await client.channels.get_by_team(team_id)

    for channel in channels:
        channel_type = {
            "O": "Public",
            "P": "Private",
            "D": "Direct Message",
            "G": "Group Message"
        }.get(channel.type, "Unknown")

        print(f"Channel: {channel.display_name}")
        print(f"  Name: {channel.name}")
        print(f"  Type: {channel_type}")
        print(f"  ID: {channel.id}")
```

### Search Channels

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"

    # Search by channel name or display name
    channels = await client.channels.search(team_id, "general")

    for channel in channels:
        print(f"Found: {channel.display_name} ({channel.name})")
```

### Get Channel by Name

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"

    # Get channel by URL-safe name (not display_name)
    channel = await client.channels.get_by_name(team_id, "town-square")

    if channel:
        print(f"Channel: {channel.display_name}")
        print(f"Purpose: {channel.purpose}")
        print(f"Header: {channel.header}")
    else:
        print("Channel not found")
```

### Create Public Channel

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"

    channel = await client.channels.create(
        team_id=team_id,
        name="dev-updates",  # URL-safe identifier
        display_name="Development Updates",
        channel_type="O",  # "O" for public
        purpose="Share development progress and updates",
        header="Weekly dev updates every Friday",
    )

    print(f"Created channel: {channel.display_name}")
    print(f"Channel ID: {channel.id}")
```

### Create Private Channel

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"

    channel = await client.channels.create(
        team_id=team_id,
        name="leadership-private",
        display_name="Leadership Discussion",
        channel_type="P",  # "P" for private
        purpose="Private leadership discussions",
    )

    print(f"Created private channel: {channel.display_name}")
```

### Create Direct Message (DM)

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Create DM between two users
    user1_id = "user_abc123"
    user2_id = "user_def456"

    dm_channel = await client.channels.create_direct([user1_id, user2_id])

    print(f"Created DM channel: {dm_channel.id}")
    print(f"Channel name: {dm_channel.name}")  # Auto-generated based on user IDs
```

### Create Group Message

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    # Create group message with 3+ users
    user_ids = ["user_abc123", "user_def456", "user_ghi789"]

    group_channel = await client.channels.create_direct(user_ids)

    print(f"Created group message: {group_channel.id}")
```

### Add Channel Member

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"
    user_id = "user_def456"

    member = await client.channels.add_member(channel_id, user_id)

    print(f"Added user {member.user_id} to channel {member.channel_id}")
```

### Remove Channel Member

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"
    user_id = "user_def456"

    result = await client.channels.remove_member(channel_id, user_id)
    print("User removed from channel")
```

### Grant Channel Admin Role

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"
    user_id = "user_def456"

    member = await client.channels.set_admin(channel_id, user_id)
    print(f"User is now channel admin: {member.scheme_admin}")
```

### Revoke Channel Admin Role

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"
    user_id = "user_def456"

    member = await client.channels.remove_admin(channel_id, user_id)
    print(f"Admin role removed. Is admin: {member.scheme_admin}")
```

### Get Channel Members

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"

    members = await client.channels.get_members(channel_id, page=0, per_page=100)

    for member in members:
        print(f"User ID: {member.user_id}")
        print(f"  Admin: {member.scheme_admin}")
        print(f"  Roles: {member.roles}")
```

### Delete Channel

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"

    result = await client.channels.delete(channel_id)
    print("Channel deleted successfully")
```

---

## Messaging

### Send Simple Message

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"

    post = await client.posts.create(
        channel_id=channel_id,
        message="Hello, team! This is a test message.",
    )

    print(f"Message sent! Post ID: {post.id}")
    print(f"Created at: {post.create_at}")
```

### Reply in Thread (using root_id)

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"
    parent_post_id = "post_parent123"

    # Reply to a specific message
    reply = await client.posts.create(
        channel_id=channel_id,
        message="Thanks for the update!",
        root_id=parent_post_id,  # Creates a threaded reply
    )

    print(f"Reply sent! Post ID: {reply.id}")
    print(f"Parent post: {reply.root_id}")
```

### Get Channel Messages with Pagination

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    channel_id = "channel_abc123"

    # Get most recent 60 posts (default)
    posts = await client.posts.get_for_channel(channel_id, page=0, per_page=60)

    for post in posts:
        print(f"[{post.create_at}] {post.user_id}: {post.message}")

    # Get older posts
    older_posts = await client.posts.get_for_channel(channel_id, page=1, per_page=60)
```

### Get Thread Messages

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    root_post_id = "post_parent123"

    # Get all messages in a thread
    thread_posts = await client.posts.get_thread(root_post_id)

    print(f"Thread has {len(thread_posts)} posts:")
    for post in thread_posts:
        indent = "  " if post.root_id else ""
        print(f"{indent}{post.user_id}: {post.message}")
```

### Update Existing Message

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    post_id = "post_abc123"

    updated_post = await client.posts.update(
        post_id=post_id,
        message="This message has been updated!",
    )

    print(f"Message updated! Update time: {updated_post.update_at}")
```

### Delete Message

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    post_id = "post_abc123"

    result = await client.posts.delete(post_id)
    print("Message deleted successfully")
```

### Search Messages in Team

```python
async with AsyncMattermostClient(url=url, token=token) as client:
    team_id = "team_abc123"

    # Search supports Mattermost search syntax
    posts = await client.posts.search(team_id, "from:@johndoe deployment")

    print(f"Found {len(posts)} matching posts:")
    for post in posts:
        print(f"  {post.user_id}: {post.message[:50]}...")

    # Search with advanced syntax
    posts = await client.posts.search(team_id, "in:town-square urgent")
```

---

## Error Handling

### Basic Try/Except Pattern

```python
from mm_async import AsyncMattermostClient
from mm_async.exceptions import MattermostError

async with AsyncMattermostClient(url=url, token=token) as client:
    try:
        user = await client.users.get_by_username("nonexistent")
        if user:
            print(f"Found: {user.username}")
        else:
            print("User not found (returned None)")
    except MattermostError as e:
        print(f"Error: {e}")
        print(f"Status code: {e.status_code}")
        print(f"Response: {e.response_body}")
```

### Handling Authentication Errors

```python
from mm_async import AsyncMattermostClient
from mm_async.exceptions import MattermostAuthError

async def connect_with_retry(url: str, token: str):
    try:
        async with AsyncMattermostClient(url=url, token=token) as client:
            me = await client.users.get_me()
            print(f"Authenticated as: {me.username}")
    except MattermostAuthError as e:
        print(f"Authentication failed: {e}")
        print("Please check your token and try again")
```

### Handling Rate Limits with retry_after

```python
import asyncio
from mm_async import AsyncMattermostClient
from mm_async.exceptions import MattermostRateLimitError

async with AsyncMattermostClient(url=url, token=token) as client:
    try:
        users = await client.users.search("john")
    except MattermostRateLimitError as e:
        print(f"Rate limited: {e}")

        if e.retry_after:
            print(f"Retry after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            # Retry the request
            users = await client.users.search("john")
        else:
            print("Rate limit exceeded, retry later")
```

### Handling Not Found Errors

```python
from mm_async import AsyncMattermostClient
from mm_async.exceptions import MattermostNotFoundError

async with AsyncMattermostClient(url=url, token=token) as client:
    try:
        user = await client.users.get_by_id("invalid_user_id")
    except MattermostNotFoundError:
        print("User does not exist")

    # Alternative: Some methods return None instead of raising
    user = await client.users.get_by_username("maybe_exists")
    if user is None:
        print("User not found (None returned)")
```

### Connection Error Recovery

```python
import asyncio
from mm_async import AsyncMattermostClient
from mm_async.exceptions import MattermostConnectionError

async def robust_client_usage(url: str, token: str):
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            async with AsyncMattermostClient(url=url, token=token) as client:
                me = await client.users.get_me()
                print(f"Connected successfully: {me.username}")
                return
        except MattermostConnectionError as e:
            print(f"Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("Max retries reached. Giving up.")
                raise
```

### Comprehensive Error Handling

```python
from mm_async import AsyncMattermostClient
from mm_async.exceptions import (
    MattermostAuthError,
    MattermostForbiddenError,
    MattermostNotFoundError,
    MattermostRateLimitError,
    MattermostServerError,
    MattermostConnectionError,
    MattermostValidationError,
    MattermostError,
)

async def safe_api_call(client: AsyncMattermostClient):
    try:
        result = await client.users.search("john")
        return result
    except MattermostAuthError:
        print("Authentication failed - check token")
    except MattermostForbiddenError:
        print("Permission denied - insufficient privileges")
    except MattermostNotFoundError:
        print("Resource not found")
    except MattermostRateLimitError as e:
        print(f"Rate limited - retry after {e.retry_after} seconds")
    except MattermostServerError as e:
        print(f"Server error ({e.status_code}) - try again later")
    except MattermostConnectionError:
        print("Connection failed - check network/URL")
    except MattermostValidationError as e:
        print(f"Invalid input: {e}")
    except MattermostError as e:
        print(f"Unknown error: {e} (status: {e.status_code})")
```

---

## Advanced Patterns

### Pagination Helper Function

```python
from typing import AsyncIterator
from mm_async import AsyncMattermostClient

async def paginate_all_teams(
    client: AsyncMattermostClient,
    per_page: int = 100,
) -> AsyncIterator:
    """Fetch all teams using pagination."""
    page = 0
    while True:
        teams = await client.teams.get_all(page=page, per_page=per_page)

        if not teams:
            break

        for team in teams:
            yield team

        # Stop if we got fewer results than requested (last page)
        if len(teams) < per_page:
            break

        page += 1

# Usage
async def main():
    async with AsyncMattermostClient(url=url, token=token) as client:
        async for team in paginate_all_teams(client):
            print(f"Team: {team.display_name}")
```

### Generic Pagination Helper

```python
from typing import AsyncIterator, Callable, TypeVar, Awaitable

T = TypeVar("T")

async def paginate(
    fetch_func: Callable[[int, int], Awaitable[list[T]]],
    per_page: int = 100,
) -> AsyncIterator[T]:
    """Generic pagination helper for any paginated endpoint."""
    page = 0
    while True:
        items = await fetch_func(page, per_page)

        if not items:
            break

        for item in items:
            yield item

        if len(items) < per_page:
            break

        page += 1

# Usage
async def main():
    async with AsyncMattermostClient(url=url, token=token) as client:
        team_id = "team_abc123"

        # Paginate through team members
        async for member in paginate(
            lambda p, pp: client.teams.get_members(team_id, p, pp),
            per_page=50
        ):
            print(f"Member: {member.user_id}")
```

### Bulk User Operations

```python
async def add_users_to_team_bulk(
    client: AsyncMattermostClient,
    team_id: str,
    user_ids: list[str],
):
    """Add multiple users to a team sequentially."""
    results = []

    for user_id in user_ids:
        try:
            member = await client.teams.add_member(team_id, user_id)
            results.append({"user_id": user_id, "success": True, "member": member})
            print(f"Added {user_id} to team")
        except MattermostError as e:
            results.append({"user_id": user_id, "success": False, "error": str(e)})
            print(f"Failed to add {user_id}: {e}")

    return results

# Usage
async def main():
    async with AsyncMattermostClient(url=url, token=token) as client:
        team_id = "team_abc123"
        user_ids = ["user1", "user2", "user3", "user4"]

        results = await add_users_to_team_bulk(client, team_id, user_ids)

        successful = sum(1 for r in results if r["success"])
        print(f"Successfully added {successful}/{len(user_ids)} users")
```

### Concurrent API Calls with asyncio.gather

```python
import asyncio
from mm_async import AsyncMattermostClient

async def fetch_user_details(client: AsyncMattermostClient, user_ids: list[str]):
    """Fetch multiple users concurrently."""
    # Create tasks for concurrent execution
    tasks = [client.users.get_by_id(user_id) for user_id in user_ids]

    # Execute all tasks concurrently
    users = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    results = []
    for user_id, result in zip(user_ids, users):
        if isinstance(result, Exception):
            print(f"Error fetching {user_id}: {result}")
        else:
            results.append(result)

    return results

# Usage
async def main():
    async with AsyncMattermostClient(url=url, token=token) as client:
        user_ids = ["user1", "user2", "user3", "user4", "user5"]

        # Fetch all users concurrently (faster than sequential)
        users = await fetch_user_details(client, user_ids)

        print(f"Fetched {len(users)} users concurrently")
        for user in users:
            print(f"  - {user.username}")
```

### Concurrent Team and Channel Fetch

```python
import asyncio
from mm_async import AsyncMattermostClient

async def fetch_team_with_channels(client: AsyncMattermostClient, team_id: str):
    """Fetch team and its channels concurrently."""
    # Run both API calls in parallel
    team, channels = await asyncio.gather(
        client.teams.get_by_id(team_id),
        client.channels.get_by_team(team_id),
    )

    return {
        "team": team,
        "channels": channels,
        "channel_count": len(channels),
    }

# Usage
async def main():
    async with AsyncMattermostClient(url=url, token=token) as client:
        team_id = "team_abc123"

        result = await fetch_team_with_channels(client, team_id)

        print(f"Team: {result['team'].display_name}")
        print(f"Channels: {result['channel_count']}")
        for channel in result['channels']:
            print(f"  - {channel.display_name}")
```

### Rate-Limited Bulk Operations

```python
import asyncio
from mm_async import AsyncMattermostClient
from mm_async.exceptions import MattermostRateLimitError

async def rate_limited_operation(
    client: AsyncMattermostClient,
    operations: list[Callable],
    delay_between: float = 0.5,
):
    """Execute operations with rate limiting."""
    results = []

    for i, operation in enumerate(operations):
        try:
            result = await operation()
            results.append({"index": i, "success": True, "result": result})
        except MattermostRateLimitError as e:
            # Handle rate limiting
            retry_after = e.retry_after or 60
            print(f"Rate limited, waiting {retry_after}s...")
            await asyncio.sleep(retry_after)

            # Retry the operation
            try:
                result = await operation()
                results.append({"index": i, "success": True, "result": result})
            except Exception as retry_error:
                results.append({"index": i, "success": False, "error": str(retry_error)})
        except Exception as e:
            results.append({"index": i, "success": False, "error": str(e)})

        # Delay between operations to avoid rate limiting
        if i < len(operations) - 1:
            await asyncio.sleep(delay_between)

    return results

# Usage
async def main():
    async with AsyncMattermostClient(url=url, token=token) as client:
        channel_id = "channel_abc123"

        # Create list of operations
        messages = [f"Message {i}" for i in range(10)]
        operations = [
            lambda msg=msg: client.posts.create(channel_id, msg)
            for msg in messages
        ]

        # Execute with rate limiting
        results = await rate_limited_operation(client, operations, delay_between=1.0)

        successful = sum(1 for r in results if r["success"])
        print(f"Sent {successful}/{len(operations)} messages")
```

### Batch Processing with Progress Tracking

```python
import asyncio
from mm_async import AsyncMattermostClient

async def process_users_batch(
    client: AsyncMattermostClient,
    user_ids: list[str],
    batch_size: int = 10,
):
    """Process users in batches with progress tracking."""
    total = len(user_ids)
    processed = 0

    for i in range(0, total, batch_size):
        batch = user_ids[i:i + batch_size]

        # Process batch concurrently
        tasks = [client.users.get_by_id(uid) for uid in batch]
        users = await asyncio.gather(*tasks, return_exceptions=True)

        # Track progress
        processed += len(batch)
        print(f"Progress: {processed}/{total} users processed ({processed/total*100:.1f}%)")

        # Process results
        for user_id, user in zip(batch, users):
            if isinstance(user, Exception):
                print(f"  Error: {user_id} - {user}")
            else:
                print(f"  Success: {user.username}")

        # Small delay between batches
        if i + batch_size < total:
            await asyncio.sleep(0.5)

# Usage
async def main():
    async with AsyncMattermostClient(url=url, token=token) as client:
        # Example: process 100 users in batches of 10
        user_ids = [f"user_{i}" for i in range(100)]
        await process_users_batch(client, user_ids, batch_size=10)
```

---

## Complete Example: Bot Setup

```python
import asyncio
from mm_async import AsyncMattermostClient
from mm_async.exceptions import MattermostError

async def setup_bot_environment():
    """Complete bot setup example."""
    url = "https://mattermost.example.com"
    token = "your-bot-token"

    async with AsyncMattermostClient(url=url, token=token) as client:
        # 1. Verify bot identity
        me = await client.users.get_me()
        print(f"Bot authenticated as: {me.username} ({me.id})")

        # 2. Find or create team
        team = await client.teams.get_by_name("bot-team")
        if not team:
            print("Creating new team...")
            team = await client.teams.create(
                name="bot-team",
                display_name="Bot Team",
                team_type="O"
            )
        print(f"Team: {team.display_name}")

        # 3. Find or create channel
        channel = await client.channels.get_by_name(team.id, "bot-logs")
        if not channel:
            print("Creating bot-logs channel...")
            channel = await client.channels.create(
                team_id=team.id,
                name="bot-logs",
                display_name="Bot Logs",
                channel_type="O",
                purpose="Bot activity logs",
            )
        print(f"Channel: {channel.display_name}")

        # 4. Send startup message
        post = await client.posts.create(
            channel_id=channel.id,
            message="Bot has started successfully!"
        )
        print(f"Startup message sent: {post.id}")

        # 5. Get bot's team membership
        member = await client.teams.get_member(team.id, me.id)
        print(f"Bot team membership: {member.roles}")

# Run the setup
asyncio.run(setup_bot_environment())
```

---

## Tips and Best Practices

1. **Always use context managers** for automatic connection/cleanup
2. **Handle specific exceptions** before generic ones
3. **Use pagination** for large datasets to avoid memory issues
4. **Implement retry logic** for rate limits and transient errors
5. **Batch concurrent operations** to avoid overwhelming the server
6. **Cache frequently accessed data** (teams, channels) to reduce API calls
7. **Log errors with context** (user IDs, channel IDs) for debugging
8. **Use type hints** for better IDE support and code clarity
9. **Test with small datasets** before scaling to production
10. **Monitor rate limits** and implement backoff strategies

---

For more information, see the [README](../README.md) and the [Mattermost API Documentation](https://api.mattermost.com/).
