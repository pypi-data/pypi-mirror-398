import json
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from aiokafka.helpers import create_ssl_context

from infrastructure.driven_adapters.logging.logger_config import LoggerConfig


class KafkaProducerAdapter:
    """Asynchronous Kafka producer service."""

    def __init__(self, kafka_config):
        """Initialize Kafka producer service.

        Args:
            bootstrap_servers: Kafka broker addresses.
            output_topic: Topic for sending agent responses.
        """
        self.kafka_config = kafka_config

        self.producer: Optional[AIOKafkaProducer] = None
        self._started = False
        self.logger = LoggerConfig().get_logger(self.__class__.__name__)

    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._started:
            return

        self.logger.info("Starting Kafka producer...")

        try:
            producer_args = {
                **self.kafka_config,
                "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
                "ssl_context": create_ssl_context()
            }
            self.producer = AIOKafkaProducer(**producer_args)

            await self.producer.start()
            self._started = True

            self.logger.info("Kafka producer started successfully")

        except KafkaError as e:
            self.logger.error("Kafka error starting producer: %s", e)
            raise
        except Exception as e:
            self.logger.error("Unexpected error starting producer: %s", e)
            raise

    async def send_message(self,
                           topic_name: str,
                           message: Dict[str, Any],
                           headers) -> None:
        """Send a message to Kafka topic.

        Args:
            message: Message dictionary to send.

        Raises:
            Exception: If sending fails.
        """
        if not self._started or self.producer is None:
            await self.start()

        try:
            self.logger.info("Sending message to topic '%s'", topic_name)
            if self.producer is not None:
                await self.producer.send_and_wait(topic_name, value=message,
                                                  headers=headers)

            self.logger.info("Message sent successfully")

        except Exception as e:
            self.logger.error("Error sending message to Kafka: %s", e)
            raise

    async def stop(self) -> None:
        """Stop the Kafka producer gracefully."""
        if not self._started:
            return

        self.logger.info("Stopping Kafka producer...")

        if self.producer is not None:
            try:
                await self.producer.stop()
                self._started = False
                self.logger.info("Kafka producer stopped successfully")

            except Exception as e:
                self.logger.error("Error stopping producer: %s", e)
