from typing import List
from src.domain.model.paper.gateway.paper_repository import PaperRepository


class PaperUseCase:
    def __init__(self, paper_repository: PaperRepository):
        self.paper_repository = paper_repository

    async def search_papers(self,
                            topic: str,
                            max_results: int = 5) -> List[str]:

        return await self.paper_repository.search_papers(topic, max_results)

    async def extract_info(self, paper_id: str) -> str:

        return await self.paper_repository.extract_info(paper_id)
