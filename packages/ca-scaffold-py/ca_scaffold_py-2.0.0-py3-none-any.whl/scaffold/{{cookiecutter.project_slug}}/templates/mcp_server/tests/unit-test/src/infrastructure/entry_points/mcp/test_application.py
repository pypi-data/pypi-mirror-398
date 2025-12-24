import pytest

from src.infrastructure.entry_points.mcp.application import (
    lifespan,
    create_application
)


@pytest.fixture(name="mock_fast_mcp")
def fixture_mock_fast_mcp(mocker):
    mock = mocker.MagicMock()
    mock.session_manager.run = mocker.MagicMock()
    mock.session_manager.run.return_value.__aenter__ = (
        mocker.AsyncMock()
    )
    mock.session_manager.run.return_value.__aexit__ = (
        mocker.AsyncMock()
    )
    mock.streamable_http_app = mocker.MagicMock()
    return mock


@pytest.fixture(name="mock_fast_api")
def fixture_mock_fast_api(mocker):
    mock = mocker.MagicMock()
    return mock


@pytest.fixture(name="mock_container")
def fixture_mock_container(mocker):
    mock = mocker.MagicMock()
    mock.config.url_prefix.return_value = "/test"
    mock.config.from_pydantic = mocker.MagicMock()
    mock.wire = mocker.MagicMock()
    return mock


@pytest.fixture(name="mock_tools")
def fixture_mock_tools(mocker):
    mock = mocker.MagicMock()
    mock.bind_tools = mocker.MagicMock()
    return mock


@pytest.fixture(name="mock_resources")
def fixture_mock_resources(mocker):
    mock = mocker.MagicMock()
    mock.bind_resources = mocker.MagicMock()
    return mock


@pytest.fixture(name="mock_prompts")
def fixture_mock_prompts(mocker):
    mock = mocker.MagicMock()
    mock.bind_prompts = mocker.MagicMock()
    return mock


@pytest.mark.asyncio
async def test_lifespan_binds_tools_resources_and_prompts(
    mock_fast_api,
    mock_fast_mcp,
    mock_tools,
    mock_resources,
    mock_prompts,
    mocker
):
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.tools",
        mock_tools
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.resources",
        mock_resources
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.prompts",
        mock_prompts
    )
    async with lifespan(mock_fast_api, mock_fast_mcp):
        pass
    mock_tools.bind_tools.assert_called_once_with(mock_fast_mcp)
    mock_resources.bind_resources.assert_called_once_with(
        mock_fast_mcp
    )
    mock_prompts.bind_prompts.assert_called_once_with(
        mock_fast_mcp
    )


@pytest.mark.asyncio
async def test_lifespan_runs_session_manager(
    mock_fast_api,
    mock_fast_mcp,
    mocker
):
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.tools"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.resources"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.prompts"
    )
    async with lifespan(mock_fast_api, mock_fast_mcp):
        pass
    mock_fast_mcp.session_manager.run.assert_called_once()


def test_create_application_returns_fastapi_instance(
    mock_container,
    mock_fast_mcp,
    mocker
):
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Container",
        return_value=mock_container
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.FastMCP",
        return_value=mock_fast_mcp
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Config"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.set_routes"
    )
    app = create_application()
    assert app is not None
    assert callable(app)


def test_create_application_configures_container(
    mock_container,
    mock_fast_mcp,
    mocker
):
    mock_config = mocker.MagicMock()
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Container",
        return_value=mock_container
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.FastMCP",
        return_value=mock_fast_mcp
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Config",
        return_value=mock_config
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.set_routes"
    )
    create_application()
    mock_container.config.from_pydantic.assert_called_once_with(
        mock_config
    )


def test_create_application_wires_modules(
    mock_container,
    mock_fast_mcp,
    mocker
):
    mock_tools = mocker.MagicMock()
    mock_resources = mocker.MagicMock()
    mock_prompts = mocker.MagicMock()
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Container",
        return_value=mock_container
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.FastMCP",
        return_value=mock_fast_mcp
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Config"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.set_routes"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.tools",
        mock_tools
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.resources",
        mock_resources
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.prompts",
        mock_prompts
    )
    create_application()
    mock_container.wire.assert_called_once_with(
        modules=[mock_tools, mock_resources, mock_prompts]
    )


def test_create_application_creates_fastmcp_with_correct_params(
    mock_container,
    mocker
):
    mock_fastmcp_class = mocker.patch(
        "src.infrastructure.entry_points.mcp.application.FastMCP"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Container",
        return_value=mock_container
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Config"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.set_routes"
    )
    create_application()
    mock_fastmcp_class.assert_called_once_with(
        "customer",
        stateless_http=True
    )


def test_create_application_mounts_mcp_app(
    mock_container,
    mock_fast_mcp,
    mocker
):
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Container",
        return_value=mock_container
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.FastMCP",
        return_value=mock_fast_mcp
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.Config"
    )
    mocker.patch(
        "src.infrastructure.entry_points.mcp.application.set_routes"
    )
    create_application()
    mock_fast_mcp.streamable_http_app.assert_called_once()


