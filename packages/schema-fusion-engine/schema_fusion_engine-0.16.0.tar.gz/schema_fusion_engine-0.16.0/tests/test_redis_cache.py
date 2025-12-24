"""Tests for Redis-backed query cache."""

from unittest.mock import Mock, patch

import pytest

from src.core.query.redis_cache import RedisQueryCache


class TestRedisQueryCache:
    """Test cases for RedisQueryCache."""

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_init_redis_cache(self, mock_redis_class):
        """Test Redis cache initialization."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache(host="localhost", port=6379, db=0, ttl=300)

        assert cache.host == "localhost"
        assert cache.port == 6379
        assert cache.db == 0
        assert cache.ttl == 300
        mock_redis_class.assert_called_once()
        mock_redis.ping.assert_called_once()

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_init_redis_cache_connection_failure(self, mock_redis_class):
        """Test Redis cache initialization with connection failure."""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache(host="localhost", port=6379, db=0, ttl=300)

        assert cache._redis is None

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_generate_key(self, mock_redis_class):
        """Test cache key generation."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache()
        key1 = cache._generate_key("SELECT 1", catalog="test", schema="public")
        key2 = cache._generate_key("SELECT 1", catalog="test", schema="public")
        key3 = cache._generate_key("SELECT 2", catalog="test", schema="public")

        assert key1 == key2  # Same query should generate same key
        assert key1 != key3  # Different queries should generate different keys
        assert key1.startswith("schemafusion:query:")

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_get_cache_hit(self, mock_redis_class):
        """Test getting cached result (cache hit)."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = '{"query": "SELECT 1", "rows": [[1]]}'
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache()
        result = cache.get("SELECT 1", catalog="test", schema="public")

        assert result is not None
        assert result["query"] == "SELECT 1"
        assert result["rows"] == [[1]]
        assert cache._hits == 1
        assert cache._misses == 0

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_get_cache_miss(self, mock_redis_class):
        """Test getting cached result (cache miss)."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache()
        result = cache.get("SELECT 1", catalog="test", schema="public")

        assert result is None
        assert cache._hits == 0
        assert cache._misses == 1

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_set_cache(self, mock_redis_class):
        """Test setting cache value."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache(ttl=300)
        result = {"query": "SELECT 1", "rows": [[1]], "row_count": 1}

        cache.set("SELECT 1", result, catalog="test", schema="public")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300  # TTL
        assert "SELECT 1" in call_args[0][2]  # JSON contains query

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_clear_cache(self, mock_redis_class):
        """Test clearing cache."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.keys.return_value = ["schemafusion:query:key1", "schemafusion:query:key2"]
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache()
        cache._hits = 10
        cache._misses = 5

        cache.clear()

        mock_redis.keys.assert_called_once_with("schemafusion:query:*")
        mock_redis.delete.assert_called_once_with(
            "schemafusion:query:key1", "schemafusion:query:key2"
        )
        assert cache._hits == 0
        assert cache._misses == 0

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_stats(self, mock_redis_class):
        """Test cache statistics."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.keys.return_value = ["schemafusion:query:key1"]
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache(host="localhost", port=6379, db=0, ttl=300)
        cache._hits = 10
        cache._misses = 5

        stats = cache.stats()

        assert stats["backend"] == "redis"
        assert stats["hits"] == 10
        assert stats["misses"] == 5
        assert stats["hit_rate"] == pytest.approx(66.67, abs=0.01)
        assert stats["ttl"] == 300
        assert stats["redis"]["connected"] is True
        assert stats["redis"]["host"] == "localhost"
        assert stats["redis"]["port"] == 6379
        assert stats["redis"]["db"] == 0

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_get_with_connection_error(self, mock_redis_class):
        """Test get operation when Redis connection fails."""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache()
        # Cache should be None after failed connection
        assert cache._redis is None

        result = cache.get("SELECT 1")
        assert result is None
        assert cache._misses == 1

    @patch("src.core.query.redis_cache.redis.Redis")
    def test_set_with_connection_error(self, mock_redis_class):
        """Test set operation when Redis connection fails."""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis

        cache = RedisQueryCache()
        result = {"query": "SELECT 1", "rows": [[1]]}

        # Should not raise exception, just silently fail
        cache.set("SELECT 1", result)
        # No assertion needed, just verify no exception
