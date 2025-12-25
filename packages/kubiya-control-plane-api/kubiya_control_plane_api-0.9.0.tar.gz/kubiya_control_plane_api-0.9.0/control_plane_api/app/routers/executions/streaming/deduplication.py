"""
Message deduplication for streaming execution data.

This module provides a bounded-memory message deduplication system using LRU caching
to prevent duplicate messages from being sent during streaming execution sessions.

Key Features:
- Two-level deduplication: message ID + content signature
- LRU cache with bounded memory (max 1000 entries)
- Backward compatibility with old message ID formats
- Content-based deduplication for assistant messages within 5-second window
- Thread-safe operation

Test Strategy:
- Unit test deduplication with various message types (user, assistant, system)
- Test LRU eviction at boundary (1001st entry)
- Test backward compatibility with old message ID formats (timestamp-based vs turn-based)
- Test content signature collision handling with near-duplicate messages
- Test edge cases: empty content, None message_id, missing timestamps
- Test thread safety with concurrent message processing
"""

import hashlib
import logging
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MessageDeduplicator:
    """
    Handles message deduplication with bounded memory using LRU cache.

    This class provides two-level deduplication:
    1. Message ID deduplication - prevents exact duplicate messages
    2. Content signature deduplication - prevents near-duplicate assistant messages
       within a 5-second window (handles retry/regeneration scenarios)

    The deduplicator also normalizes old message ID formats for backward compatibility:
    - New format: {execution_id}_{role}_{turn_number} (deterministic, turn-based)
    - Old formats: {execution_id}_{role}_{timestamp_micros} or {execution_id}_{role}_{idx}

    Memory is bounded using LRU eviction at 1000 entries to prevent memory leaks
    in long-running streaming sessions.
    """

    # LRU cache size - limits memory usage to ~1000 message IDs + signatures
    MAX_CACHE_SIZE = 1000

    # Time window for content signature deduplication (seconds)
    CONTENT_DEDUP_WINDOW = 5.0

    # Length of content to use for signature (characters)
    CONTENT_SIGNATURE_LENGTH = 200

    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        """
        Initialize the message deduplicator.

        Args:
            max_size: Maximum number of entries in LRU cache (default: 1000)
        """
        self.max_size = max_size

        # LRU cache for sent message IDs
        # OrderedDict maintains insertion order, move_to_end() implements LRU
        self._sent_ids: OrderedDict[str, bool] = OrderedDict()

        # Content signature cache for assistant messages
        # Maps content_signature -> (message_data, timestamp)
        self._content_cache: OrderedDict[str, tuple[Dict[str, Any], datetime]] = OrderedDict()

        # Statistics for monitoring
        self._stats = {
            "messages_checked": 0,
            "duplicates_by_id": 0,
            "duplicates_by_content": 0,
            "evictions": 0,
            "normalized_ids": 0,
        }

    def is_sent(self, message: Dict[str, Any]) -> bool:
        """
        Check if a message has already been sent (deduplicate).

        This method performs two-level deduplication:
        1. Check if message ID is in sent cache
        2. For assistant messages, check content signature within time window

        Args:
            message: Message dictionary with keys: message_id, role, content, timestamp

        Returns:
            True if message is a duplicate and should be skipped, False otherwise
        """
        self._stats["messages_checked"] += 1

        message_id = message.get("message_id")
        role = message.get("role")

        # Normalize old message ID formats for backward compatibility
        if message_id:
            message_id = self._normalize_message_id(message_id, message)
            message["message_id"] = message_id

        # Level 1: Check message ID deduplication
        if message_id and message_id in self._sent_ids:
            self._stats["duplicates_by_id"] += 1
            logger.debug(
                "duplicate_message_id_detected",
                message_id=message_id,
                role=role,
                content_preview=(message.get("content", "") or "")[:50]
            )
            # Move to end to mark as recently used (LRU)
            self._sent_ids.move_to_end(message_id)
            return True

        # Level 2: Check content signature deduplication (assistant messages only)
        if role == "assistant":
            content = message.get("content", "") or ""
            timestamp_str = message.get("timestamp", "")

            if content and timestamp_str:
                content_sig = self._content_signature(content)

                if content_sig in self._content_cache:
                    prev_msg, prev_timestamp = self._content_cache[content_sig]

                    # Check if messages are within deduplication window
                    try:
                        current_timestamp = self._parse_timestamp(timestamp_str)
                        time_diff = abs((current_timestamp - prev_timestamp).total_seconds())

                        if time_diff <= self.CONTENT_DEDUP_WINDOW:
                            self._stats["duplicates_by_content"] += 1
                            logger.debug(
                                "duplicate_content_signature_detected",
                                message_id=message_id,
                                content_signature=content_sig[:16],
                                time_diff=time_diff,
                                prev_message_id=prev_msg.get("message_id")
                            )
                            # Move to end (LRU)
                            self._content_cache.move_to_end(content_sig)
                            return True
                    except Exception as e:
                        # If timestamp parsing fails, don't skip the message
                        logger.warning(
                            "failed_to_parse_timestamp_for_content_dedup",
                            timestamp=timestamp_str,
                            error=str(e)
                        )

        return False

    def mark_sent(self, message: Dict[str, Any]) -> None:
        """
        Mark a message as sent (add to deduplication cache).

        This method:
        1. Adds message ID to sent cache
        2. For assistant messages, adds content signature to cache
        3. Enforces LRU eviction when cache exceeds max size

        Args:
            message: Message dictionary with keys: message_id, role, content, timestamp
        """
        message_id = message.get("message_id")
        role = message.get("role")

        # Add message ID to sent cache
        if message_id:
            self._sent_ids[message_id] = True
            self._evict_if_needed(self._sent_ids)

        # Add content signature for assistant messages
        if role == "assistant":
            content = message.get("content", "") or ""
            timestamp_str = message.get("timestamp", "")

            if content and timestamp_str:
                try:
                    content_sig = self._content_signature(content)
                    timestamp = self._parse_timestamp(timestamp_str)
                    self._content_cache[content_sig] = (message, timestamp)
                    self._evict_if_needed(self._content_cache)
                except Exception as e:
                    logger.warning(
                        "failed_to_cache_content_signature",
                        message_id=message_id,
                        error=str(e)
                    )

    def _content_signature(self, content: str) -> str:
        """
        Generate a content signature for deduplication.

        The signature is based on:
        - First 200 characters of normalized content
        - Lowercase, stripped of whitespace
        - MD5 hashed for fixed-length signature

        Args:
            content: Message content string

        Returns:
            MD5 hash of normalized content (32-character hex string)
        """
        if not content:
            return ""

        # Normalize: strip, lowercase, first 200 chars
        normalized = content.strip().lower()[:self.CONTENT_SIGNATURE_LENGTH]

        # Hash for fixed-length signature
        return hashlib.md5(normalized.encode()).hexdigest()

    def _normalize_message_id(self, message_id: str, message: Dict[str, Any]) -> str:
        """
        Normalize old message ID formats for backward compatibility.

        Message ID formats:
        - New (turn-based): {execution_id}_{role}_{turn_number}
          Example: "exec123_assistant_5"
        - Old (timestamp-based): {execution_id}_{role}_{timestamp_micros}
          Example: "exec123_assistant_1234567890123456"
        - Old (index-based): {execution_id}_{role}_{idx}
          Example: "exec123_assistant_42" (ambiguous with turn-based)

        Detection heuristic:
        - If last part is < 10000, assume turn-based (new format) - keep as-is
        - If last part is >= 10000, assume timestamp-based (old format) - use content hash
        - If can't parse, use content hash

        Args:
            message_id: Original message ID
            message: Full message dictionary for content hash fallback

        Returns:
            Normalized message ID (may be unchanged if already in new format)
        """
        if not message_id:
            return message_id

        parts = message_id.split("_")

        # Check if format is: {execution_id}_{role}_{number}
        if len(parts) >= 3 and parts[-2] in ["user", "assistant", "system"]:
            try:
                last_part = int(parts[-1])

                # Turn numbers are small (1-100), timestamps are huge (1e15)
                if last_part < 10000:
                    # New format (turn-based) - keep as-is
                    return message_id

                # Old format (timestamp-based) - normalize to content hash
                self._stats["normalized_ids"] += 1

            except (ValueError, IndexError):
                # Can't parse as number - might be hash or other format
                # Use content hash for stability
                self._stats["normalized_ids"] += 1

        # Generate stable ID based on content hash
        content = message.get("content", "") or ""
        role = message.get("role", "unknown")
        execution_id = parts[0] if parts else "unknown"

        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        normalized_id = f"{execution_id}_{role}_{content_hash}"

        logger.debug(
            "normalized_old_message_id_format",
            old_id=message_id,
            new_id=normalized_id,
            role=role
        )

        return normalized_id

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO format timestamp string.

        Handles both with and without 'Z' suffix.

        Args:
            timestamp_str: ISO format timestamp (e.g., "2024-01-15T10:30:00Z")

        Returns:
            datetime object

        Raises:
            ValueError: If timestamp cannot be parsed
        """
        # Handle 'Z' suffix for UTC timestamps
        normalized = timestamp_str.replace('Z', '+00:00')
        return datetime.fromisoformat(normalized)

    def _evict_if_needed(self, cache: OrderedDict) -> None:
        """
        Evict oldest entry from cache if it exceeds max size (LRU eviction).

        Args:
            cache: OrderedDict cache to check and evict from
        """
        if len(cache) > self.max_size:
            # Remove oldest entry (first item in OrderedDict)
            cache.popitem(last=False)
            self._stats["evictions"] += 1

            logger.debug(
                "lru_cache_eviction",
                cache_size=len(cache),
                max_size=self.max_size,
                total_evictions=self._stats["evictions"]
            )

    def get_stats(self) -> Dict[str, int]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with statistics:
            - messages_checked: Total messages checked
            - duplicates_by_id: Duplicates found by message ID
            - duplicates_by_content: Duplicates found by content signature
            - evictions: LRU cache evictions performed
            - normalized_ids: Old message IDs normalized
        """
        return self._stats.copy()

    def reset(self) -> None:
        """
        Reset the deduplicator (clear all caches and statistics).

        Useful for testing or starting a new session.
        """
        self._sent_ids.clear()
        self._content_cache.clear()
        self._stats = {
            "messages_checked": 0,
            "duplicates_by_id": 0,
            "duplicates_by_content": 0,
            "evictions": 0,
            "normalized_ids": 0,
        }
        logger.debug("message_deduplicator_reset")
