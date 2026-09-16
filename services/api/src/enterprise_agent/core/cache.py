from __future__ import annotations

import json
from collections.abc import MutableMapping

from redis.asyncio import Redis


class CacheBackend:
    async def set_json(self, key: str, value: dict, ttl_sec: int | None = None) -> None:
        raise NotImplementedError

    async def get_json(self, key: str) -> dict | None:
        raise NotImplementedError


class InMemoryCache(CacheBackend):
    def __init__(self) -> None:
        self._store: MutableMapping[str, str] = {}

    async def set_json(self, key: str, value: dict, ttl_sec: int | None = None) -> None:
        _ = ttl_sec
        self._store[key] = json.dumps(value)

    async def get_json(self, key: str) -> dict | None:
        raw = self._store.get(key)
        return json.loads(raw) if raw else None


class RedisCache(CacheBackend):
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def set_json(self, key: str, value: dict, ttl_sec: int | None = None) -> None:
        payload = json.dumps(value)
        if ttl_sec:
            await self._client.set(key, payload, ex=ttl_sec)
        else:
            await self._client.set(key, payload)

    async def get_json(self, key: str) -> dict | None:
        raw = await self._client.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)


async def create_cache(redis_url: str) -> CacheBackend:
    try:
        client = Redis.from_url(redis_url)
        await client.ping()
        return RedisCache(client)
    except Exception:
        return InMemoryCache()
