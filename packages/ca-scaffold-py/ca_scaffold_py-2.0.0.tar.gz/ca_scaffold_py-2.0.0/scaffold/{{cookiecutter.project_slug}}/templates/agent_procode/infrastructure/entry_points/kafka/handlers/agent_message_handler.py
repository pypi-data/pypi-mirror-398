import json
from typing import Any, Dict

from domain.usecase.agent_interaction_usecase import AgentInteractionUseCase
from infrastructure.driven_adapters.kafka_producer_adapter import KafkaProducerAdapter
from infrastructure.driven_adapters.logging.logger_config import LoggerConfig
from infrastructure.entry_points.kafka.handlers.base_handler import (
    BaseKafkaHandler
)




class AgentMessageHandler(BaseKafkaHandler):
    """Handler for processing agent messages from Kafka."""

    def __init__(self,
                 agent_interaction_use_case: AgentInteractionUseCase,
                 kafka_producer: KafkaProducerAdapter):
        """Initialize handler with dependencies.

        Args:
            process_agent_use_case: Use case for processing messages.
            kafka_producer: Kafka producer for sending responses.
        """
        self.agent_interaction_use_case = agent_interaction_use_case
        self.kafka_producer = kafka_producer
        self.logger = LoggerConfig().get_logger(self.__class__.__name__)

    @staticmethod
    def _serialize_headers(headers: Dict[str, str]) -> list[tuple[str, bytes]]:
        """Serialize headers dictionary to Kafka format.

        Converts from Dict[str, str] to list[tuple[str, bytes]].

        Args:
            headers: Dictionary with header keys and string values.

        Returns:
            List of tuples in Kafka header format.
        """
        return [(key, value.encode("utf-8")) for key, value in headers.items()]

    async def handle(self,
                     message_value: bytes,
                     message_headers: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Kafka message with agent.

        Args:
            message_value: Raw message bytes from Kafka.

        Returns:
            Dictionary with processing result.

        Raises:
            Exception: If message processing fails.
        """
        try:
            message = self.decode_message(message_value)

            self.logger.info("Processing agent message: %s",
                        json.dumps(message, indent=2))
            metadata = message.get("metadata", {})
            data = message.get("data", {})

            conversation_id = metadata.get("MessageIdentifier")
            user_message = data["MessageContent"]


            agent_response = await self.agent_interaction_use_case.interact_with_agent(
                user_message
            )

            self.logger.info("Agent response status: %s for conversation: %s",
                        agent_response.status)

            response_message = {
                "data": {
                    "Messages": [
                        {
                            "MessageType": "text",
                            "MessageContent": agent_response
                        }
                    ]
                },
                "metadata": metadata
            }
            topic = message_headers.get("ReplyTo", "")
            if topic:
                del message_headers["ReplyTo"]

            headers = self._serialize_headers(message_headers)
            await self.kafka_producer.send_message(topic, response_message,
                                                   headers=headers)

            return {
                "status": "processed",
                "conversation_id": conversation_id
            }

        except Exception as e:
            self.logger.error("Error handling agent message: %s", e)
            raise
