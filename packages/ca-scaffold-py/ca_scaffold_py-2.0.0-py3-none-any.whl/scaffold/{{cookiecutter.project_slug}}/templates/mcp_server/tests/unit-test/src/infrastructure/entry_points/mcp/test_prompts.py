import pytest

from mcp.server.fastmcp import FastMCP

from src.infrastructure.entry_points.mcp.prompts import bind_prompts


@pytest.fixture(name="mock_mcp")
def fixture_mock_mcp(mocker):
    mock = mocker.Mock(spec=FastMCP)
    mock.prompt.return_value = lambda func: func
    return mock


@pytest.fixture(name="mock_prompt_usecase")
def fixture_mock_prompt_usecase(mocker):
    usecase = mocker.AsyncMock()
    usecase.generate_search_prompt.return_value = (
        "Search prompt for topic"
    )
    return usecase


@pytest.fixture(name="mock_container", autouse=True)
def fixture_mock_container(mocker, mock_prompt_usecase):
    container = mocker.patch(
        "src.infrastructure.entry_points.mcp.prompts.Container"
    )
    container.prompt_usecase = mock_prompt_usecase
    return container


def test_bind_prompts_registers_decorator(
    mock_mcp
):
    bind_prompts(mock_mcp)
    assert mock_mcp.prompt.called


@pytest.mark.asyncio
async def test_generate_search_prompt_with_defaults(
    mock_mcp,
    mock_prompt_usecase
):
    decorated_functions = []
    mock_mcp.prompt.return_value = (
        lambda func: decorated_functions.append(func) or func
    )

    bind_prompts(mock_mcp, prompt_usecase=mock_prompt_usecase)

    assert len(decorated_functions) == 1
    prompt_func = decorated_functions[0]

    result = await prompt_func(topic="AI")
    assert result == "Search prompt for topic"
    mock_prompt_usecase.generate_search_prompt.assert_called_once_with(
        topic="AI", num_papers=5
    )


@pytest.mark.asyncio
async def test_generate_search_prompt_with_custom_num_papers(
    mock_mcp,
    mock_prompt_usecase
):
    decorated_functions = []
    mock_mcp.prompt.return_value = (
        lambda func: decorated_functions.append(func) or func
    )

    bind_prompts(mock_mcp, prompt_usecase=mock_prompt_usecase)

    assert len(decorated_functions) == 1
    prompt_func = decorated_functions[0]

    result = await prompt_func(topic="ML", num_papers=10)
    assert result == "Search prompt for topic"
    args = mock_prompt_usecase.generate_search_prompt.call_args
    assert args[1]["topic"] == "ML"
    assert args[1]["num_papers"] == 10
