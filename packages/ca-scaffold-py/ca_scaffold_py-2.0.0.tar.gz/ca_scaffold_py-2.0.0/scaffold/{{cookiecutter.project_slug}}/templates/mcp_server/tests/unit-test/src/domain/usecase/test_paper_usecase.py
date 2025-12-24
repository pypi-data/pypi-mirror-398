from unittest.mock import AsyncMock, patch
import pytest

from src.domain.model.paper.gateway.paper_repository import PaperRepository
from src.domain.usecase.paper_usecase import PaperUseCase

@pytest.fixture(name='mock_tool_repository')
def setup_mock_tool_repository():
    return AsyncMock(spec=PaperRepository)

@pytest.mark.asyncio
@patch("src.domain.model.paper.gateway.paper_repository.PaperRepository.__abstractmethods__", set())
async def test_abstract_tool_repository():
    # Create an instance of the abstract class,
    # it should show an error but with patch it will be instantiated
    tool_repository = PaperRepository()

    with pytest.raises(NotImplementedError) as exc_create:
        await tool_repository.search_papers(topic="test", max_results=5)

    with pytest.raises(NotImplementedError) as exc_create:
        await tool_repository.extract_info(paper_id="article123")

    assert isinstance(exc_create.value, NotImplementedError)

@pytest.mark.asyncio
async def test_search_papers(mock_tool_repository):
    # Mock the search_papers method
    mock_tool_repository.search_papers.return_value = [
        "paper1",
        "paper2"
    ]

    usecase = PaperUseCase(mock_tool_repository)

    result = await usecase.search_papers(topic="test topic", max_results=5)
    # Verify the use case calls the repository method
    mock_tool_repository.search_papers.assert_called_once_with("test topic", 5)
    assert result == ["paper1", "paper2"]

@pytest.mark.asyncio
async def test_extract_info(mock_tool_repository):
    # Mock the extract_info method
    mock_tool_repository.extract_info.return_value = "Paper information"

    usecase = PaperUseCase(mock_tool_repository)

    result = await usecase.extract_info(paper_id="paper1")

    # Verify the use case calls the repository method
    mock_tool_repository.extract_info.assert_called_once_with("paper1")
    assert result == "Paper information"
