"""
Kafka Avro producer and consumer clients.

Sync (for Celery workers, scripts):
    from investify_utils.kafka import AvroProducer, AvroConsumer

Async producer (for LangGraph, FastAPI):
    from investify_utils.kafka import AsyncAvroProducer
"""


def __getattr__(name: str):
    """Lazy import to avoid loading confluent-kafka if not needed."""
    if name == "AvroProducer":
        from investify_utils.kafka.sync_producer import AvroProducer

        return AvroProducer
    if name == "AvroConsumer":
        from investify_utils.kafka.sync_consumer import AvroConsumer

        return AvroConsumer
    if name == "OffsetTracker":
        from investify_utils.kafka.sync_consumer import OffsetTracker

        return OffsetTracker
    if name == "AsyncAvroProducer":
        from investify_utils.kafka.async_producer import AsyncAvroProducer

        return AsyncAvroProducer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AvroProducer",
    "AvroConsumer",
    "OffsetTracker",
    "AsyncAvroProducer",
]
