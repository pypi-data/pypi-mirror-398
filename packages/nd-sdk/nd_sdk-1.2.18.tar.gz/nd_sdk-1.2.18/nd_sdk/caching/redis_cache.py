from .base import CacheProvider
from ..observability.factory import get_logger
from ..config.loaders import load_env
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import redis
import json
import re


class RedisCache(CacheProvider):
    """
    Enhanced Redis cache provider with pattern matching support.

    Features:
    - Wildcard pattern matching with SCAN for memory-efficient key retrieval
    - Support for multiple wildcards in a single pattern
    - Configurable batch size for SCAN operations
    - Automatic serialization/deserialization
    """

    DEFAULT_TTL = 3600  # 1 hour
    SCAN_BATCH_SIZE = 1000

    def __init__(self, scan_batch_size: int = SCAN_BATCH_SIZE, environment: str = "dev"):
        """
        Initialize Redis cache with configurable scan batch size.

        Args:
            scan_batch_size: Number of keys to retrieve per SCAN iteration
        """
        self.logger = get_logger.get()
        self.cache = redis.Redis(**{"host": load_env("cache_").get("host"), "port": load_env("cache_").get("port")})
        self.serializer = JSONSerializer()
        self.scan_batch_size = scan_batch_size
        self.environment = environment

    def get(self, key: str) -> Any:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if not found
        """
        try:
            key = f"{self.environment}:{key}"
            data = self.cache.get(key)
            if data is None:
                self.logger.debug(f"Cache miss for key: {key}")
                return None
            return self.serializer.deserialize(data)
        except Exception as e:
            self.logger.error(f"Error retrieving key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (None for no expiration)

        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{self.environment}:{key}"
            serialized = self.serializer.serialize(value)
            if ttl is not None:
                result = self.cache.setex(key, ttl, serialized)
            else:
                result = self.cache.set(key, serialized)

            self.logger.debug(f"[REDIS] SET {key} = {value} (TTL: {ttl})")
            return bool(result)
        except Exception as e:
            self.logger.error(f"Error setting key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            key = f"{self.environment}:{key}"
            result = self.cache.delete(key)
            self.logger.debug(f"[REDIS] DELETE {key}")
            return bool(result)
        except Exception as e:
            self.logger.error(f"Error deleting key '{key}': {e}")
            return False

    def build_pattern(self, pattern_dict: Dict[str, str]) -> str:
        """
        Build a Redis pattern from a dictionary.

        Args:
            pattern_dict: Dictionary with keys as pattern components.
                         Use "*" for wildcard matching.

        Returns:
            Redis SCAN-compatible pattern string
            '*:Cassandra'
        """
        # pattern_dict['environment'] = self.environment
        return ":".join(str(v) for v in pattern_dict.values())

    def scan_keys(self, pattern: str) -> List[str]:
        """
        Scan for keys matching a pattern using SCAN command.

        Uses SCAN instead of KEYS for production safety - it doesn't
        block the Redis server and works incrementally.

        Args:
            pattern: Redis pattern (supports * and ? wildcards)

        Returns:
            List of matching keys (as strings)
        """
        pattern = f"{self.environment}:{pattern}"
        matched_keys = []
        cursor = 0

        try:
            while True:
                cursor, keys = self.cache.scan(
                    cursor=cursor,
                    match=pattern,
                    count=self.scan_batch_size
                )
                # Decode bytes to strings
                matched_keys.extend([k.decode('utf-8') if isinstance(k, bytes) else k
                                     for k in keys])

                if cursor == 0:
                    break

            self.logger.info(f"Found {len(matched_keys)} keys matching pattern: {pattern}")
            return matched_keys

        except Exception as e:
            self.logger.error(f"Error scanning keys with pattern '{pattern}': {e}")
            return []

    def get_multiple_by_pattern(self, pattern: str) -> Dict[str, Any]:
        """
        Retrieve all key-value pairs matching a pattern.

        Args:
            pattern: Redis pattern with wildcards

        Returns:
            Dictionary mapping keys to deserialized values
        """
        # pattern = f"{self.environment}:{pattern}"
        results = {}
        keys = self.scan_keys(pattern)

        if not keys:
            return results

        try:
            # Use pipeline for efficient multi-get
            pipeline = self.cache.pipeline()
            for key in keys:
                pipeline.get(key)

            values = pipeline.execute()

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        results[key] = self.serializer.deserialize(value)
                    except Exception as e:
                        self.logger.warning(f"Failed to deserialize key '{key}': {e}")
                        results[key] = None

            return results

        except Exception as e:
            self.logger.error(f"Error retrieving values for pattern '{pattern}': {e}")
            return {}

    def get_by_pattern(self, pattern: str) -> Optional[Any]:
        """
        Retrieve all key-value pairs matching a pattern.

        Args:
            pattern: Redis pattern with wildcards

        Returns:
            Dictionary mapping keys to deserialized values
        """
        # pattern = f"{self.environment}:{pattern}"
        keys = self.scan_keys(pattern)

        if not keys:
            return None

        try:
            # Use pipeline for efficient multi-get
            pipeline = self.cache.pipeline()
            for key in keys:
                pipeline.get(key)

            values = pipeline.execute()

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        return self.serializer.deserialize(value)
                    except Exception as e:
                        self.logger.warning(f"Failed to deserialize key '{key}': {e}")
                        return None

            return None

        except Exception as e:
            self.logger.error(f"Error retrieving values for pattern '{pattern}': {e}")
            return {}

    def get_by_dict(self, pattern_dict: Dict[str, str], multiple: bool = False) -> Any:
        """
        Retrieve key-value pairs using a pattern dictionary.

        Convenience method that builds the pattern and retrieves values.

        Args:
            pattern_dict: Dictionary defining the pattern

        Returns:
            Dictionary mapping keys to values
            :param pattern_dict:
            :param multiple:
        """
        # pattern_dict['environment'] = self.environment
        pattern = self.build_pattern(pattern_dict)
        if multiple:
            return self.get_multiple_by_pattern(pattern)
        return self.get_by_pattern(pattern)

    def delete_by_pattern(self, pattern: str, batch_size: int = 100) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis pattern with wildcards
            batch_size: Number of keys to delete per batch

        Returns:
            Number of keys deleted
        """
        # pattern = f"{self.environment}:{pattern}"
        keys = self.scan_keys(pattern)

        if not keys:
            return 0

        deleted_count = 0
        try:
            # Delete in batches using pipeline
            for i in range(0, len(keys), batch_size):
                batch = keys[i:i + batch_size]
                pipeline = self.cache.pipeline()
                for key in batch:
                    pipeline.delete(key)
                results = pipeline.execute()
                deleted_count += sum(results)

            self.logger.info(f"Deleted {deleted_count} keys matching pattern: {pattern}")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Error deleting keys with pattern '{pattern}': {e}")
            return deleted_count

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.cache.exists(key))
        except Exception as e:
            self.logger.error(f"Error checking existence of key '{key}': {e}")
            return False

    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining time to live for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiration, None if key doesn't exist
        """
        try:
            ttl = self.cache.ttl(key)
            if ttl == -2:  # Key doesn't exist
                return None
            return ttl
        except Exception as e:
            self.logger.error(f"Error getting TTL for key '{key}': {e}")
            return None


class BaseSerializer(ABC):
    """Abstract base class for serializers."""

    @abstractmethod
    def serialize(self, obj: Any) -> bytes:
        """Serialize an object to bytes."""
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to an object."""
        pass


