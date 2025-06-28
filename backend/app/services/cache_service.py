import os
import json
import asyncio

try:
    import redis
    try:
        aioredis = redis.asyncio
    except AttributeError:
        aioredis = None
except ImportError:
    aioredis = None

class CacheService:
    """
    Modern, robust, and bug-free async cache service using aioredis.
    Improvements:
    - Handles Redis connection errors gracefully.
    - Allows configuration via environment variables.
    - Defensive: returns None on error.
    - TTL configurable, default 5 minutes.
    - All cache keys are namespaced.
    """

    def __init__(self, url=None, namespace="cache", ttl=300):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost")
        self.namespace = namespace
        self.ttl = ttl
        self._redis = None
        self.enabled = aioredis is not None

    async def connect(self):
        if not self.enabled:
            print("[CacheService] aioredis not installed. Cache disabled.")
            return
        if self._redis is not None:
            return
        try:
            # aioredis.from_url is available in redis-py >= 4.2.0
            self._redis = aioredis.from_url(self.url, encoding="utf-8", decode_responses=True)
            # Test connection
            await self._redis.ping()
        except Exception as e:
            print(f"[CacheService] Redis connection failed: {e}")
            self._redis = None
            self.enabled = False

    def _key(self, key):
        return f"{self.namespace}:{key}"

    async def get(self, key):
        if not self.enabled:
            return None
        await self.connect()
        if not self._redis:
            return None
        try:
            value = await self._redis.get(self._key(key))
            return json.loads(value) if value else None
        except Exception as e:
            print(f"[CacheService] Error getting key '{key}': {e}")
            return None

    async def set(self, key, value, ttl=None):
        if not self.enabled:
            return
        await self.connect()
        if not self._redis:
            return
        try:
            await self._redis.set(self._key(key), json.dumps(value), ex=ttl or self.ttl)
        except Exception as e:
            print(f"[CacheService] Error setting key '{key}': {e}")

# Singleton instance for convenience
cache_service = CacheService()

# Backwards-compatible functional API
async def cache_get(key):
    return await cache_service.get(key)

async def cache_set(key, value, ttl=300):
    await cache_service.set(key, value, ttl=ttl)
