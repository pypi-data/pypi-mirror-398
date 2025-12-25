"""
Kafka Avro producer and consumer clients (sync only).

Usage:
    from investify_utils.kafka import AvroProducer, AvroConsumer
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AvroProducer",
    "AvroConsumer",
    "OffsetTracker",
]
