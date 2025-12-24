from a2a.client import A2AClient as A2ALibClient
from a2a.types import SendMessageResponse
from typing import AsyncIterator

class A2AClientWrapper:
    """Wrapper para el cliente A2A de la librería oficial"""

    def __init__(self, client: A2ALibClient):
        self.client = client

    @classmethod
    async def create(cls, agent_url: str) -> 'A2AClientWrapper':
        """Crea un cliente A2A conectado a un agente externo"""
        client = A2ALibClient(agent_url)
        return cls(client)

    async def send_message(self, message: str) -> SendMessageResponse:
        """Envía mensaje síncrono según protocolo A2A"""
        return await self.client.send_message(message)

    async def stream_message(self, message: str) -> AsyncIterator:
        """Envía mensaje con respuesta streaming según protocolo A2A"""
        async for event in self.client.stream_message(message):
            yield event

    async def close(self):
        """Cierra la conexión del cliente"""
        if hasattr(self.client, 'close'):
            await self.client.close()