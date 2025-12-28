from typing import Any, Literal, overload

import falkordb  # type: ignore
import falkordb.asyncio  # type: ignore
import redis
import redis.asyncio
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from ..._settings import settings_manager

_sync_cache: dict[str, falkordb.FalkorDB] = {}
"""
Sync FalkorDB clients cache
"""

_async_cache: dict[str, falkordb.asyncio.FalkorDB] = {}
"""
Async FalkorDB clients cache
"""


@overload
def get_falkordb(
    mode: Literal["sync"],
    settings_key: str | None = None,
    *,
    cache_key: str | None = None,
    use_retry: bool | None = None,
    url: str | None = None,
    **kwargs: Any,
) -> falkordb.FalkorDB: ...


@overload
def get_falkordb(
    mode: Literal["async"],
    settings_key: str | None = None,
    *,
    cache_key: str | None = None,
    use_retry: bool | None = None,
    url: str | None = None,
    **kwargs: Any,
) -> falkordb.asyncio.FalkorDB: ...


def get_falkordb(
    mode: Literal["sync", "async"],
    settings_key: str | None = None,
    *,
    cache_key: str | None = None,
    use_retry: bool | None = None,
    url: str | None = None,
    **kwargs: Any,
) -> falkordb.FalkorDB | falkordb.asyncio.FalkorDB:
    """
    Get a FalkorDB client with shared logic.
    """
    settings = settings_manager.get_settings(settings_key)

    if url is None:
        url = settings.url.get_secret_value()

    if use_retry is None:
        use_retry = settings.use_retry

    params = {**settings.initialize_params, **kwargs}

    if use_retry:
        params.update(
            {
                "socket_timeout": settings.socket_timeout,
                "socket_connect_timeout": settings.socket_connect_timeout,
                "health_check_interval": settings.health_check_interval,
                "retry": Retry(
                    ExponentialBackoff(cap=settings.retry_delay),
                    settings.retry_attempts,
                ),
            }
        )

        if mode == "sync":
            params["retry_on_error"] = [redis.ConnectionError, redis.TimeoutError]
        else:
            params["retry_on_error"] = [
                redis.asyncio.ConnectionError,
                redis.asyncio.TimeoutError,
            ]

    if cache_key is None:
        cache_key = url

    if mode == "sync":
        if cache_key not in _sync_cache:
            _sync_cache[cache_key] = falkordb.FalkorDB.from_url(url, **params)

        return _sync_cache[cache_key]

    else:
        if cache_key not in _async_cache:
            _async_cache[cache_key] = falkordb.asyncio.FalkorDB.from_url(url, **params)

        return _async_cache[cache_key]
