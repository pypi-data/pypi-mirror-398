"""Online feature store with Redis backend for low-latency serving.

Provides sub-millisecond feature lookups for real-time ML predictions.
"""

import json
from typing import Any

import structlog

from forge_flow.exceptions import FeatureStoreError

logger = structlog.get_logger(__name__)


class OnlineStore:
    """Redis-based online feature store for low-latency serving.

    Features:
    - Sub-millisecond feature lookups
    - TTL management for feature freshness
    - Batch get operations
    - Automatic serialization/deserialization

    Example:
        >>> store = OnlineStore(backend="redis", host="localhost", port=6379)
        >>> # Set features
        >>> store.set_features(
        ...     entity_id="user_123",
        ...     feature_set="fraud_detection_v1",
        ...     features={"age": 25, "income": 50000}
        ... )
        >>> # Get features
        >>> features = store.get_features(
        ...     entity_id="user_123",
        ...     feature_set="fraud_detection_v1"
        ... )
    """

    def __init__(
        self,
        backend: str = "redis",
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        default_ttl: int = 3600,
    ) -> None:
        """Initialize online store.

        Args:
            backend: Backend type (currently only 'redis' supported).
            host: Redis host.
            port: Redis port.
            db: Redis database number.
            password: Optional Redis password.
            default_ttl: Default TTL in seconds for features.

        Raises:
            FeatureStoreError: If Redis connection fails.
        """
        if backend != "redis":
            raise FeatureStoreError(f"Unsupported backend: {backend}")

        self.backend = backend
        self.default_ttl = default_ttl

        try:
            import redis

            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
            )

            # Test connection
            self.client.ping()

            logger.info(
                "online_store_initialized",
                backend=backend,
                host=host,
                port=port,
            )

        except ImportError as e:
            raise FeatureStoreError(
                "Redis not installed. Install with: pip install forge-flow[serving]"
            ) from e
        except (ConnectionError, TimeoutError) as e:
            logger.error("redis_connection_failed", host=host, port=port, error=str(e))
            raise FeatureStoreError(f"Failed to connect to Redis: {e}") from e

    def _make_key(self, entity_id: str, feature_set: str) -> str:
        """Generate Redis key for entity and feature set.

        Args:
            entity_id: Entity identifier.
            feature_set: Feature set name.

        Returns:
            Redis key string.
        """
        return f"features:{feature_set}:{entity_id}"

    def set_features(
        self,
        entity_id: str,
        feature_set: str,
        features: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set features for an entity.

        Args:
            entity_id: Entity identifier (e.g., 'user_123').
            feature_set: Feature set name (e.g., 'fraud_detection_v1').
            features: Dictionary of feature values.
            ttl: Optional TTL in seconds (uses default_ttl if None).

        Raises:
            FeatureStoreError: If operation fails.
        """
        try:
            key = self._make_key(entity_id, feature_set)
            value = json.dumps(features)
            ttl = ttl or self.default_ttl

            self.client.setex(key, ttl, value)

            logger.debug(
                "features_set",
                entity_id=entity_id,
                feature_set=feature_set,
                feature_count=len(features),
                ttl=ttl,
            )

        except Exception as e:
            logger.error(
                "set_features_failed",
                entity_id=entity_id,
                feature_set=feature_set,
                error=str(e),
            )
            raise FeatureStoreError(f"Failed to set features: {e}") from e

    def get_features(
        self,
        entity_id: str,
        feature_set: str,
    ) -> dict[str, Any] | None:
        """Get features for an entity.

        Args:
            entity_id: Entity identifier.
            feature_set: Feature set name.

        Returns:
            Dictionary of feature values, or None if not found.

        Raises:
            FeatureStoreError: If operation fails.
        """
        try:
            key = self._make_key(entity_id, feature_set)
            value = self.client.get(key)

            if value is None:
                logger.debug(
                    "features_not_found",
                    entity_id=entity_id,
                    feature_set=feature_set,
                )
                return None

            features = json.loads(value)

            logger.debug(
                "features_retrieved",
                entity_id=entity_id,
                feature_set=feature_set,
                feature_count=len(features),
            )

            return features

        except Exception as e:
            logger.error(
                "get_features_failed",
                entity_id=entity_id,
                feature_set=feature_set,
                error=str(e),
            )
            raise FeatureStoreError(f"Failed to get features: {e}") from e

    def batch_get_features(
        self,
        entity_ids: list[str],
        feature_set: str,
    ) -> dict[str, dict[str, Any] | None]:
        """Get features for multiple entities in one operation.

        Args:
            entity_ids: List of entity identifiers.
            feature_set: Feature set name.

        Returns:
            Dictionary mapping entity_id to features (or None if not found).

        Raises:
            FeatureStoreError: If operation fails.
        """
        try:
            keys = [self._make_key(eid, feature_set) for eid in entity_ids]

            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            for key in keys:
                pipe.get(key)

            values = pipe.execute()

            # Parse results
            results = {}
            for entity_id, value in zip(entity_ids, values, strict=False):
                if value is not None:
                    results[entity_id] = json.loads(value)
                else:
                    results[entity_id] = None

            logger.info(
                "batch_features_retrieved",
                feature_set=feature_set,
                requested=len(entity_ids),
                found=sum(1 for v in results.values() if v is not None),
            )

            return results

        except Exception as e:
            logger.error(
                "batch_get_features_failed",
                feature_set=feature_set,
                error=str(e),
            )
            raise FeatureStoreError(f"Batch get features failed: {e}") from e

    def delete_features(self, entity_id: str, feature_set: str) -> None:
        """Delete features for an entity.

        Args:
            entity_id: Entity identifier.
            feature_set: Feature set name.

        Raises:
            FeatureStoreError: If operation fails.
        """
        try:
            key = self._make_key(entity_id, feature_set)
            self.client.delete(key)

            logger.debug(
                "features_deleted",
                entity_id=entity_id,
                feature_set=feature_set,
            )

        except Exception as e:
            logger.error(
                "delete_features_failed",
                entity_id=entity_id,
                feature_set=feature_set,
                error=str(e),
            )
            raise FeatureStoreError(f"Failed to delete features: {e}") from e

    def close(self) -> None:
        """Close Redis connection."""
        if hasattr(self, "client"):
            self.client.close()
            logger.info("online_store_closed")
