import logging
import asyncio
import aiohttp
from src.infrastructure.driven_adapters.aio_http_adapter.errors import (
    AioHttpError
)


class AiohttpAdapter:
    """Adapter for HTTP requests using aiohttp."""

    def __init__(self):
        """Initializes the AiohttpAdapter with a session and logger."""
        self.session = aiohttp.ClientSession()
        self.logger = logging.getLogger(__name__)

    async def post(self, url, payload, headers, timeout):
        """Sends a POST request using aiohttp.

        Args:
            url (str): The URL to send the request to.
            payload (dict): The JSON payload to send.
            headers (dict): The headers to include in the request.
            timeout (int): The request timeout in seconds.

        Returns:
            tuple: (status code, response content, response body as dict)

        Raises:
            aiohttp.ClientError: If an HTTP client error occurs.
            aiohttp.ContentTypeError: If the response is not JSON.
        """
        try:
            async with self.session.post(url,
                                         json=payload,
                                         headers=headers,
                                         timeout=timeout) as response:
                body = await response.json()
                return response.status, body
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.logger.error("aiohttp error occurred: %s", str(e))
            raise AioHttpError("Aiohttp error occurred") from e

    async def get(self, url, params, headers, timeout):
        """Sends a GET request using aiohttp.

        Args:
            url (str): The URL to send the request to.
            params (dict): The query parameters to send.
            headers (dict): The headers to include in the request.
            timeout (int): The request timeout in seconds.

        Returns:
            tuple: (status code, response body as dict)

        Raises:
            aiohttp.ClientError: If an HTTP client error occurs.
            aiohttp.ContentTypeError: If the response is not JSON.
        """
        try:
            async with self.session.get(url,
                                        params=params,
                                        headers=headers,
                                        timeout=timeout) as response:
                body = await response.json()
                return response.status, body
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.logger.error("aiohttp error occurred: %s", str(e))
            raise AioHttpError("Aiohttp error occurred") from e
