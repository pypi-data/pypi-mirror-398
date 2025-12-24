from abc import ABC, abstractmethod
from typing import AsyncIterator

class CollaborateAdapter(ABC):
    @abstractmethod
    async def discover_agent(self, agent_url: str) -> dict:
        """Obtiene el agent card de otro agente"""

    @abstractmethod
    async def send_to_agent(self, agent_url: str, message: str) -> dict:
        """Envía mensaje síncrono a otro agente"""

    @abstractmethod
    async def stream_from_agent(self, agent_url: str, message: str) -> AsyncIterator:
        """Recibe respuesta streaming de otro agente"""