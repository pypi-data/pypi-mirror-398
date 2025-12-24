from abc import ABC, abstractmethod

class PromptRepository(ABC):
    @abstractmethod
    async def generate_search_prompt(self, topic: str, num_papers: int) -> str:
        raise NotImplementedError("This method should be implemented in a subclass.")
