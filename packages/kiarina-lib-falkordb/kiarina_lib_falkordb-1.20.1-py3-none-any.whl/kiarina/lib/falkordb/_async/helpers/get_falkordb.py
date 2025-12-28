from typing import Any

from falkordb.asyncio import FalkorDB  # type: ignore

from ..._core.helpers.get_falkordb import get_falkordb as _get_falkordb


def get_falkordb(
    settings_key: str | None = None,
    *,
    cache_key: str | None = None,
    use_retry: bool | None = None,
    url: str | None = None,
    **kwargs: Any,
) -> FalkorDB:
    """
    Get a FalkorDB client (async version - currently uses sync implementation).

    Note: FalkorDB doesn't have native async support yet, so this currently
    returns the same sync client. This is prepared for future async support.
    """
    return _get_falkordb(
        "async",
        settings_key,
        cache_key=cache_key,
        use_retry=use_retry,
        url=url,
        **kwargs,
    )
