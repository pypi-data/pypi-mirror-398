"""NATS JetStream KeyValue Store Helpers.

This module provides helper functions for interacting with NATS JetStream
KeyValue stores, commonly used by Kryten services for state persistence.
"""

import json
import logging
from typing import Any

from nats.aio.client import Client as NATSClient
from nats.js import JetStreamContext
from nats.js import api


async def get_kv_store(
    nats_client: NATSClient,
    bucket_name: str,
    logger: logging.Logger | None = None
) -> Any:
    """Get an existing NATS JetStream KeyValue store.

    This function only binds to existing buckets. It does NOT create buckets
    because bucket creation requires specific configuration (max_value_size, etc.)
    that varies by use case. Bucket creation is the responsibility of the service
    that owns the data (typically kryten-robot).

    Args:
        nats_client: Connected NATS client.
        bucket_name: Name of the KV bucket.
        logger: Optional logger for error reporting.

    Returns:
        KeyValue bucket instance.

    Raises:
        Exception: If JetStream is not available or bucket doesn't exist.

    Examples:
        >>> kv = await get_kv_store(nats_client, "my_bucket", logger)
        >>> await kv.put("key", b"value")
    """
    try:
        js: JetStreamContext = nats_client.jetstream()
        kv = await js.key_value(bucket_name)
        if logger:
            logger.debug("Accessed KV bucket: %s", bucket_name)
        return kv
    except Exception as e:
        if logger:
            logger.error(
                "KV bucket '%s' does not exist. Ensure kryten-robot is running "
                "and has created the bucket: %s", bucket_name, e
            )
        raise


async def get_or_create_kv_store(
    nats_client: NATSClient,
    bucket_name: str,
    description: str | None = None,
    max_value_size: int = 1024 * 1024,  # 1MB default
    logger: logging.Logger | None = None
) -> Any:
    """Get or create a NATS JetStream KeyValue store.

    This function binds to an existing bucket if it exists, or creates it
    with the specified configuration if it doesn't. Use this for services
    that own their own buckets (e.g., kryten-moderator for moderation data).

    Args:
        nats_client: Connected NATS client.
        bucket_name: Name of the KV bucket.
        description: Description for the bucket (used on creation).
        max_value_size: Maximum value size in bytes (default 1MB).
        logger: Optional logger for error reporting.

    Returns:
        KeyValue bucket instance.

    Raises:
        Exception: If JetStream is not available.

    Examples:
        >>> kv = await get_or_create_kv_store(
        ...     nats_client, "my_bucket",
        ...     description="My service state",
        ...     logger=logger
        ... )
        >>> await kv.put("key", b"value")
    """
    js: JetStreamContext = nats_client.jetstream()

    try:
        kv = await js.key_value(bucket_name)
        if logger:
            logger.debug("Bound to existing KV bucket: %s", bucket_name)
        return kv
    except Exception:
        # Bucket doesn't exist, create it
        kv = await js.create_key_value(
            config=api.KeyValueConfig(
                bucket=bucket_name,
                description=description or f"Kryten {bucket_name}",
                max_value_size=max_value_size,
            )
        )
        if logger:
            logger.info("Created KV bucket: %s", bucket_name)
        return kv


async def kv_get(
    kv_store: Any,
    key: str,
    default: Any = None,
    parse_json: bool = False,
    logger: logging.Logger | None = None
) -> Any:
    """Get a value from KeyValue store.

    Args:
        kv_store: KeyValue bucket instance.
        key: Key to retrieve.
        default: Default value if key doesn't exist.
        parse_json: If True, parse value as JSON.
        logger: Optional logger for error reporting.

    Returns:
        Value from store, or default if key doesn't exist.

    Examples:
        >>> value = await kv_get(kv, "config", default={}, parse_json=True)
        >>> raw_bytes = await kv_get(kv, "data")
    """
    try:
        entry = await kv_store.get(key)
        if entry is None:
            return default

        value = entry.value
        if parse_json and value:
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                if logger:
                    logger.error("Failed to parse JSON for key %s: %s", key, e)
                return default

        return value if value is not None else default

    except Exception as e:
        if logger:
            logger.error("Failed to get key %s: %s", key, e)
        return default


async def kv_put(
    kv_store: Any,
    key: str,
    value: Any,
    as_json: bool = False,
    logger: logging.Logger | None = None
) -> bool:
    """Put a value into KeyValue store.

    Args:
        kv_store: KeyValue bucket instance.
        key: Key to store.
        value: Value to store (bytes, str, or dict/list if as_json=True).
        as_json: If True, serialize value as JSON.
        logger: Optional logger for error reporting.

    Returns:
        True if successful, False otherwise.

    Examples:
        >>> await kv_put(kv, "config", {"setting": "value"}, as_json=True)
        >>> await kv_put(kv, "data", b"raw bytes")
    """
    try:
        if as_json:
            data = json.dumps(value).encode('utf-8')
        elif isinstance(value, str):
            data = value.encode('utf-8')
        elif isinstance(value, bytes):
            data = value
        else:
            # Try to convert to string then bytes
            data = str(value).encode('utf-8')

        await kv_store.put(key, data)
        if logger:
            logger.debug("Stored key %s in KV store", key)
        return True

    except Exception as e:
        if logger:
            logger.error("Failed to put key %s: %s", key, e)
        return False


async def kv_delete(
    kv_store: Any,
    key: str,
    logger: logging.Logger | None = None
) -> bool:
    """Delete a key from KeyValue store.

    Args:
        kv_store: KeyValue bucket instance.
        key: Key to delete.
        logger: Optional logger for error reporting.

    Returns:
        True if successful, False otherwise.

    Examples:
        >>> await kv_delete(kv, "old_key")
    """
    try:
        await kv_store.delete(key)
        if logger:
            logger.debug("Deleted key %s from KV store", key)
        return True
    except Exception as e:
        if logger:
            logger.error("Failed to delete key %s: %s", key, e)
        return False


async def kv_keys(
    kv_store: Any,
    logger: logging.Logger | None = None
) -> list[str]:
    """Get all keys from KeyValue store.

    Args:
        kv_store: KeyValue bucket instance.
        logger: Optional logger for error reporting.

    Returns:
        List of keys in the store.

    Examples:
        >>> keys = await kv_keys(kv)
        >>> print(f"Found {len(keys)} keys")
    """
    try:
        keys = await kv_store.keys()
        return keys if keys else []
    except Exception as e:
        if logger:
            logger.error("Failed to get keys: %s", e)
        return []


async def kv_get_all(
    kv_store: Any,
    parse_json: bool = False,
    logger: logging.Logger | None = None
) -> dict[str, Any]:
    """Get all key-value pairs from KeyValue store.

    Args:
        kv_store: KeyValue bucket instance.
        parse_json: If True, parse values as JSON.
        logger: Optional logger for error reporting.

    Returns:
        Dictionary of all key-value pairs.

    Examples:
        >>> data = await kv_get_all(kv, parse_json=True)
        >>> for key, value in data.items():
        ...     print(f"{key}: {value}")
    """
    result = {}
    keys = await kv_keys(kv_store, logger)

    for key in keys:
        value = await kv_get(kv_store, key, parse_json=parse_json, logger=logger)
        if value is not None:
            result[key] = value

    return result


__all__ = [
    "get_kv_store",
    "kv_get",
    "kv_put",
    "kv_delete",
    "kv_keys",
    "kv_get_all",
]
