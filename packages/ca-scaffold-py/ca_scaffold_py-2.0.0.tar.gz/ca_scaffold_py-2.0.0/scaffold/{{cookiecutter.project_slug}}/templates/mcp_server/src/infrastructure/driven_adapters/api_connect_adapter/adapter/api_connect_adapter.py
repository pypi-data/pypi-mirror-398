import uuid
import json
import logging
from typing import Any, Dict, Optional
from src.infrastructure.driven_adapters.aio_http_adapter import (
    AioHttpError,
    AiohttpAdapter
)
from src.infrastructure.driven_adapters.secret_manager_adapter import (
    SecretManagerAdapter,
    SecretRetrievalError
)
from src.infrastructure.driven_adapters.api_connect_adapter.errors import (
    ApiConnectError
)


class ApiConnectAdapter:
    """class for API Connect adapters with shared functionality."""

    def __init__(self,
                 config: Dict,
                 http_adapter: AiohttpAdapter,
                 secret_manager: SecretManagerAdapter):
        """
        Initialize adapter with shared dependencies.

        Args:
            config: Configuration dictionary with API settings
            http_adapter: HTTP client adapter for making requests
            secret_manager: Secret manager for retrieving credentials
        """
        self.secret_manager = secret_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.http_adapter = http_adapter
        self.secret_name: str = config.get("api_secret_name", "")
        self.cached_credentials = None

    async def get_client_credentials(self) -> Dict[str, str]:
        """Retrieve client credentials from secret manager."""

        if self.cached_credentials:
            return self.cached_credentials
        try:
            secret = await self.secret_manager.get_secret(self.secret_name)
            json_secret = json.loads(secret)
            self.cached_credentials = {
                "client_id": json_secret.get("client_id"),
                "client_secret": json_secret.get("client_secret")
            }
            return self.cached_credentials
        except (SecretRetrievalError, json.JSONDecodeError) as e:
            self.logger.error("Error fetching client credentials: %s", str(e))
            raise ApiConnectError(
                "Failed to retrieve client credentials"
            ) from e

    async def validate_credentials(self) -> bool:
        """Validate API credentials."""
        if not self.cached_credentials:
            return False
        return True

    def get_default_headers(
        self,
        credentials: Dict[str, str],
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Get default headers for API requests."""
        headers = {
            "client-id": credentials["client_id"],
            "client-secret": credentials["client_secret"],
            "content-type": "application/json",
            "message-id": str(uuid.uuid4())
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers

    async def make_post_request(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generic method to make POST API requests."""
        try:
            credentials = await self.get_client_credentials()
            headers = self.get_default_headers(credentials, additional_headers)
            status, body = await self.http_adapter.post(
                url=endpoint,
                payload=payload,
                headers=headers,
                timeout=10
            )
            return {"status": status, "body": body}
        except AioHttpError as e:
            self.logger.error(
                "Unexpected error in make_post_request for endpoint '%s': %s",
                endpoint,
                str(e)
            )
            raise ApiConnectError(str(e)) from e

    async def make_get_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generic method to make GET API requests."""
        try:
            credentials = await self.get_client_credentials()
            headers = self.get_default_headers(credentials, additional_headers)
            status, body = await self.http_adapter.get(
                url=endpoint,
                params=params or {},
                headers=headers,
                timeout=10
            )
            return {"status": status, "body": body}
        except AioHttpError as e:
            self.logger.error(
                "Unexpected error in make_get_request for endpoint '%s': %s",
                endpoint,
                str(e)
            )
            raise ApiConnectError(str(e)) from e

    async def handle_api_error(self, result: Dict[str, Any]) -> None:
        """Handle API errors and log details."""
        status = result.get("status")
        if status == 200:
            return
        if status == 401:
            self.logger.warning("401 Unauthorized: clearing cache")
            self.cached_credentials = None
        error_msg = f"API error: status={status}"
        errors = result.get("body", {}).get("errors")
        if errors and isinstance(errors, list) and len(errors) > 0:
            code = errors[0].get("code", "")
            detail = errors[0].get("detail", "")
            error_msg += f", code={code}, detail={detail}"

        self.logger.error("API request failed: %s", error_msg)
        raise ApiConnectError(error_msg)
