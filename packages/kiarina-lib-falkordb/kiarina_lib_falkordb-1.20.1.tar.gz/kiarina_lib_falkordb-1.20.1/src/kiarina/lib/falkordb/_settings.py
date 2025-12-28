from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class FalkorDBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_FALKORDB_")

    url: SecretStr = SecretStr("falkor://localhost:6379")
    """
    FalkorDB URL

    Example:
    - falkor://[[username]:[password]]@localhost:6379
    - falkors://[[username]:[password]]@localhost:6379

    Note: This field uses SecretStr to prevent accidental exposure of credentials in logs.
    """

    initialize_params: dict[str, Any] = Field(default_factory=dict)
    """
    Additional parameters to initialize the FalkorDB client.
    """

    use_retry: bool = False
    """
    Whether to enable automatic retries

    When enabled, it is configured to retry upon occurrence of
    redis.ConnectionError or redis.TimeoutError.
    """

    socket_timeout: float = 6.0
    """
    Socket timeout in seconds

    After sending a command, if this time is exceeded, a redis.TimeoutError will be raised.
    """

    socket_connect_timeout: float = 3.0
    """
    Socket connection timeout in seconds

    If this time is exceeded when establishing a new connection, a redis.ConnectionError will occur.
    """

    health_check_interval: int = 60
    """
    Health check interval in seconds

    When acquiring a connection from the pool,
    if the time since last use has elapsed, execute a PING to verify the connection status.
    """

    retry_attempts: int = 3
    """
    Number of retry attempts
    """

    retry_delay: float = 1.0
    """
    Delay between retry attempts in seconds
    """


settings_manager = SettingsManager(FalkorDBSettings, multi=True)
