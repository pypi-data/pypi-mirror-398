"""
Investify Utils - Shared utilities for Investify services.

Install with optional dependencies:
    pip install investify-utils[postgres]        # Sync PostgreSQL client
    pip install investify-utils[postgres-async]  # Async PostgreSQL client
    pip install investify-utils[kafka]           # Kafka Avro producer/consumer
    pip install investify-utils[s3]              # S3 client
    pip install investify-utils[helpers]         # Timestamp/SQL utilities

Usage:
    # Logging (no extra required)
    from investify_utils.logging import setup_logging

    # PostgreSQL
    from investify_utils.postgres import PostgresClient, AsyncPostgresClient

    # Kafka
    from investify_utils.kafka import AvroProducer, AvroConsumer

    # S3
    from investify_utils.s3 import S3Client

    # Helpers
    from investify_utils.helpers import convert_to_pd_timestamp, create_sql_in_filter
"""

__version__ = "2.0.0a8"
