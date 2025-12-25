"""
Asynchronous Avro producer using confluent-kafka with asyncio.

Features:
- Non-blocking produce with async/await
- Background asyncio task for polling
- Suitable for async frameworks (LangGraph, FastAPI)

Usage:
    from investify_utils.kafka import AsyncAvroProducer

    producer = AsyncAvroProducer(
        topic="my-topic",
        subject="my-topic-value",
        schema_registry_url="http://localhost:8081",
        bootstrap_servers="localhost:9092",
    )

    # In async context
    await producer.produce(key="key1", value={"field": "value"})
    producer.close()
"""

import asyncio
import logging
from typing import Callable

from confluent_kafka import KafkaException, SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient, record_subject_name_strategy
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer

logger = logging.getLogger(__name__)


class AsyncAvroProducer:
    """
    Asynchronous Avro producer for async frameworks.

    Args:
        topic: Kafka topic name
        subject: Schema Registry subject name
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
        self._poll_task: asyncio.Task | None = None

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

            # Start background polling task
            self._poll_task = asyncio.create_task(self._poll_loop())

        return self._producer

    async def _poll_loop(self) -> None:
        """Background task for polling delivery callbacks."""
        while True:
            self._producer.poll(0.1)
            await asyncio.sleep(0.1)

    async def produce(
        self,
        value: dict,
        key: str | None = None,
        on_delivery: Callable | None = None,
    ) -> asyncio.Future:
        """
        Produce a message asynchronously.

        Args:
            value: Message value (dict matching Avro schema)
            key: Optional message key
            on_delivery: Optional callback(err, msg) for delivery confirmation

        Returns:
            Future that resolves to the delivered message
        """
        loop = asyncio.get_running_loop()
        result = loop.create_future()

        def ack(err, msg):
            if err:
                loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
            else:
                loop.call_soon_threadsafe(result.set_result, msg)
            if on_delivery:
                loop.call_soon_threadsafe(on_delivery, err, msg)

        self.producer.produce(self.topic, key=key, value=value, on_delivery=ack)
        return await result

    def flush(self, timeout: float = 10.0) -> int:
        """
        Wait for all messages to be delivered.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Number of messages still in queue
        """
        if self._producer:
            return self._producer.flush(timeout)
        return 0

    def close(self) -> None:
        """Cancel polling task and flush pending messages."""
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        if self._producer:
            self._producer.flush()
            self._producer = None
