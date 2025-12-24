from unittest.mock import AsyncMock, patch
import pytest

from src.domain.model.paper.gateway.prompt_repository import PromptRepository
from src.domain.usecase.prompt_usecase import PromptUseCase

@pytest.fixture(name='mock_prompt_repository')
def setup_mock_prompt_repository():
    return AsyncMock(spec=PromptRepository)


@pytest.mark.asyncio
@patch("src.domain.model.paper.gateway.prompt_repository.PromptRepository.__abstractmethods__", set())
async def test_abstract_prompt_repository():
    # Create an instance of the abstract class,
    # it should show an error but with patch it will be instantiated
    prompt_repository = PromptRepository()

    with pytest.raises(NotImplementedError) as exc_create:
        await prompt_repository.generate_search_prompt(topic="test", num_papers=1)

    assert isinstance(exc_create.value, NotImplementedError)

@pytest.mark.asyncio
async def test_generate_search_prompt(mock_prompt_repository):
    # Mock the generate_search_prompt method
    mock_prompt_repository.generate_search_prompt.return_value = "Generated prompt"

    usecase = PromptUseCase(mock_prompt_repository)

    result = await usecase.generate_search_prompt(topic="test topic", num_papers=5)
    # Verify the use case calls the repository method
    mock_prompt_repository.generate_search_prompt.assert_called_once_with("test topic", 5)
    assert result == "Generated prompt"
