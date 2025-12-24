from unittest.mock import AsyncMock, patch
import pytest

from src.domain.model.paper.gateway.resource_repository import ResourceRepository
from src.domain.usecase.resource_usecase import ResourceUseCase

@pytest.fixture(name='mock_resource_repository')
def setup_mock_resource_repository():
    return AsyncMock(spec=ResourceRepository)


@pytest.mark.asyncio
@patch("src.domain.model.paper.gateway.resource_repository.ResourceRepository.__abstractmethods__", set())
async def test_abstract_resource_repository():
    # Create an instance of the abstract class,
    # it should show an error but with patch it will be instantiated
    resource_repository = ResourceRepository()

    with pytest.raises(NotImplementedError) as exc_create:
        await resource_repository.get_available_folders()

    with pytest.raises(NotImplementedError) as exc_create:
        await resource_repository.get_topic_papers(topic="test")

    assert isinstance(exc_create.value, NotImplementedError)

@pytest.mark.asyncio
async def test_get_available_folders(mock_resource_repository):
    # Mock the get_available_folders method
    mock_resource_repository.get_available_folders.return_value = ["folder1", "folder2"]

    usecase = ResourceUseCase(mock_resource_repository)

    result = await usecase.get_available_folders()
    # Verify the use case calls the repository method
    mock_resource_repository.get_available_folders.assert_called_once()
    assert result == ["folder1", "folder2"]

@pytest.mark.asyncio
async def test_get_topic_papers(mock_resource_repository):
    # Mock the get_topic_papers method
    mock_resource_repository.get_topic_papers.return_value = "Papers on topic"

    usecase = ResourceUseCase(mock_resource_repository)

    result = await usecase.get_topic_papers(topic="test topic")

    # Verify the use case calls the repository method
    mock_resource_repository.get_topic_papers.assert_called_once_with("test topic")
    assert result == "Papers on topic"
