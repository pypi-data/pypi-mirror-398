"""
Redis Namespace - Whisperer caching operations.

Provides Redis caching operations via Upstash REST API.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class RedisNamespace:
    """
    Redis caching namespace.

    All caching operations go through /api/whisperer/* endpoints.
    TTL enforced: min 60 seconds, max 86400 seconds (24 hours).

    Usage:
        # Set/get values
        await dominus.redis.set("user:123", {"name": "John"}, ttl=3600)
        value = await dominus.redis.get("user:123")

        # Get with TTL refresh
        value = await dominus.redis.get("user:123", nudge=True, ttl=3600)

        # Distributed locks
        acquired = await dominus.redis.setnx("lock:resource", "owner_id", ttl=30)

        # Counters
        count = await dominus.redis.incr("page:views", delta=1)

        # Hash operations
        await dominus.redis.hset("user:123", "email", "john@example.com")
        email = await dominus.redis.hget("user:123", "email")
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set a value with TTL.

        Args:
            key: Key name (logical_path)
            value: Any JSON-serializable value
            ttl: Time-to-live in seconds (60-86400, default: 3600)
            category: Optional namespace category

        Returns:
            Dict with "key", "stored", "ttl_seconds"
        """
        body = {
            "logical_path": key,
            "value": value,
            "ttl_seconds": ttl
        }
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/set",
            body=body
        )

    async def get(
        self,
        key: str,
        category: Optional[str] = None,
        nudge: bool = False,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get a value, optionally refreshing TTL.

        Args:
            key: Key name (logical_path)
            category: Optional namespace category
            nudge: If True, refresh TTL on read
            ttl: New TTL if nudge=True (uses default if not provided)

        Returns:
            Dict with "found" (bool) and "value" (if found)
        """
        body = {
            "logical_path": key,
            "nudge": nudge
        }
        if category:
            body["category"] = category
        if ttl and nudge:
            body["ttl_seconds"] = ttl

        return await self._client._request(
            endpoint="/api/whisperer/get",
            body=body
        )

    async def delete(
        self,
        key: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a key.

        Args:
            key: Key name (logical_path)
            category: Optional namespace category

        Returns:
            Dict with "deleted" (bool)
        """
        body = {"logical_path": key}
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/delete",
            body=body
        )

    async def list(
        self,
        prefix: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List keys by prefix with pagination.

        Args:
            prefix: Key prefix filter
            category: Optional namespace category
            limit: Maximum keys to return (max 500, default: 100)
            cursor: Pagination cursor from previous response

        Returns:
            Dict with "keys" list, "cursor" (for next page), "count"
        """
        body = {"limit": min(limit, 500)}
        if prefix:
            body["logical_prefix"] = prefix
        if category:
            body["category"] = category
        if cursor:
            body["cursor"] = cursor

        return await self._client._request(
            endpoint="/api/whisperer/list",
            body=body
        )

    async def mget(self, keys: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Get multiple keys at once.

        Args:
            keys: List of key specs [{"logical_path": "...", "category": "..."}]
                  Maximum 100 keys per request.

        Returns:
            Dict with "results" list of {"found": bool, "value": ...}
        """
        return await self._client._request(
            endpoint="/api/whisperer/mget",
            body={"keys": keys[:100]}
        )

    async def setnx(
        self,
        key: str,
        value: Any,
        ttl: int = 60,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set if not exists (for distributed locks/idempotency).

        Args:
            key: Key name (logical_path)
            value: Any JSON-serializable value
            ttl: Time-to-live in seconds (60-86400, default: 60)
            category: Optional namespace category

        Returns:
            Dict with "acquired" (bool), and "existing" value if not acquired
        """
        body = {
            "logical_path": key,
            "value": value,
            "ttl_seconds": ttl
        }
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/setnx",
            body=body
        )

    async def incr(
        self,
        key: str,
        delta: int = 1,
        ttl: int = 3600,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Increment counter (creates if not exists).

        Args:
            key: Key name (logical_path)
            delta: Increment amount (can be negative, default: 1)
            ttl: Time-to-live in seconds (60-86400, default: 3600)
            category: Optional namespace category

        Returns:
            Dict with "value" (new counter value)
        """
        body = {
            "logical_path": key,
            "delta": delta,
            "ttl_seconds": ttl
        }
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/incr",
            body=body
        )

    async def hset(
        self,
        key: str,
        field: str,
        value: Any,
        ttl: int = 3600,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set a hash field.

        Args:
            key: Hash key name (logical_path)
            field: Field name within the hash
            value: Any JSON-serializable value
            ttl: Time-to-live in seconds (60-86400, default: 3600)
            category: Optional namespace category

        Returns:
            Dict with "set" (bool - True if new field, False if updated)
        """
        body = {
            "logical_path": key,
            "field": field,
            "value": value,
            "ttl_seconds": ttl
        }
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/hset",
            body=body
        )

    async def hget(
        self,
        key: str,
        field: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a hash field.

        Args:
            key: Hash key name (logical_path)
            field: Field name within the hash
            category: Optional namespace category

        Returns:
            Dict with "found" (bool) and "value" (if found)
        """
        body = {
            "logical_path": key,
            "field": field
        }
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/hget",
            body=body
        )

    async def hgetall(
        self,
        key: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all fields from a hash.

        Args:
            key: Hash key name (logical_path)
            category: Optional namespace category

        Returns:
            Dict with "found" (bool) and "fields" dict (if found)
        """
        body = {"logical_path": key}
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/hgetall",
            body=body
        )

    async def hdel(
        self,
        key: str,
        field: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a hash field.

        Args:
            key: Hash key name (logical_path)
            field: Field name to delete
            category: Optional namespace category

        Returns:
            Dict with "deleted" (bool)
        """
        body = {
            "logical_path": key,
            "field": field
        }
        if category:
            body["category"] = category

        return await self._client._request(
            endpoint="/api/whisperer/hdel",
            body=body
        )
