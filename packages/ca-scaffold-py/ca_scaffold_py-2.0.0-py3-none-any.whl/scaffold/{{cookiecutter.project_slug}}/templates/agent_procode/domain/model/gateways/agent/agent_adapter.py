from abc import abstractmethod, ABC
from typing import Optional, Dict, Any


class AgentAdapter(ABC):

    @abstractmethod
    async def interact(self, prompt: str) -> Optional[Dict[str, Any]]:
        """" Interact with the agent using the given prompt. """

    @abstractmethod
    def create_prompt(self, message) -> str:
        """ Create a prompt from the given message. """
