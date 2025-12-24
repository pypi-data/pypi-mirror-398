import json
import pytest
from mcp.server.fastmcp import FastMCP
from src.applications.settings.container import Container
from src.infrastructure.entry_points.mcp import tools


@pytest.fixture(name='container_fixture')
def fixture_container_fixture():
    return Container()


@pytest.fixture(name='mock_paper_usecase')
def fixture_mock_paper_usecase(mocker):
    mock_usecase = mocker.AsyncMock()
    mock_usecase.search_papers.return_value = [
        'paper1',
        'paper2'
    ]
    mock_usecase.extract_info.return_value = (
        '{\"title\": \"Test Paper\", \"authors\": [\"Author1\"]}'
    )
    return mock_usecase


@pytest.fixture(name='mock_sum_usecase')
def fixture_mock_sum_usecase(mocker):
    mock_usecase = mocker.AsyncMock()
    mock_usecase.execute.return_value = 10.5
    return mock_usecase


@pytest.fixture(name='mock_personal_data_usecase')
def fixture_mock_personal_data_usecase(mocker):
    mock_basic = mocker.MagicMock()
    mock_basic.model_dump.return_value = {
        'customer_key': '123',
        'identification': {'type': 'CC', 'number': '456'}
    }
    mock_detailed = mocker.MagicMock()
    mock_detailed.model_dump.return_value = {
        'customer_key': '123',
        'identification': {'type': 'CC', 'number': '456'},
        'natural_person': {'name': 'Test'}
    }
    mock_usecase = mocker.AsyncMock()
    mock_usecase.get_basic_information.return_value = mock_basic
    mock_usecase.get_detailed_information.return_value = (
        mock_detailed
    )
    return mock_usecase


@pytest.mark.asyncio
async def test_bind_tools_registers_search_papers(
    container_fixture,
    mock_paper_usecase,
    mock_sum_usecase,
    mock_personal_data_usecase
):
    with container_fixture.paper_usecase.override(
        mock_paper_usecase
    ):
        with container_fixture.sum_usecase.override(
            mock_sum_usecase
        ):
            pers_override = (
                container_fixture.personal_data_usecase.override
            )
            with pers_override(mock_personal_data_usecase):
                container_fixture.wire(modules=[tools])
                mcp = FastMCP()

                tools.bind_tools(mcp)

                result = await mcp.call_tool(
                    'search_papers',
                    {'topic': 'quantum', 'max_results': 2}
                )

                assert isinstance(result, tuple)
                assert isinstance(result[0], list)
                assert len(result[0]) == 2
                assert result[0][0].text == 'paper1'
                assert result[0][1].text == 'paper2'
                called = mock_paper_usecase.search_papers
                called.assert_called_once_with('quantum', 2)

    container_fixture.reset_override()


@pytest.mark.asyncio
async def test_bind_tools_registers_extract_info(
    container_fixture,
    mock_paper_usecase,
    mock_sum_usecase,
    mock_personal_data_usecase
):
    with container_fixture.paper_usecase.override(
        mock_paper_usecase
    ):
        with container_fixture.sum_usecase.override(
            mock_sum_usecase
        ):
            pers_override = (
                container_fixture.personal_data_usecase.override
            )
            with pers_override(mock_personal_data_usecase):
                container_fixture.wire(modules=[tools])
                mcp = FastMCP()

                tools.bind_tools(mcp)

                result = await mcp.call_tool(
                    'extract_info',
                    {'paper_id': 'arxiv123'}
                )

                assert isinstance(result, tuple)
                assert isinstance(result[0], list)
                expected = (
                    '{\"title\": \"Test Paper\", '
                    '\"authors\": [\"Author1\"]}'
                )
                assert result[0][0].text == expected
                called = mock_paper_usecase.extract_info
                called.assert_called_once_with('arxiv123')

    container_fixture.reset_override()


