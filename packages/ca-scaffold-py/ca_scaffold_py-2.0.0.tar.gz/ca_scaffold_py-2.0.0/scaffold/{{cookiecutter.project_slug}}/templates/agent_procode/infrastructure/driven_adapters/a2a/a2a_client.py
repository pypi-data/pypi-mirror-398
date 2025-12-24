from typing import AsyncIterator

import httpx

from domain.model.gateways.agent.collaborate_adapter import CollaborateAdapter
from infrastructure.entry_points.a2a.a2a_client_wrapper import A2AClientWrapper


class A2AClient(CollaborateAdapter):

    def __init__(self) -> None:
        self.clients = {}

    async def discover_agent(self, agent_url: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{agent_url}/.well-known/agent")
            response.raise_for_status()
            return response.json()

    async def send_to_agent(self, agent_url: str, message: str) -> dict:
        client = await self._get_or_create_client(agent_url)
        response = await client.send_message(message)
        return self._extract_response_content(response)


    async def stream_from_agent(self, agent_url: str, message: str) -> AsyncIterator:
        client = await self._get_or_create_client(agent_url)
        async for event in client.stream_message(message):
            yield self._extract_stream_content(event)

    async def _get_or_create_client(self, agent_url: str) -> A2AClientWrapper:
        if agent_url not in self.clients:
            self.clients[agent_url] = await A2AClientWrapper.create(agent_url)
        return self.clients[agent_url]

    @staticmethod
    def _extract_response_content(response) -> dict:
        # Convertir respuesta A2A a formato interno
        if hasattr(response, 'message'):
            parts = response.message.get('parts', [])
            if parts and parts[0].get('kind') == 'text':
                return {"content": parts[0].get('text')}
        return {"content": str(response)}

    @staticmethod
    def _extract_stream_content(event) -> dict:
        """Extrae contenido de eventos de streaming A2A"""
        if hasattr(event, 'data') and hasattr(event.data, 'delta'):
            return {"content": event.data.delta}
        return {"content": ""}