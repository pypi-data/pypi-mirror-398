import logging
import asyncio
from typing import Optional, Dict
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaConnectionError
from aiokafka.structs import ConsumerRecord
from aiokafka.helpers import create_ssl_context
from tenacity import (retry,
                      stop_never,
                      retry_if_exception_type,
                      before_sleep_log,
                      wait_exponential)

from infrastructure.driven_adapters.logging.logger_config import LoggerConfig
from infrastructure.entry_points.kafka.handlers.base_handler import (
    BaseKafkaHandler
)




class KafkaConsumerAdapter:
    """Asynchronous Kafka consumer service with at-most-once semantics."""

    def __init__(self,
                 kafka_config: dict,
                 message_handler: BaseKafkaHandler):
        """Initialize Kafka consumer service.

        Args:
            kafka_config: Kafka configuration dictionary.
            message_handler: Handler for processing messages.
        """
        self.logger = LoggerConfig().get_logger(self.__class__.__name__)
        self.input_topic = kafka_config.get("input_topic")
        self.max_concurrent_messages = kafka_config.get(
            "max_concurrent_messages",
            10
        )
        self.max_retry_messages = kafka_config.get("max_retry_messages", 3)
        self.kafka_args = self._get_consumer_args(kafka_config)
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self.message_handler = message_handler

    @staticmethod
    def _get_consumer_args(kafka_config: dict) -> dict:
        args = kafka_config.copy()
        del args["input_topic"]
        del args["max_concurrent_messages"]
        del args["max_retry_messages"]
        args["ssl_context"] = create_ssl_context()
        return args

    @staticmethod
    def _parse_headers(headers) -> Dict[str, str]:
        """Parse Kafka headers to dictionary.

        Converts from Sequence[tuple[str, bytes]] to Dict[str, str].

        Args:
            headers: Kafka message headers in format
                Sequence[tuple[str, bytes]].

        Returns:
            Dictionary with header keys and decoded values.
        """
        if not headers:
            return {}

        parsed_headers = {}
        for key, value in headers:
            try:
                if isinstance(value, bytes):
                    parsed_headers[key] = value.decode("utf-8")
                else:
                    parsed_headers[key] = str(value)
            except UnicodeDecodeError:
                parsed_headers[key] = str(value)
        return parsed_headers

    async def start(self) -> None:
        """Start the Kafka consumer and begin consuming messages."""
        self.logger.info("Starting Kafka consumer service...")

        try:
            await self._connect_and_consume()
        except Exception as e:
            self.logger.error("Failed to start Kafka consumer: %s", e)
            raise

    @retry(
        retry=retry_if_exception_type(KafkaConnectionError),
        stop=stop_never,
        wait=wait_exponential(multiplier=4, min=4, max=10),
        before_sleep=before_sleep_log(LoggerConfig().get_logger('Kafka_connection'), logging.WARNING),
    )
    async def _connect_and_consume(self) -> None:
        """Connect to Kafka and start consuming messages with retry logic."""
        try:
            self.consumer = AIOKafkaConsumer(self.input_topic,
                                             **self.kafka_args)

            self.logger.info("Attempting to connect to Kafka...")
            await self.consumer.start()

            self.logger.info("Successfully connected to Kafka")
            self._running = True

            await self._consume_messages()

        except KafkaConnectionError:
            if self.consumer is not None:
                try:
                    await self.consumer.stop()
                except Exception:
                    pass
                self.consumer = None
            raise
        except (KafkaError, Exception) as e:
            self.logger.error("Non-retriable error occurred: %s", e)
            if self.consumer is not None:
                try:
                    await self.consumer.stop()
                except Exception:
                    pass
                self.consumer = None
            raise

    async def _consume_messages(self) -> None:
        """Consume and process messages with at-most-once semantics."""
        if self.consumer is None:
            self.logger.error("Kafka consumer is not initialized.")
            return

        semaphore = asyncio.Semaphore(self.max_concurrent_messages)

        try:
            async for message in self.consumer:
                asyncio.create_task(
                    self._process_with_semaphore(message, semaphore)
                )
        except Exception as e:
            self.logger.error("Error consuming messages: %s", e)
            raise

    async def _process_with_semaphore(self,
                                      msg: ConsumerRecord,
                                      semaphore: asyncio.Semaphore) -> None:
        """Control concurrency with semaphore."""
        async with semaphore:
            await self._process_message_with_retries(msg)

    async def _process_message_with_retries(self, msg: ConsumerRecord) -> None:
        """Process a message with local retry logic."""
        self.logger.info("Processing message from topic %s partition %d offset %d",
                    msg.topic, msg.partition, msg.offset)
        parsed_headers = self._parse_headers(msg.headers)
        self.logger.debug("Parsed headers: %s", parsed_headers)
        for attempt in range(1, self.max_retry_messages + 1):
            try:
                if not isinstance(msg.value, bytes):
                    raise ValueError("Message value is not of type bytes")
                await self.message_handler.handle(msg.value, parsed_headers)
                self.logger.info("Successfully processed message at offset %d",
                            msg.offset)
                return
            except Exception as e:
                if attempt < self.max_retry_messages:
                    self.logger.warning(
                        "Error processing offset %d (attempt %d/%d): %s",
                        msg.offset, attempt, self.max_retry_messages, str(e)
                    )
                    await asyncio.sleep(0.5)
                else:
                    self.logger.error(
                        "Max retries reached for offset %d. "
                        "Message will be lost. Error: %s",
                        msg.offset, str(e)
                    )

    async def stop(self) -> None:
        """Stop the Kafka consumer gracefully."""
        self.logger.info("Stopping Kafka consumer service...")
        self._running = False

        if self.consumer is not None:
            try:
                await self.consumer.stop()
                self.logger.info("Kafka consumer stopped successfully")

            except Exception as e:
                self.logger.error("Error stopping consumer: %s", e)

    def is_running(self) -> bool:
        """Check if consumer is running.

        Returns:
            True if consumer is running, False otherwise.
        """
        return self._running
