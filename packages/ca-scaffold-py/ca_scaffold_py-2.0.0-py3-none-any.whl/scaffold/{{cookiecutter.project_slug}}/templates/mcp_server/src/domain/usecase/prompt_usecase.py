from src.domain.model.paper.gateway.prompt_repository import PromptRepository


class PromptUseCase:
    def __init__(self, prompt_repository: PromptRepository):
        self.prompt_repository = prompt_repository

    async def generate_search_prompt(self,
                                     topic: str,
                                     num_papers: int = 5) -> str:
        """Generate a prompt for Claude to find and discuss academic
        papers on a specific topic.
        """
        return await self.prompt_repository.generate_search_prompt(topic,
                                                                   num_papers)
