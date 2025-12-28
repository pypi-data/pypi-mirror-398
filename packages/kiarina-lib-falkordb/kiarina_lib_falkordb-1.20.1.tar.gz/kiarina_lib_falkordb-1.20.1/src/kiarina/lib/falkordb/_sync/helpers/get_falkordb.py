from typing import Any

from falkordb import FalkorDB  # type: ignore

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
    Get a FalkorDB client.
    """
    return _get_falkordb(
        "sync",
        settings_key,
        cache_key=cache_key,
        use_retry=use_retry,
        url=url,
        **kwargs,
    )
