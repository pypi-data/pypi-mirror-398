class CacheSettings:
    """Cache Configuration Settings."""
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str | None
    redis_tls_enabled: bool
    def __new__(cls, **kwargs):
        """Singleton pattern implementation."""
    def __init__(self, *, redis_host: str | None = None, redis_port: int | None = None, redis_db: int | None = None, redis_password: str | None = None, redis_tls_enabled: bool | None = None) -> None:
        """Initialize the cache settings.

        Args:
            redis_host (str, optional): Redis host. Required.
            redis_port (int, optional): Redis port. Required.
            redis_db (int, optional): Redis database. Defaults to 0.
            redis_password (str, optional): Redis password. Defaults to None.
            redis_tls_enabled (bool, optional): Enable TLS. Defaults to False.
        """
