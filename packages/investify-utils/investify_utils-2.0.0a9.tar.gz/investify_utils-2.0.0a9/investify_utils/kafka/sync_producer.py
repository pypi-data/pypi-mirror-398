"""
Synchronous Avro producer using confluent-kafka.

Features:
- Avro serialization with Schema Registry
- Background polling thread for delivery callbacks
- Thread-safe produce operations

Usage:
    from investify_utils.kafka import AvroProducer

    producer = AvroProducer(
        topic="my-topic",
        subject="my-topic-value",
        schema_registry_url="http://localhost:8081",
        bootstrap_servers="localhost:9092",
    )

    producer.produce(key="key1", value={"field": "value"})
    producer.flush()
    producer.close()
"""

import logging
import threading
from typing import Callable

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient, record_subject_name_strategy
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer

logger = logging.getLogger(__name__)


class AvroProducer:
    """
    Synchronous Avro producer with background polling.

    Args:
        topic: Kafka topic name
        subject: Schema Registry subject name (usually "{topic}-value")
        schema_registry_url: Schema Registry URL
        bootstrap_servers: Kafka bootstrap servers
        **kwargs: Additional Kafka producer config
    """

    def __init__(
        self,
        topic: str,
        subject: str,
        schema_registry_url: str,
        bootstrap_servers: str,
        **kwargs,
    ):
        self.topic = topic
        self._schema_registry_url = schema_registry_url
        self._bootstrap_servers = bootstrap_servers
        self._subject = subject
        self._kwargs = kwargs
        self._producer: SerializingProducer | None = None
        self._shutdown_event: threading.Event | None = None
        self._poll_thread: threading.Thread | None = None

    @property
    def producer(self) -> SerializingProducer:
        """Lazy producer initialization."""
        if self._producer is None:
            schema_registry_client = SchemaRegistryClient({"url": self._schema_registry_url})
            registered_schema = schema_registry_client.get_latest_version(self._subject)
            schema_str = registered_schema.schema.schema_str

            avro_serializer = AvroSerializer(
                schema_registry_client,
                schema_str,
                conf={
                    "auto.register.schemas": False,
                    "subject.name.strategy": record_subject_name_strategy,
                },
            )

            producer_config = {
                "bootstrap.servers": self._bootstrap_servers,
                "key.serializer": StringSerializer("utf_8"),
                "value.serializer": avro_serializer,
                **self._kwargs,
            }
            self._producer = SerializingProducer(producer_config)

            # Start background polling thread
            self._shutdown_event = threading.Event()
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()

        return self._producer

    def _poll_loop(self) -> None:
        """Background thread for polling delivery callbacks."""
        while not self._shutdown_event.is_set():
            self._producer.poll(0.1)
            self._shutdown_event.wait(0.1)

    def produce(
        self,
        value: dict,
        key: str | None = None,
        on_delivery: Callable | None = None,
    ) -> None:
        """
        Produce a message to Kafka.

        Args:
            value: Message value (dict matching Avro schema)
            key: Optional message key
            on_delivery: Optional callback(err, msg) for delivery confirmation
        """
        try:
            self.producer.produce(self.topic, key=key, value=value, on_delivery=on_delivery)
        except Exception as e:
            logger.error(f"Failed to produce message: {e!r}")
            raise

    def flush(self, timeout: float = 10.0) -> int:
        """
        Wait for all messages to be delivered.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Number of messages still in queue (0 if all delivered)
        """
        return self.producer.flush(timeout)

    def close(self) -> None:
        """Flush pending messages and stop background polling."""
        if self._shutdown_event:
            self._shutdown_event.set()
        if self._producer:
            self._producer.flush()
            self._producer = None
