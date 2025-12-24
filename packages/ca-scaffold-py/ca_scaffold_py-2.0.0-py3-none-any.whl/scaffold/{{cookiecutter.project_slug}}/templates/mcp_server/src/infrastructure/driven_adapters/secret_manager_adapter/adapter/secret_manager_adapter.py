import logging
from typing import Dict
from aiobotocore.session import get_session
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    BotoCoreError
)
from src.infrastructure.driven_adapters.secret_manager_adapter import (
    SecretRetrievalError
)


class SecretManagerAdapter:
    """
    Adapter to retrieve secrets from AWS Secrets Manager
    using aiobotocore for async operations.
    """

    def __init__(self, aws_config):
        """
        Initialize the Secret Manager adapter.

        Args:
            aws_config: AWS configuration parameters
                       (region_name, credentials, etc.)
        """
        self.aws_config = aws_config
        self.logger = logging.getLogger(__name__)
        self._session = get_session()
        self._cached_secrets: Dict[str, str] = {}

    async def get_secret(self, secret_name: str) -> str:
        """
        Asynchronous method to retrieve a secret from AWS Secrets Manager.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            The secret value

        Raises:
            SecretRetrievalError: If secret cannot be retrieved
        """
        try:
            async with self._session.create_client(
                "secretsmanager",
                **self.aws_config
            ) as client:
                self.logger.info("Attempting to retrieve secret: %s",
                                 secret_name)
                response = await client.get_secret_value(SecretId=secret_name)
                if "SecretString" not in response:
                    raise ValueError(
                        f"Secret '{secret_name}' has no string value"
                    )
                secret_value = response["SecretString"]
                self.logger.info(
                    "Successfully retrieved secret: %s", secret_name
                )
                return secret_value
        except (ValueError,
                ClientError,
                NoCredentialsError,
                BotoCoreError) as error:
            error_message = str(error)
            self.logger.error("Failed to retrieve secret '%s': %s",
                              secret_name,
                              error_message)
            raise SecretRetrievalError(
                f"Failed to retrieve secret '{secret_name}': {error_message}"
            ) from error
