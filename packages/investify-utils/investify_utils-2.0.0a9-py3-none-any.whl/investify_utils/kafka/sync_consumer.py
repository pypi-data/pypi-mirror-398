"""
Synchronous Avro consumer using confluent-kafka.

Features:
- Avro deserialization with Schema Registry
- Offset tracking for reliable commits
- Seek to end option for real-time streaming

Usage:
    from investify_utils.kafka import AvroConsumer

    consumer = AvroConsumer(
        topic="my-topic",
        subject="my-topic-value",
        schema_registry_url="http://localhost:8081",
        bootstrap_servers="localhost:9092",
        group_id="my-consumer-group",
    )

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            print(msg.key(), msg.value())
            consumer.commit()
    finally:
        consumer.close()
"""

import logging
from collections import defaultdict

from confluent_kafka import DeserializingConsumer, TopicPartition
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer

logger = logging.getLogger(__name__)


class OffsetTracker:
    """
    Track message offsets for reliable commits with out-of-order processing.

    Only commits offsets where all previous offsets have been marked done,
    preventing data loss when processing messages in parallel.
    """

    def __init__(self):
        self._tracker = defaultdict(lambda: defaultdict(lambda: defaultdict(bool)))

    def log(self, msg, done: bool = False) -> None:
        """
        Log a message offset.

        Args:
            msg: Kafka message
            done: Whether processing is complete
        """
        topic = msg.topic()
        partition = msg.partition()
        offset = msg.offset()
        self._tracker[topic][partition][offset] = done

    def prepare_commit_offsets(self) -> list[TopicPartition]:
        """
        Get offsets safe to commit.

        Returns:
            List of TopicPartition with offsets to commit
        """
        new_tracker = defaultdict(lambda: defaultdict(lambda: defaultdict(bool)))
        to_commit_offsets = []

        for topic, partitions in self._tracker.items():
            for partition, offsets in partitions.items():
                sorted_offsets = sorted(offsets.items())
                to_commit_offset = None
                update_to_commit_offset = True

                for offset, done in sorted_offsets:
                    update_to_commit_offset = update_to_commit_offset and done
                    if update_to_commit_offset:
                        to_commit_offset = offset + 1
                    else:
                        new_tracker[topic][partition][offset] = done

                if to_commit_offset is not None:
                    to_commit_offsets.append(TopicPartition(topic, partition, to_commit_offset))

        self._tracker = new_tracker
        return to_commit_offsets


class AvroConsumer:
    """
    Synchronous Avro consumer.

    Args:
        topic: Kafka topic name or list of topics
        subject: Schema Registry subject name
        schema_registry_url: Schema Registry URL
        bootstrap_servers: Kafka bootstrap servers
        group_id: Consumer group ID
        seek_to_end: Start from latest offset (default: False)
        **kwargs: Additional Kafka consumer config
    """

    def __init__(
        self,
        topic: str | list[str],
        subject: str,
        schema_registry_url: str,
        bootstrap_servers: str,
        group_id: str,
        seek_to_end: bool = False,
        **kwargs,
    ):
        self._schema_registry_url = schema_registry_url
        self._bootstrap_servers = bootstrap_servers
        self._subject = subject
        self._group_id = group_id
        self._topic = topic
        self._seek_to_end = seek_to_end
        self._kwargs = kwargs
        self._consumer: DeserializingConsumer | None = None

    @property
    def consumer(self) -> DeserializingConsumer:
        """Lazy consumer initialization."""
        if self._consumer is None:
            schema_registry_client = SchemaRegistryClient({"url": self._schema_registry_url})
            registered_schema = schema_registry_client.get_latest_version(self._subject)
            schema_str = registered_schema.schema.schema_str

            avro_deserializer = AvroDeserializer(schema_registry_client, schema_str)

            consumer_config = {
                "bootstrap.servers": self._bootstrap_servers,
                "group.id": self._group_id,
                "key.deserializer": StringDeserializer("utf_8"),
                "value.deserializer": avro_deserializer,
                **self._kwargs,
            }
            self._consumer = DeserializingConsumer(consumer_config)

            topic_list = self._topic if isinstance(self._topic, list) else [self._topic]

            if self._seek_to_end:

                def seek_to_end_assign(consumer, partitions):
                    for p in partitions:
                        high_offset = consumer.get_watermark_offsets(p)[1]
                        p.offset = high_offset
                    consumer.assign(partitions)

                self._consumer.subscribe(topic_list, on_assign=seek_to_end_assign)
            else:
                self._consumer.subscribe(topic_list)

        return self._consumer

    def poll(self, timeout: float = 1.0):
        """
        Poll for a message.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Message object or None if no message available
        """
        msg = self.consumer.poll(timeout)
        if msg is None:
            return None

        if msg.error():
            logger.error(f"Consumer error: {msg.error()}")
            return None

        return msg

    def commit(self) -> None:
        """Commit current offsets."""
        self.consumer.commit()

    def commit_offsets(self, offsets: list[TopicPartition]) -> None:
        """
        Commit specific offsets.

        Args:
            offsets: List of TopicPartition with offsets to commit
        """
        self.consumer.commit(offsets=offsets)

    def close(self) -> None:
        """Close the consumer."""
        if self._consumer:
            self._consumer.close()
            self._consumer = None
