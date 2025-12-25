"""
PostgreSQL clients for Investify services.

Sync client (psycopg3):
    from investify_utils.postgres import PostgresClient

Async client (asyncpg):
    from investify_utils.postgres import AsyncPostgresClient
"""


def __getattr__(name: str):
    """Lazy import to avoid loading dependencies for unused clients."""
    if name == "PostgresClient":
        from investify_utils.postgres.sync_client import PostgresClient

        return PostgresClient
    if name == "AsyncPostgresClient":
        from investify_utils.postgres.async_client import AsyncPostgresClient

        return AsyncPostgresClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["PostgresClient", "AsyncPostgresClient"]
