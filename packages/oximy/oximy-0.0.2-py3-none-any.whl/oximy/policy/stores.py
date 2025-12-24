"""
Policy Stores

Local stores for rate limiting and cost tracking.
These stores enable in-SDK evaluation of rate_limit and cost_limit rules.
"""

import re
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitEntry:
    """Entry for rate limit tracking."""

    count: int
    window_start: float


@dataclass
class CostEntry:
    """Entry for cost limit tracking."""

    total_cost: float
    window_start: float


def parse_window(window: str) -> int:
    """
    Parses a window string (e.g., '1h', '24h', '7d') into milliseconds.

    Args:
        window: Window string in format like '1m', '1h', '24h', '7d'

    Returns:
        Window duration in milliseconds

    Raises:
        ValueError: If window format is invalid
    """
    match = re.match(r"^(\d+)(m|h|d)$", window)
    if not match:
        raise ValueError(
            f"Invalid window format: {window}. Expected format like '1m', '1h', '24h', '7d'."
        )

    value = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "m": 60 * 1000,  # minutes
        "h": 60 * 60 * 1000,  # hours
        "d": 24 * 60 * 60 * 1000,  # days
    }

    return value * multipliers[unit]


class RateLimitStore:
    """Rate limit store for tracking request counts per key within time windows."""

    def __init__(self) -> None:
        self._entries: dict[str, RateLimitEntry] = {}

    def increment(self, key: str, window_ms: int) -> int:
        """
        Increments the counter for a key and returns the new count.
        Resets the counter if the window has expired.

        Args:
            key: The unique key for this rate limit (e.g., 'rate:user_id:123')
            window_ms: The window duration in milliseconds

        Returns:
            The current count after incrementing
        """
        now = time.time() * 1000  # Convert to milliseconds
        entry = self._entries.get(key)

        if entry is None or now - entry.window_start > window_ms:
            # Window expired or new key, start fresh
            self._entries[key] = RateLimitEntry(count=1, window_start=now)
            return 1

        # Window still active, increment
        entry.count += 1
        return entry.count

    def get(self, key: str, window_ms: int) -> int:
        """
        Gets the current count for a key without incrementing.

        Args:
            key: The unique key to check
            window_ms: The window duration in milliseconds

        Returns:
            The current count, or 0 if not found or expired
        """
        now = time.time() * 1000
        entry = self._entries.get(key)

        if entry is None or now - entry.window_start > window_ms:
            return 0

        return entry.count

    def cleanup(self, max_age_ms: int = 24 * 60 * 60 * 1000) -> None:
        """
        Cleans up expired entries to prevent memory leaks.

        Args:
            max_age_ms: Maximum age before cleanup (default: 24 hours)
        """
        now = time.time() * 1000
        keys_to_delete = [
            key
            for key, entry in self._entries.items()
            if now - entry.window_start > max_age_ms
        ]
        for key in keys_to_delete:
            del self._entries[key]

    def clear(self) -> None:
        """Clears all entries."""
        self._entries.clear()

    @property
    def size(self) -> int:
        """Gets the number of tracked keys."""
        return len(self._entries)


class CostStore:
    """Cost store for tracking cumulative costs per key within time windows."""

    def __init__(self) -> None:
        self._entries: dict[str, CostEntry] = {}

    def add(self, key: str, cost: float, window_ms: int) -> float:
        """
        Adds a cost amount for a key and returns the new total.
        Resets the total if the window has expired.

        Args:
            key: The unique key for this cost limit (e.g., 'cost:user_id:123')
            cost: The cost amount to add (in USD)
            window_ms: The window duration in milliseconds

        Returns:
            The current total cost after adding
        """
        now = time.time() * 1000  # Convert to milliseconds
        entry = self._entries.get(key)

        if entry is None or now - entry.window_start > window_ms:
            # Window expired or new key, start fresh
            self._entries[key] = CostEntry(total_cost=cost, window_start=now)
            return cost

        # Window still active, add to total
        entry.total_cost += cost
        return entry.total_cost

    def get(self, key: str, window_ms: int) -> float:
        """
        Gets the current total cost for a key without adding.

        Args:
            key: The unique key to check
            window_ms: The window duration in milliseconds

        Returns:
            The current total cost, or 0 if not found or expired
        """
        now = time.time() * 1000
        entry = self._entries.get(key)

        if entry is None or now - entry.window_start > window_ms:
            return 0.0

        return entry.total_cost

    def cleanup(self, max_age_ms: int = 24 * 60 * 60 * 1000) -> None:
        """
        Cleans up expired entries to prevent memory leaks.

        Args:
            max_age_ms: Maximum age before cleanup (default: 24 hours)
        """
        now = time.time() * 1000
        keys_to_delete = [
            key
            for key, entry in self._entries.items()
            if now - entry.window_start > max_age_ms
        ]
        for key in keys_to_delete:
            del self._entries[key]

    def clear(self) -> None:
        """Clears all entries."""
        self._entries.clear()

    @property
    def size(self) -> int:
        """Gets the number of tracked keys."""
        return len(self._entries)


@dataclass
class PolicyStores:
    """Combined policy stores for use by the policy manager."""

    rate_limit_store: RateLimitStore
    cost_store: CostStore


def create_policy_stores() -> PolicyStores:
    """Creates a new set of policy stores."""
    return PolicyStores(
        rate_limit_store=RateLimitStore(),
        cost_store=CostStore(),
    )

