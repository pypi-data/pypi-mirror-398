from abc import ABC, abstractmethod
from typing import List

class PaperRepository(ABC):
    @abstractmethod
    async def search_papers(self, topic: str, max_results: int = 5) -> List[str]:
        raise NotImplementedError("This method should be implemented in a subclass.")

    @abstractmethod
    async def extract_info(self, paper_id: str) -> str:
        raise NotImplementedError("This method should be implemented in a subclass.")
