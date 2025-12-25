"""
Slack Tools - Integration with OAuth support and lazy validation

Provides comprehensive Slack API access with configuration-driven capabilities.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin

logger = logging.getLogger(__name__)

try:
    from agno.tools import Toolkit
except ImportError:
    # Fallback for testing
    class Toolkit:
        def __init__(self, name: str):
            self.name = name
            self._tools = []

        def register(self, func):
            self._tools.append(func)

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()
class SlackTools(SchemaFixMixin, Toolkit):
    """
    Slack integration toolkit with OAuth support via Integration API.

    Authentication (priority order):
    1. Integration API (fetch token via /integrations/slack/{id}/token)
    2. Secret from vault (secret_name resolved as environment variable)
    3. SLACK_BOT_TOKEN environment variable (fallback)

    Lazy validation pattern: Don't fail on __init__, validate on first tool use.

    Capabilities are configuration-driven with fine-grained permission control.
    """

    def __init__(
        self,
        integration_id: Optional[str] = None,
        secret_name: Optional[str] = None,  # Deprecated, use secrets
        secrets: Optional[List[str]] = None,
        use_env_fallback: bool = True,
        enable_read_messages: bool = True,
        enable_write_messages: bool = False,
        enable_reactions: bool = False,
        enable_channel_management: bool = False,
        # Fine-grained read permissions
        read_channels: bool = True,
        read_messages: bool = True,
        search_messages: bool = True,
        read_threads: bool = True,
        read_users: bool = True,
        # Fine-grained write permissions
        send_messages: bool = True,
        post_messages: bool = True,
        reply_to_threads: bool = True,
        update_messages: bool = True,
        # Fine-grained reaction permissions
        add_reactions: bool = True,
        remove_reactions: bool = True,
        # Fine-grained channel management permissions
        create_channels: bool = False,
        invite_to_channels: bool = False,
        archive_channels: bool = False,
        set_channel_topic: bool = False,
        # General settings
        timeout: int = 30,
        default_channel: Optional[str] = None,
        # Channel scoping
        allowed_channels: Optional[List[str]] = None,
        blocked_channels: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(name="slack")

        # Store authentication config
        self.integration_id = integration_id
        # Handle backwards compatibility: secret_name -> secrets list
        if secret_name:
            self.secrets = [secret_name]
        elif secrets:
            self.secrets = secrets if isinstance(secrets, list) else [secrets]
        else:
            self.secrets = []
        self.use_env_fallback = use_env_fallback
        self.timeout = timeout
        self.default_channel = default_channel

        # Store channel scoping
        self.allowed_channels = allowed_channels or []
        self.blocked_channels = blocked_channels or []

        # Store capability flags
        self.capabilities = {
            "read_messages": enable_read_messages,
            "write_messages": enable_write_messages,
            "reactions": enable_reactions,
            "channel_management": enable_channel_management,
        }

        # Store fine-grained permissions
        self.permissions = {
            "read_channels": read_channels,
            "read_messages": read_messages,
            "search_messages": search_messages,
            "read_threads": read_threads,
            "read_users": read_users,
            "send_messages": send_messages,
            "post_messages": post_messages,
            "reply_to_threads": reply_to_threads,
            "update_messages": update_messages,
            "add_reactions": add_reactions,
            "remove_reactions": remove_reactions,
            "create_channels": create_channels,
            "invite_to_channels": invite_to_channels,
            "archive_channels": archive_channels,
            "set_channel_topic": set_channel_topic,
        }

        # Lazy initialization - don't fetch token or create client yet
        self._client = None
        self._token = None
        self._auth_checked = False

        # Register tools based on enabled capabilities
        self._register_tools()

    def _is_channel_allowed(self, channel_id: str, channel_name: str = None) -> tuple[bool, Optional[str]]:
        """
        Check if a channel is allowed based on scoping configuration.

        Args:
            channel_id: Channel ID (e.g., "C01234567")
            channel_name: Optional channel name (e.g., "general", "#general")

        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Normalize channel name (remove # prefix if present)
        if channel_name:
            channel_name = channel_name.lstrip('#')

        # If no restrictions, allow all
        if not self.allowed_channels and not self.blocked_channels:
            return True, None

        # Check blocked channels first
        if self.blocked_channels:
            if channel_id in self.blocked_channels:
                return False, f"Channel {channel_id} is blocked by configuration"
            if channel_name and channel_name in self.blocked_channels:
                return False, f"Channel {channel_name} is blocked by configuration"

        # Check allowed channels
        if self.allowed_channels:
            if channel_id not in self.allowed_channels:
                if not channel_name or channel_name not in self.allowed_channels:
                    return False, f"Channel not in allowed list. Allowed channels: {', '.join(self.allowed_channels)}"

        return True, None

    def _register_tools(self):
        """Register tools based on enabled capabilities and permissions."""
        # Always register get_available_channels (useful for discovery)
        self.register(self.get_available_channels)

        # Read Messages Group
        if self.capabilities["read_messages"]:
            if self.permissions["read_channels"]:
                self.register(self.list_channels)
            if self.permissions["read_messages"]:
                self.register(self.get_channel_history)
            if self.permissions["search_messages"]:
                self.register(self.search_messages)
            if self.permissions["read_threads"]:
                self.register(self.get_thread_replies)
            if self.permissions["read_users"]:
                self.register(self.get_user_info)
                self.register(self.list_users)

        # Write Messages Group
        if self.capabilities["write_messages"]:
            if self.permissions["send_messages"]:
                self.register(self.send_message)
            if self.permissions["post_messages"]:
                self.register(self.post_message)
            if self.permissions["reply_to_threads"]:
                self.register(self.reply_to_thread)
            if self.permissions["update_messages"]:
                self.register(self.update_message)
                self.register(self.delete_message)

        # Reactions Group
        if self.capabilities["reactions"]:
            if self.permissions["add_reactions"]:
                self.register(self.add_reaction)
            if self.permissions["remove_reactions"]:
                self.register(self.remove_reaction)
            self.register(self.list_reactions)

        # Channel Management Group
        if self.capabilities["channel_management"]:
            if self.permissions["create_channels"]:
                self.register(self.create_channel)
            if self.permissions["invite_to_channels"]:
                self.register(self.invite_to_channel)
            if self.permissions["archive_channels"]:
                self.register(self.archive_channel)
            if self.permissions["set_channel_topic"]:
                self.register(self.set_channel_topic)
                self.register(self.set_channel_description)

    def _get_client(self):
        """Lazy initialization of Slack client with authentication."""
        if self._client is not None:
            return self._client

        # Get authentication token
        token = self._get_auth_token()

        # Import slack_sdk
        try:
            from slack_sdk import WebClient
        except ImportError:
            raise ImportError(
                "slack_sdk is required for Slack skill. "
                "Install with: pip install slack-sdk"
            )

        # Create client
        self._client = WebClient(token=token, timeout=self.timeout)
        logger.info("Slack WebClient initialized successfully")
        return self._client

    def _get_auth_token(self) -> str:
        """
        Get Slack authentication token.

        Priority:
        1. Integration API (if integration_id provided)
        2. Secrets from vault (if secrets list provided, resolved as env vars)
        3. Environment variable SLACK_BOT_TOKEN (if use_env_fallback=True)

        Returns OAuth URL if integration exists but not authenticated.
        Raises exception if no authentication available.
        """
        if self._token:
            return self._token

        # Try Integration API first
        if self.integration_id:
            logger.info(f"Attempting to fetch Slack token from Integration API for integration_id: {self.integration_id}")
            token = self._fetch_from_integration_api()
            if token:
                self._token = token
                return token

            # If integration exists but no token, return OAuth URL
            oauth_url = self._get_oauth_url()
            if oauth_url:
                logger.warning(f"Slack integration not authenticated, OAuth URL: {oauth_url}")
                raise Exception(
                    f"❌ Slack integration not authenticated.\n\n"
                    f"🔗 Please complete OAuth flow:\n{oauth_url}\n\n"
                    f"After authorizing, please retry your request."
                )

        # Try secrets from vault (resolved as environment variables)
        # Check each secret in order, use first one found
        if self.secrets:
            for secret_name in self.secrets:
                # Secrets from the vault are injected as environment variables
                # by the execution environment controller with the secret name as the key
                token = os.environ.get(secret_name)
                if token:
                    logger.info(f"Using Slack token from secret: {secret_name}")
                    self._token = token
                    return token

            # None of the secrets were found
            logger.warning(f"None of the configured secrets found in environment: {self.secrets}")

        # Try environment variable fallback
        if self.use_env_fallback:
            token = os.environ.get("SLACK_BOT_TOKEN")
            if token:
                logger.info("Using Slack token from SLACK_BOT_TOKEN environment variable")
                self._token = token
                return token

        # No authentication available
        logger.error("No Slack authentication found")
        raise Exception(
            "❌ No Slack authentication found.\n\n"
            "Either provide integration_id with authenticated OAuth, "
            "provide secrets referencing secrets in the vault, "
            "or set SLACK_BOT_TOKEN environment variable."
        )

    def _fetch_from_integration_api(self) -> Optional[str]:
        """Fetch token from Integration API."""
        try:
            import httpx

            # Get integration API base URL from environment
            integration_api_base = os.environ.get(
                "INTEGRATION_API_BASE",
                "https://api.kubiya.ai"
            )
            api_key = os.environ.get("KUBIYA_API_KEY")

            if not api_key:
                logger.warning("KUBIYA_API_KEY not set, cannot fetch from Integration API")
                return None

            # Call Integration API
            url = f"{integration_api_base}/integrations/slack/{self.integration_id}/token"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }

            logger.debug(f"Fetching Slack token from: {url}")
            response = httpx.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            token = data.get("access_token")

            if token:
                logger.info("Successfully fetched Slack token from Integration API")
                return token

            logger.warning("No access_token in Integration API response")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch Slack token from Integration API: {e}")
            return None

    def _get_oauth_url(self) -> Optional[str]:
        """Get OAuth URL for Slack integration."""
        try:
            import httpx

            integration_api_base = os.environ.get(
                "INTEGRATION_API_BASE",
                "https://api.kubiya.ai"
            )
            api_key = os.environ.get("KUBIYA_API_KEY")

            if not api_key:
                return None

            url = f"{integration_api_base}/integrations/slack/{self.integration_id}/oauth-url"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }

            response = httpx.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return data.get("oauth_url")

        except Exception as e:
            logger.error(f"Failed to get OAuth URL: {e}")
            return None

    # ========================================================================
    # Channel Discovery & Scoping
    # ========================================================================

    def get_available_channels(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100
    ) -> str:
        """
        Get list of channels available to this skill based on configuration.

        This tool respects the allowed_channels and blocked_channels configuration,
        returning only channels that the skill is permitted to access.

        Args:
            types: Channel types (public_channel,private_channel,mpim,im)
            limit: Maximum channels to return (default: 100)

        Returns:
            JSON string with available channels and scoping info
        """
        try:
            client = self._get_client()
            response = client.conversations_list(
                types=types,
                limit=min(limit, 1000)
            )

            all_channels = response.get("channels", [])

            # Filter channels based on scoping configuration
            available_channels = []
            blocked_count = 0

            for ch in all_channels:
                channel_id = ch["id"]
                channel_name = ch.get("name")

                # Check if channel is allowed
                is_allowed, error_msg = self._is_channel_allowed(channel_id, channel_name)

                if is_allowed:
                    available_channels.append({
                        "id": ch["id"],
                        "name": ch.get("name"),
                        "is_private": ch.get("is_private", False),
                        "is_archived": ch.get("is_archived", False),
                        "is_member": ch.get("is_member", False),
                        "num_members": ch.get("num_members", 0),
                        "topic": ch.get("topic", {}).get("value", ""),
                        "purpose": ch.get("purpose", {}).get("value", "")
                    })
                else:
                    blocked_count += 1

            result = {
                "success": True,
                "available_channels": available_channels,
                "available_count": len(available_channels),
                "total_channels": len(all_channels),
                "blocked_count": blocked_count,
                "scoping_active": bool(self.allowed_channels or self.blocked_channels),
                "allowed_channels_config": self.allowed_channels,
                "blocked_channels_config": self.blocked_channels,
                "message": (
                    f"Found {len(available_channels)} available channels "
                    f"(blocked {blocked_count} due to configuration)"
                    if blocked_count > 0
                    else f"Found {len(available_channels)} available channels"
                )
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error getting available channels: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    # ========================================================================
    # Read Messages Group
    # ========================================================================

    def list_channels(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100
    ) -> str:
        """
        List Slack channels.

        Args:
            types: Channel types (public_channel,private_channel,mpim,im)
            limit: Maximum channels to return (default: 100)

        Returns:
            JSON string with channel list
        """
        try:
            client = self._get_client()
            response = client.conversations_list(
                types=types,
                limit=min(limit, 1000)
            )

            channels = response.get("channels", [])
            result = {
                "success": True,
                "channels": [
                    {
                        "id": ch["id"],
                        "name": ch.get("name"),
                        "is_private": ch.get("is_private", False),
                        "is_archived": ch.get("is_archived", False),
                        "is_member": ch.get("is_member", False),
                        "num_members": ch.get("num_members", 0),
                        "topic": ch.get("topic", {}).get("value", ""),
                        "purpose": ch.get("purpose", {}).get("value", "")
                    }
                    for ch in channels
                ],
                "count": len(channels)
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def get_channel_history(
        self,
        channel_id: str,
        limit: int = 50,
        oldest: Optional[str] = None,
        latest: Optional[str] = None
    ) -> str:
        """
        Get message history from a Slack channel.

        Args:
            channel_id: Channel ID (required)
            limit: Number of messages (default: 50, max: 1000)
            oldest: Timestamp for oldest message
            latest: Timestamp for latest message

        Returns:
            JSON string with message history
        """
        try:
            client = self._get_client()
            kwargs = {
                "channel": channel_id,
                "limit": min(limit, 1000)
            }
            if oldest:
                kwargs["oldest"] = oldest
            if latest:
                kwargs["latest"] = latest

            response = client.conversations_history(**kwargs)

            messages = response.get("messages", [])
            result = {
                "success": True,
                "channel_id": channel_id,
                "messages": [
                    {
                        "ts": msg.get("ts"),
                        "user": msg.get("user"),
                        "text": msg.get("text"),
                        "type": msg.get("type"),
                        "thread_ts": msg.get("thread_ts"),
                        "reply_count": msg.get("reply_count", 0),
                        "reactions": msg.get("reactions", [])
                    }
                    for msg in messages
                ],
                "count": len(messages),
                "has_more": response.get("has_more", False)
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error getting channel history: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def search_messages(
        self,
        query: str,
        count: int = 20,
        sort: str = "score"
    ) -> str:
        """
        Search for messages in Slack.

        Args:
            query: Search query (required)
            count: Number of results (default: 20, max: 100)
            sort: Sort by 'score' or 'timestamp' (default: score)

        Returns:
            JSON string with search results
        """
        try:
            client = self._get_client()
            response = client.search_messages(
                query=query,
                count=min(count, 100),
                sort=sort
            )

            messages = response.get("messages", {}).get("matches", [])
            result = {
                "success": True,
                "query": query,
                "matches": [
                    {
                        "text": msg.get("text"),
                        "user": msg.get("user"),
                        "username": msg.get("username"),
                        "channel": msg.get("channel", {}).get("name"),
                        "channel_id": msg.get("channel", {}).get("id"),
                        "ts": msg.get("ts"),
                        "permalink": msg.get("permalink"),
                        "type": msg.get("type")
                    }
                    for msg in messages
                ],
                "count": len(messages),
                "total": response.get("messages", {}).get("total", 0)
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def get_thread_replies(
        self,
        channel_id: str,
        thread_ts: str,
        limit: int = 50
    ) -> str:
        """
        Get replies from a Slack thread.

        Args:
            channel_id: Channel ID (required)
            thread_ts: Thread timestamp (required)
            limit: Number of replies (default: 50, max: 1000)

        Returns:
            JSON string with thread replies
        """
        try:
            client = self._get_client()
            response = client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=min(limit, 1000)
            )

            messages = response.get("messages", [])
            result = {
                "success": True,
                "channel_id": channel_id,
                "thread_ts": thread_ts,
                "messages": [
                    {
                        "ts": msg.get("ts"),
                        "user": msg.get("user"),
                        "text": msg.get("text"),
                        "type": msg.get("type"),
                        "reactions": msg.get("reactions", [])
                    }
                    for msg in messages
                ],
                "count": len(messages)
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error getting thread replies: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def get_user_info(
        self,
        user_id: str
    ) -> str:
        """
        Get information about a Slack user.

        Args:
            user_id: User ID (required)

        Returns:
            JSON string with user information
        """
        try:
            client = self._get_client()
            response = client.users_info(user=user_id)

            user = response.get("user", {})
            result = {
                "success": True,
                "user": {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "display_name": user.get("profile", {}).get("display_name"),
                    "email": user.get("profile", {}).get("email"),
                    "title": user.get("profile", {}).get("title"),
                    "is_bot": user.get("is_bot", False),
                    "is_admin": user.get("is_admin", False),
                    "is_owner": user.get("is_owner", False),
                    "tz": user.get("tz"),
                    "status_text": user.get("profile", {}).get("status_text", ""),
                    "status_emoji": user.get("profile", {}).get("status_emoji", "")
                }
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def list_users(
        self,
        limit: int = 100
    ) -> str:
        """
        List users in the Slack workspace.

        Args:
            limit: Maximum users to return (default: 100, max: 1000)

        Returns:
            JSON string with user list
        """
        try:
            client = self._get_client()
            response = client.users_list(limit=min(limit, 1000))

            members = response.get("members", [])
            result = {
                "success": True,
                "users": [
                    {
                        "id": user.get("id"),
                        "name": user.get("name"),
                        "real_name": user.get("real_name"),
                        "display_name": user.get("profile", {}).get("display_name"),
                        "is_bot": user.get("is_bot", False),
                        "is_admin": user.get("is_admin", False),
                        "deleted": user.get("deleted", False)
                    }
                    for user in members
                    if not user.get("deleted", False)  # Filter out deleted users
                ],
                "count": len([u for u in members if not u.get("deleted", False)])
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    # ========================================================================
    # Write Messages Group
    # ========================================================================

    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[str] = None
    ) -> str:
        """
        Send a message to a Slack channel.

        Args:
            channel: Channel ID or name (required)
            text: Message text (required)
            thread_ts: Thread timestamp (to reply in thread)
            blocks: Optional Block Kit blocks as JSON string

        Returns:
            JSON string with message details
        """
        try:
            # Check channel scoping
            is_allowed, error_msg = self._is_channel_allowed(channel, channel)
            if not is_allowed:
                return json.dumps({
                    "success": False,
                    "error": f"❌ Channel access denied: {error_msg}"
                })

            client = self._get_client()
            kwargs = {
                "channel": channel,
                "text": text
            }
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            if blocks:
                kwargs["blocks"] = json.loads(blocks) if isinstance(blocks, str) else blocks

            response = client.chat_postMessage(**kwargs)

            result = {
                "success": True,
                "channel": response.get("channel"),
                "ts": response.get("ts"),
                "message": {
                    "text": response.get("message", {}).get("text"),
                    "user": response.get("message", {}).get("user"),
                    "ts": response.get("message", {}).get("ts")
                }
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[str] = None
    ) -> str:
        """
        Post a message to a Slack channel (alias for send_message without thread).

        Args:
            channel: Channel ID or name (required)
            text: Message text (required)
            blocks: Optional Block Kit blocks as JSON string

        Returns:
            JSON string with message details
        """
        return self.send_message(channel=channel, text=text, blocks=blocks)

    def reply_to_thread(
        self,
        channel: str,
        thread_ts: str,
        text: str
    ) -> str:
        """
        Reply to a Slack thread.

        Args:
            channel: Channel ID or name (required)
            thread_ts: Thread timestamp (required)
            text: Reply text (required)

        Returns:
            JSON string with reply details
        """
        return self.send_message(channel=channel, text=text, thread_ts=thread_ts)

    def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[str] = None
    ) -> str:
        """
        Update an existing Slack message.

        Args:
            channel: Channel ID (required)
            ts: Message timestamp (required)
            text: New message text (required)
            blocks: Optional Block Kit blocks as JSON string

        Returns:
            JSON string with update confirmation
        """
        try:
            client = self._get_client()
            kwargs = {
                "channel": channel,
                "ts": ts,
                "text": text
            }
            if blocks:
                kwargs["blocks"] = json.loads(blocks) if isinstance(blocks, str) else blocks

            response = client.chat_update(**kwargs)

            result = {
                "success": True,
                "channel": response.get("channel"),
                "ts": response.get("ts"),
                "text": response.get("text")
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error updating message: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def delete_message(
        self,
        channel: str,
        ts: str
    ) -> str:
        """
        Delete a Slack message.

        Args:
            channel: Channel ID (required)
            ts: Message timestamp (required)

        Returns:
            JSON string with deletion confirmation
        """
        try:
            client = self._get_client()
            response = client.chat_delete(
                channel=channel,
                ts=ts
            )

            result = {
                "success": True,
                "channel": response.get("channel"),
                "ts": response.get("ts")
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    # ========================================================================
    # Reactions Group
    # ========================================================================

    def add_reaction(
        self,
        channel: str,
        ts: str,
        reaction: str
    ) -> str:
        """
        Add a reaction to a Slack message.

        Args:
            channel: Channel ID (required)
            ts: Message timestamp (required)
            reaction: Reaction emoji name without colons (e.g., 'thumbsup')

        Returns:
            JSON string with confirmation
        """
        try:
            client = self._get_client()
            # Remove colons if present
            reaction = reaction.strip(':')

            response = client.reactions_add(
                channel=channel,
                timestamp=ts,
                name=reaction
            )

            result = {
                "success": True,
                "reaction": reaction,
                "channel": channel,
                "ts": ts
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def remove_reaction(
        self,
        channel: str,
        ts: str,
        reaction: str
    ) -> str:
        """
        Remove a reaction from a Slack message.

        Args:
            channel: Channel ID (required)
            ts: Message timestamp (required)
            reaction: Reaction emoji name without colons (e.g., 'thumbsup')

        Returns:
            JSON string with confirmation
        """
        try:
            client = self._get_client()
            # Remove colons if present
            reaction = reaction.strip(':')

            response = client.reactions_remove(
                channel=channel,
                timestamp=ts,
                name=reaction
            )

            result = {
                "success": True,
                "reaction": reaction,
                "channel": channel,
                "ts": ts
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error removing reaction: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def list_reactions(
        self,
        channel: str,
        ts: str
    ) -> str:
        """
        List reactions on a Slack message.

        Args:
            channel: Channel ID (required)
            ts: Message timestamp (required)

        Returns:
            JSON string with reactions list
        """
        try:
            client = self._get_client()
            response = client.reactions_get(
                channel=channel,
                timestamp=ts
            )

            message = response.get("message", {})
            reactions = message.get("reactions", [])

            result = {
                "success": True,
                "channel": channel,
                "ts": ts,
                "reactions": [
                    {
                        "name": r.get("name"),
                        "count": r.get("count"),
                        "users": r.get("users", [])
                    }
                    for r in reactions
                ],
                "count": len(reactions)
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error listing reactions: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    # ========================================================================
    # Channel Management Group
    # ========================================================================

    def create_channel(
        self,
        name: str,
        is_private: bool = False,
        description: Optional[str] = None
    ) -> str:
        """
        Create a new Slack channel.

        Args:
            name: Channel name (required, lowercase, no spaces)
            is_private: Create as private channel (default: False)
            description: Optional channel description

        Returns:
            JSON string with new channel details
        """
        try:
            client = self._get_client()
            response = client.conversations_create(
                name=name,
                is_private=is_private
            )

            channel = response.get("channel", {})

            # Set description if provided
            if description and channel.get("id"):
                try:
                    client.conversations_setPurpose(
                        channel=channel["id"],
                        purpose=description
                    )
                except:
                    pass  # Description setting is optional

            result = {
                "success": True,
                "channel": {
                    "id": channel.get("id"),
                    "name": channel.get("name"),
                    "is_private": channel.get("is_private", False),
                    "created": channel.get("created")
                }
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error creating channel: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def invite_to_channel(
        self,
        channel: str,
        user_ids: str
    ) -> str:
        """
        Invite users to a Slack channel.

        Args:
            channel: Channel ID (required)
            user_ids: Comma-separated user IDs (required)

        Returns:
            JSON string with confirmation
        """
        try:
            client = self._get_client()
            # Parse user IDs
            users = [uid.strip() for uid in user_ids.split(',')]

            response = client.conversations_invite(
                channel=channel,
                users=users
            )

            result = {
                "success": True,
                "channel": response.get("channel", {}).get("id"),
                "invited_users": users,
                "count": len(users)
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error inviting to channel: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def archive_channel(
        self,
        channel: str
    ) -> str:
        """
        Archive a Slack channel.

        Args:
            channel: Channel ID (required)

        Returns:
            JSON string with confirmation
        """
        try:
            client = self._get_client()
            response = client.conversations_archive(channel=channel)

            result = {
                "success": True,
                "channel": channel
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error archiving channel: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def set_channel_topic(
        self,
        channel: str,
        topic: str
    ) -> str:
        """
        Set a Slack channel's topic.

        Args:
            channel: Channel ID (required)
            topic: New topic text (required)

        Returns:
            JSON string with confirmation
        """
        try:
            client = self._get_client()
            response = client.conversations_setTopic(
                channel=channel,
                topic=topic
            )

            result = {
                "success": True,
                "channel": response.get("channel"),
                "topic": response.get("topic")
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error setting channel topic: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def set_channel_description(
        self,
        channel: str,
        description: str
    ) -> str:
        """
        Set a Slack channel's description (purpose).

        Args:
            channel: Channel ID (required)
            description: New description text (required)

        Returns:
            JSON string with confirmation
        """
        try:
            client = self._get_client()
            response = client.conversations_setPurpose(
                channel=channel,
                purpose=description
            )

            result = {
                "success": True,
                "channel": response.get("channel"),
                "purpose": response.get("purpose")
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error setting channel description: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
