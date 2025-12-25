"""
Synchronous PostgreSQL client using psycopg3.

Features:
- Lazy initialization (safe for Celery prefork)
- Connection pooling via SQLAlchemy
- COPY protocol for fast inserts
- Upsert via pangres

Usage:
    from investify_utils.postgres import PostgresClient

    client = PostgresClient(
        host="localhost",
        port=5432,
        username="user",
        password="pass",
        database="db",
    )

    df = client.read("SELECT * FROM table")
    client.insert(df, "table", schema="public")
    client.upsert(df, "table", schema="public")
    client.execute("DELETE FROM table WHERE id = 1")
"""

import csv
from collections.abc import Iterable
from io import StringIO
from typing import Literal
from urllib.parse import quote

import pandas as pd
import pangres
from pandas.io.sql import SQLTable
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class PostgresClient:
    """
    Synchronous PostgreSQL client with lazy initialization.

    Uses SQLAlchemy engine with psycopg3 driver for connection pooling.
    Safe for use with Celery prefork workers - engine is created on first use.

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
        self._engine: Engine | None = None

    @staticmethod
    def _create_uri(host: str, username: str, password: str, database: str, port: int) -> str:
        """Create PostgreSQL connection URI."""
        return f"postgresql+psycopg://{username}:{quote(password)}@{host}:{port}/{database}"

    @property
    def engine(self) -> Engine:
        """Lazy engine initialization - created on first access."""
        if self._engine is None:
            self._engine = create_engine(self._uri, **self._kwargs)
        return self._engine

    def read(self, query: str, chunksize: int | None = None) -> pd.DataFrame:
        """
        Read SQL query into a DataFrame.

        Args:
            query: SQL query string
            chunksize: If specified, return iterator of DataFrames with this many rows each.
                      If None, return single DataFrame.

        Returns:
            DataFrame with query results
        """
        sql_text = text(query) if isinstance(query, str) else query

        if chunksize is not None:
            chunks = pd.read_sql(sql_text, self.engine, chunksize=chunksize)
            return pd.concat(list(chunks), ignore_index=True)
        return pd.read_sql(sql_text, self.engine)

    def insert(
        self,
        df: pd.DataFrame,
        table: str,
        schema: str | None = None,
        chunksize: int | None = 10000,
        index: bool = False,
    ) -> None:
        """
        Insert rows from DataFrame into table using COPY protocol.

        Args:
            df: DataFrame to insert
            table: Target table name
            schema: Target schema (default: public)
            chunksize: Rows per chunk (default: 10000)
            index: Include DataFrame index as column (default: False)
        """
        df.to_sql(
            table,
            self.engine,
            schema=schema,
            chunksize=chunksize,
            if_exists="append",
            index=index,
            method=self._psql_insert_copy,
        )

    @staticmethod
    def _psql_insert_copy(table: SQLTable, engine: Engine, keys: list[str], data_iter: Iterable[tuple]):
        """COPY protocol insert method for pandas to_sql."""
        with engine.connection.cursor() as cur:
            s_buf = StringIO()
            writer = csv.writer(s_buf)
            writer.writerows(data_iter)
            s_buf.seek(0)

            columns = ", ".join(f'"{k}"' for k in keys)
            table_name = f"{table.schema}.{table.name}" if table.schema else table.name

            sql = f"COPY {table_name} ({columns}) FROM STDIN WITH CSV"
            with cur.copy(sql) as copy:
                copy.write(s_buf.getvalue())

    def upsert(
        self,
        df: pd.DataFrame,
        table: str,
        schema: str | None = None,
        if_row_exists: Literal["ignore", "update"] = "update",
        create_schema: bool = False,
        create_table: bool = False,
        add_new_columns: bool = False,
        chunksize: int | None = 10000,
        dtype: dict | None = None,
    ) -> None:
        """
        Upsert rows from DataFrame into table.

        Uses pangres library. DataFrame index must contain primary key columns.

        Args:
            df: DataFrame to upsert (index = primary key columns)
            table: Target table name
            schema: Target schema
            if_row_exists: "update" for upsert, "ignore" for insert-only
            create_schema: Create schema if not exists
            create_table: Create table if not exists
            add_new_columns: Add new columns from DataFrame to table
            chunksize: Rows per chunk
            dtype: Column type overrides
        """
        pangres.upsert(
            self.engine,
            df,
            table,
            if_row_exists=if_row_exists,
            schema=schema,
            create_schema=create_schema,
            create_table=create_table,
            add_new_columns=add_new_columns,
            chunksize=chunksize,
            dtype=dtype,
        )

    def execute(self, stmt: str) -> None:
        """
        Execute a SQL statement (INSERT, UPDATE, DELETE, DDL).

        Args:
            stmt: SQL statement to execute
        """
        with self.engine.connect() as conn:
            conn.execute(text(stmt))
            conn.commit()

    def close(self) -> None:
        """
        Close the engine and all connections.

        Call this in Celery worker_process_init if using eager initialization.
        With lazy init, this resets the engine for recreation on next use.
        """
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
