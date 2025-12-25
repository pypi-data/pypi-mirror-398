"""
Asynchronous PostgreSQL client using SQLAlchemy async engine with asyncpg driver.

Features:
- Lazy engine initialization (safe for Celery prefork)
- Connection pooling via SQLAlchemy async engine
- Read-only operations (for async web frameworks)

Usage:
    from investify_utils.postgres import AsyncPostgresClient

    client = AsyncPostgresClient(
        host="localhost",
        port=5432,
        username="user",
        password="pass",
        database="db",
    )

    # In async context
    df = await client.read("SELECT * FROM table")
    await client.close()

    # Or as context manager
    async with AsyncPostgresClient(...) as client:
        df = await client.read("SELECT * FROM table")
"""

from urllib.parse import quote

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class AsyncPostgresClient:
    """
    Asynchronous PostgreSQL client with lazy engine initialization.

    Uses SQLAlchemy async engine with asyncpg driver for connection pooling.
    Safe for use with async web frameworks like FastAPI.

    Args:
        host: Database host
        port: Database port
        username: Database username
        password: Database password
        database: Database name
        **kwargs: Additional SQLAlchemy engine options (pool_size, pool_recycle, etc.)
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        database: str,
        port: int = 5432,
        **kwargs,
    ):
        self._uri = self._create_uri(host, username, password, database, port)
        self._kwargs = kwargs
        self._engine: AsyncEngine | None = None

    @staticmethod
    def _create_uri(host: str, username: str, password: str, database: str, port: int) -> str:
        """Create PostgreSQL connection URI for asyncpg."""
        return f"postgresql+asyncpg://{username}:{quote(password)}@{host}:{port}/{database}"

    @property
    def engine(self) -> AsyncEngine:
        """Lazy engine initialization - created on first access."""
        if self._engine is None:
            self._engine = create_async_engine(self._uri, **self._kwargs)
        return self._engine

    async def read(self, query: str) -> pd.DataFrame:
        """
        Read SQL query into a DataFrame.

        Args:
            query: SQL query string

        Returns:
            DataFrame with query results
        """
        sql_text = text(query) if isinstance(query, str) else query

        async with self.engine.connect() as conn:
            result = await conn.execute(sql_text)
            rows = result.fetchall()
            columns = list(result.keys())
            return pd.DataFrame(rows, columns=columns)

    async def close(self) -> None:
        """
        Close the async engine and all connections.

        Call this to clean up resources when done.
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
