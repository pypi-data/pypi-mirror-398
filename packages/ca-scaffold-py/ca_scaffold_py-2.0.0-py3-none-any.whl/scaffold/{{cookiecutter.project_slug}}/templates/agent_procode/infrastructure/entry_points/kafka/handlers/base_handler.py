import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict


logger = logging.getLogger(__name__)


class BaseKafkaHandler(ABC):
    """Base class for Kafka message handlers."""

    @abstractmethod
    async def handle(self, message_value: bytes, message_headers: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Kafka message.

        Args:
            message_value: Raw message bytes from Kafka.

        Returns:
            Dictionary with processing result.

        Raises:
            Exception: If message processing fails.
        """

    def decode_message(self, message_value: bytes) -> Dict[str, Any]:
        """Decode message from bytes to dictionary.

        Args:
            message_value: Raw message bytes.

        Returns:
            Decoded message as dictionary.

        Raises:
            json.JSONDecodeError: If message is not valid JSON.
        """
        try:
            message_str = message_value.decode("utf-8")
            return json.loads(message_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode message bytes: {e}")
            raise

    def validate_required_fields(
        self,
        message: Dict[str, Any],
        required_fields: list[str]
    ) -> None:
        """Validate that required fields are present in message.

        Args:
            message: Decoded message dictionary.
            required_fields: List of required field names.

        Raises:
            ValueError: If any required field is missing.
        """
        missing_fields = [
            field for field in required_fields
            if field not in message
        ]
        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
