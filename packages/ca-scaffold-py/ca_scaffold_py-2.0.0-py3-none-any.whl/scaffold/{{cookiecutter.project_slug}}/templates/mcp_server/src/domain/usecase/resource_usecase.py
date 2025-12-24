from typing import List
from src.domain.model.paper.gateway.resource_repository import (
    ResourceRepository
)


class ResourceUseCase:
    def __init__(self, resource_repository: ResourceRepository):
        self.resource_repository = resource_repository

    async def get_available_folders(self) -> List[str]:
        """
        List all available topic folders in the papers directory.

        This resource provides a simple list of all available topic folders.
        """
        return await self.resource_repository.get_available_folders()

    async def get_topic_papers(self, topic: str) -> str:
        """
        Get detailed information about papers on a specific topic.

        Args:
            topic: The research topic to retrieve papers for
        """

        return await self.resource_repository.get_topic_papers(topic)
