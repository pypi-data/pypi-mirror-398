import hashlib
import json
from functools import wraps

import redis.asyncio as redis

from .common import nds_get_v

_r = None


async def nds_cache_init():
    global _r
    _r = redis.from_url(
        nds_get_v("CacheURL", "redis://"),
        encoding="utf-8",
        decode_responses=True
    )


async def _get(key: str):
    if _r is None:
        return None

    try:
        data = await _r.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


async def _set(key: str, value):
    if _r is None:
        return

    try:
        await _r.set(key, json.dumps(value), ex=nds_get_v("CacheExpire", 120))
    except Exception:
        return


def nds_cache(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            key = f"{f.__name__}:{hashlib.md5(
                json.dumps([args, kwargs], sort_keys=True, default=str)
                .encode())
                .hexdigest()}"
        except (TypeError, ValueError):
            return await f(*args, **kwargs)

        cached = await _get(key)
        if cached is not None:
            return cached

        result = await f(*args, **kwargs)
        await _set(key, result)
        return result
    return wrapper
