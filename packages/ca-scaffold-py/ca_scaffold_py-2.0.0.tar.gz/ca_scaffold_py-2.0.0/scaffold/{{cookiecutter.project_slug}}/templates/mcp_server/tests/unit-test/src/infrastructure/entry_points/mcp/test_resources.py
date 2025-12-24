from typing import List
from unittest.mock import AsyncMock, call

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel.helper_types import ReadResourceContents

from src.applications.settings.container import Container
from src.infrastructure.entry_points.mcp import resources


@pytest.fixture(name="mock_mcp")
def fixture_mock_mcp():
    return AsyncMock(spec=FastMCP)


@pytest.fixture(name="mock_resource_usecase")
def fixture_mock_resource_usecase():
    usecase = AsyncMock()
    usecase.get_available_folders.return_value = [
        "ai", "ml", "nlp"
    ]
    usecase.get_topic_papers.return_value = "Paper details"
    return usecase


@pytest.mark.asyncio
async def test_bind_resources_registers_two_resources(mock_mcp):
    resources.bind_resources(mock_mcp)

    assert hasattr(mock_mcp, "resource")
    assert callable(mock_mcp.resource)
    assert (
        mock_mcp.resource.__dict__["_mock_call_count"] == 2
    )
    assert call("papers://folders") in (
        mock_mcp.resource.__dict__["_mock_call_args_list"]
    )
    assert call("papers://{topic}") in (
        mock_mcp.resource.__dict__["_mock_call_args_list"]
    )


@pytest.mark.asyncio
async def test_get_available_folders_returns_list_with_folders(
        mock_resource_usecase):
    container = Container()
    mcp = FastMCP()
    with container.resource_usecase.override(
            mock_resource_usecase):
        container.wire(modules=[resources])
        resources.bind_resources(mcp)

        result: List[ReadResourceContents] = (
            await mcp.read_resource("papers://folders")
        )

        assert isinstance(result, list)
        assert "ai" in result[0].content


@pytest.mark.asyncio
async def test_get_topic_papers_returns_paper_details(
        mock_resource_usecase):
    container = Container()
    mcp = FastMCP()

    with container.resource_usecase.override(
            mock_resource_usecase):
        container.wire(modules=[resources])
        resources.bind_resources(mcp)

        result: List[ReadResourceContents] = (
            await mcp.read_resource("papers://ai")
        )

        assert isinstance(result, list)
        assert "Paper details" in result[0].content