class JSONSerializer(BaseSerializer):
    """JSON serializer for common data types."""

    def __init__(self):
        self.logger = get_logger.get()

    def serialize(self, obj: Any) -> bytes:
        """
        Serialize object to JSON bytes.

        Args:
            obj: Object to serialize

        Returns:
            UTF-8 encoded JSON bytes

        Raises:
            TypeError: If object is not JSON serializable
            ValueError: If serialization fails
        """
        try:
            return json.dumps(obj, ensure_ascii=False).encode('utf-8')
        except (TypeError, ValueError) as e:
            self.logger.error(f"JSON serialization error: {e}")
            raise

    def deserialize(self, data: bytes) -> Any:
        """
        Deserialize JSON bytes to object.

        Args:
            data: UTF-8 encoded JSON bytes

        Returns:
            Deserialized Python object

        Raises:
            json.JSONDecodeError: If data is not valid JSON
            UnicodeDecodeError: If data is not valid UTF-8
        """
        if data is None:
            return None

        try:
            if isinstance(data, bytes):
                return json.loads(data.decode('utf-8'))
            return json.loads(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self.logger.error(f"JSON deserialization error: {e}")
            raise


# Usage example (for documentation purposes)
"""
# Initialize cache
cache = RedisCache()

# 1. Basic operations
cache.set("user:123", {"name": "John", "age": 30}, ttl=3600)
user = cache.get("user:123")

# 2. Pattern matching with wildcards
pattern_dict = {
    "environment": "dev",
    "service": "*",          # Match any service
    "provider": "Cassandra",
    "category": "provider",
    "identifier": "*"        # Match any identifier
}

# Get all matching keys and values
results = cache.get_by_dict(pattern_dict)
for key, value in results.items():
    print(f"{key}: {value}")

# 3. Direct pattern usage
results = cache.get_by_pattern("*:Cassandra:*:file")

# 4. Get only keys (no values)
keys = cache.scan_keys("dev:api-*:*:provider:config")

# 5. Delete by pattern
deleted = cache.delete_by_pattern("temp:*:*")
print(f"Deleted {deleted} temporary keys")

# 6. Check operations
if cache.exists("user:123"):
    ttl = cache.get_ttl("user:123")
    print(f"Key expires in {ttl} seconds")
"""