@pytest.mark.asyncio
async def test_bind_tools_registers_sum_numbers(
    container_fixture,
    mock_paper_usecase,
    mock_sum_usecase,
    mock_personal_data_usecase
):
    with container_fixture.paper_usecase.override(
        mock_paper_usecase
    ):
        with container_fixture.sum_usecase.override(
            mock_sum_usecase
        ):
            pers_override = (
                container_fixture.personal_data_usecase.override
            )
            with pers_override(mock_personal_data_usecase):
                container_fixture.wire(modules=[tools])
                mcp = FastMCP()

                tools.bind_tools(mcp)

                result = await mcp.call_tool(
                    'sum_numbers',
                    {'a': 5.5, 'b': 5.0}
                )

                assert isinstance(result, tuple)
                assert isinstance(result[0], list)
                assert result[0][0].text == '10.5'
                called = mock_sum_usecase.execute
                called.assert_called_once_with(5.5, 5.0)

    container_fixture.reset_override()


@pytest.mark.asyncio
async def test_bind_tools_registers_get_basic_personal_data(
    container_fixture,
    mock_paper_usecase,
    mock_sum_usecase,
    mock_personal_data_usecase
):
    with container_fixture.paper_usecase.override(
        mock_paper_usecase
    ):
        with container_fixture.sum_usecase.override(
            mock_sum_usecase
        ):
            pers_override = (
                container_fixture.personal_data_usecase.override
            )
            with pers_override(mock_personal_data_usecase):
                container_fixture.wire(modules=[tools])
                mcp = FastMCP()

                tools.bind_tools(mcp)

                result = await mcp.call_tool(
                    'get_basic_personal_data',
                    {
                        'identification_type': 'CC',
                        'identification_number': '456'
                    }
                )

                assert isinstance(result, list)
                assert len(result) > 0
                result_dict = json.loads(result[0].text)
                assert result_dict['customer_key'] == '123'
                typ = result_dict['identification']['type']
                assert typ == 'CC'
                num = result_dict['identification']['number']
                assert num == '456'
                called = (
                    mock_personal_data_usecase
                    .get_basic_information
                )
                called.assert_called_once_with('CC', '456')

    container_fixture.reset_override()


@pytest.mark.asyncio
async def test_bind_tools_registers_get_detailed_personal_data(
    container_fixture,
    mock_paper_usecase,
    mock_sum_usecase,
    mock_personal_data_usecase
):
    with container_fixture.paper_usecase.override(
        mock_paper_usecase
    ):
        with container_fixture.sum_usecase.override(
            mock_sum_usecase
        ):
            pers_override = (
                container_fixture.personal_data_usecase.override
            )
            with pers_override(mock_personal_data_usecase):
                container_fixture.wire(modules=[tools])
                mcp = FastMCP()

                tools.bind_tools(mcp)

                result = await mcp.call_tool(
                    'get_detailed_personal_data',
                    {
                        'identification_type': 'CC',
                        'identification_number': '456'
                    }
                )

                assert isinstance(result, list)
                assert len(result) > 0
                result_dict = json.loads(result[0].text)
                assert result_dict['customer_key'] == '123'
                typ = result_dict['identification']['type']
                assert typ == 'CC'
                num = result_dict['identification']['number']
                assert num == '456'
                name = result_dict['natural_person']['name']
                assert name == 'Test'
                called = (
                    mock_personal_data_usecase
                    .get_detailed_information
                )
                called.assert_called_once_with('CC', '456')

    container_fixture.reset_override()


@pytest.mark.asyncio
async def test_bind_tools_search_papers_default_max_results(
    container_fixture,
    mock_paper_usecase,
    mock_sum_usecase,
    mock_personal_data_usecase
):
    with container_fixture.paper_usecase.override(
        mock_paper_usecase
    ):
        with container_fixture.sum_usecase.override(
            mock_sum_usecase
        ):
            pers_override = (
                container_fixture.personal_data_usecase.override
            )
            with pers_override(mock_personal_data_usecase):
                container_fixture.wire(modules=[tools])
                mcp = FastMCP()

                tools.bind_tools(mcp)

                result = await mcp.call_tool(
                    'search_papers',
                    {'topic': 'AI'}
                )

                assert isinstance(result, tuple)
                assert isinstance(result[0], list)
                called = mock_paper_usecase.search_papers
                called.assert_called_once_with('AI', 5)

    container_fixture.reset_override()
