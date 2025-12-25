# investify-utils

Shared utilities for Investify services.

## Installation

```bash
# Sync PostgreSQL client (psycopg3 + SQLAlchemy + pangres)
pip install investify-utils[postgres]

# Async PostgreSQL client (asyncpg + SQLAlchemy)
pip install investify-utils[postgres-async]
```

## PostgreSQL Clients

### Sync Client (PostgresClient)

Uses psycopg3 + SQLAlchemy for connection pooling, pangres for upsert.

```python
from investify_utils.postgres import PostgresClient

client = PostgresClient(
    host="localhost",
    port=5432,
    username="user",
    password="pass",
    database="db",
    # SQLAlchemy pool options
    pool_size=5,
    pool_recycle=3600,
)

# Read
df = client.read("SELECT * FROM table")

# Insert (uses COPY protocol)
client.insert(df, table="my_table", schema="public")

# Upsert (DataFrame index = primary keys)
df = df.set_index(["id"])
client.upsert(df, table="my_table", schema="public")

# Execute DDL/DML
client.execute("DELETE FROM table WHERE id = 1")

# Close (important for Celery workers)
client.close()
```

### Async Client (AsyncPostgresClient)

Uses asyncpg + SQLAlchemy async engine. Read-only.

```python
from investify_utils.postgres import AsyncPostgresClient

client = AsyncPostgresClient(
    host="localhost",
    port=5432,
    username="user",
    password="pass",
    database="db",
    # SQLAlchemy pool options
    pool_size=5,
    pool_recycle=3600,
)

# In async context
df = await client.read("SELECT * FROM table")
await client.close()

# Or as context manager
async with AsyncPostgresClient(...) as client:
    df = await client.read("SELECT * FROM table")
```

## Celery Integration

Both clients use lazy initialization, safe for Celery prefork workers.

```python
# instances/postgres_core.py
from investify_utils.postgres import PostgresClient
from config import settings

postgres_core = PostgresClient(**settings.postgres.model_dump())
```

```python
# celery_app.py
from celery.signals import worker_process_init

@worker_process_init.connect
def init_worker(**_kwargs):
    # Reset engine for each worker (optional with lazy init)
    from instances.postgres_core import postgres_core
    postgres_core.close()
```

## Development

```bash
uv sync
uv run ruff check investify_utils/
```
