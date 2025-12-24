from abc import ABC, abstractmethod

class ResourceRepository(ABC):
    @abstractmethod
    async def get_available_folders(self) -> str:
        raise NotImplementedError("This method should be implemented in a subclass.")

    @abstractmethod
    async def get_topic_papers(self, topic: str) -> str:
        raise NotImplementedError("This method should be implemented in a subclass.")
