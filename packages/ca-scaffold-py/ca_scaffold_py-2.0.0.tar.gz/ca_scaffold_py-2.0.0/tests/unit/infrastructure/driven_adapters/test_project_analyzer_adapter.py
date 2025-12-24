import pytest
from unittest.mock import Mock, mock_open, call
import os
from project_generator.infrastructure.driven_adapters.project_analyzer_adapter import ProjectAnalyzerAdapter
from project_generator.domain.models.project_models import ProjectInventory

@pytest.fixture
def analyzer():
    return ProjectAnalyzerAdapter()

TOOLS_CONTENT = """
@mcp.tool()
async def tool_one(...): ...

@mcp.tool()
async def tool_two(...): ...
"""
PROMPTS_CONTENT = """
@mcp.prompt("prompt_a")
async def prompt_a(...): ...
"""
RESOURCES_CONTENT = """
@mcp.resource("res://uri/{id}")
async def resource_x(...): ...
"""
ENV_CONTENT = """
MCP_CONNECTION_1_NAME=conn1
MCP_CONNECTION_1_ENDPOINT=http://conn1
MCP_CONNECTION_2_NAME=conn2
"""

def test_analyze_invalid_project(analyzer, mocker):
    mocker.patch("os.path.exists", return_value=False)
    inventory = analyzer.analyze("/invalid/path")
    assert inventory.is_valid is False
    assert inventory.project_path == os.path.abspath("/invalid/path")

def test_analyze_valid_mcp_server(analyzer, mocker):
    def exists_side_effect(path):
        if 'pyproject.toml' in path: return True
        if 'src/infrastructure/entry_points/mcp/tools.py' in path: return True
        return False
    
    mocker.patch("os.path.exists", side_effect=exists_side_effect)
    mocker.patch("builtins.open", mock_open(read_data=""))
    mocker.patch("os.path.abspath", side_effect=lambda p: p)

    inventory = analyzer.analyze("/fake/project")
    assert inventory.is_valid is True
    assert inventory.project_type == "mcp_server"

def test_analyze_valid_agent_procode(analyzer, mocker):
    def exists_side_effect(path):
        if 'pyproject.toml' in path: return True
        if 'infrastructure/entry_points/a2a/a2a_server.py' in path: return True
        if '.env' in path: return True
        return False
    
    mocker.patch("os.path.exists", side_effect=exists_side_effect)
    mocker.patch("builtins.open", mock_open(read_data=ENV_CONTENT))
    mocker.patch("os.path.abspath", side_effect=lambda p: p)

    inventory = analyzer.analyze("/fake/agent")
    assert inventory.is_valid is True
    assert inventory.project_type == "agent_procode"
    assert "conn1" in inventory.existing_mcp_connections

def test_analyze_unknown_project(analyzer, mocker):
    mocker.patch("os.path.exists", side_effect=lambda p: 'pyproject.toml' in p)
    mocker.patch("os.path.abspath", side_effect=lambda p: p)
    inventory = analyzer.analyze("/fake/unknown")
    assert inventory.is_valid is False
    assert inventory.project_type == "unknown"

def test_find_components_io_error(analyzer, mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", side_effect=IOError("Read error"))
    assert analyzer._find_components("path", "pat") == []
    assert analyzer._find_components_multiple_groups("path", "pat") == []

    assert analyzer._find_mcp_connections("path") == []

def test_find_components_file_not_exists(analyzer, mocker):
    mocker.patch("os.path.exists", return_value=False)
    assert analyzer._find_components("path", "pat") == []
    assert analyzer._find_components_multiple_groups("path", "pat") == []
    assert analyzer._find_mcp_connections("path") == []

def test_find_mcp_connections_parsing(analyzer, mocker):
    mocker.patch("os.path.exists", return_value=True)
    content = """
    MCP_CONNECTION_1_NAME='sales'
    MCP_CONNECTION_1_ENDPOINT=http://s
    MCP_CONNECTION_2_NAME="inventory"
    """
    mocker.patch("builtins.open", mock_open(read_data=content))
    result = analyzer._find_mcp_connections("/fake/.env")
    assert "sales" in result
    assert "inventory" in result

def test_find_components_with_tuple_match(analyzer, mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data="key=val\nkey2=val2"))

    pattern = r"(\w+)=(\w+)"
    
    result = analyzer._find_components("any/path.py", pattern, group_index=2)
    assert result == ["val", "val2"]

    result_group1 = analyzer._find_components("any/path.py", pattern, group_index=1)
    assert result_group1 == ["key", "key2"]

def test_find_components_multiple_groups_io_error(analyzer, mocker):

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", side_effect=IOError("Read error"))
    assert analyzer._find_components_multiple_groups("path", "pat") == []

def test_analyze_parses_tools_prompts_resources(analyzer, mocker):
    """Covers: full parsing of tools, prompts, and resources in mcp_server."""
    TOOLS_CONTENT_FULL = """
@mcp.tool()
async def tool_one(...): ...

@mcp.tool()
async def tool_two(...): ...
"""
    PROMPTS_CONTENT_FULL = """
@mcp.prompt("prompt_a")
async def prompt_a(...): ...
"""
    RESOURCES_CONTENT_FULL = """
@mcp.resource("res://uri/{id}")
async def resource_x(...): ...
"""
    
    def exists_side_effect(path):
        if 'pyproject.toml' in path:
            return True
        if 'src/infrastructure/entry_points/mcp/tools.py' in path:
            return True
        if 'prompts.py' in path:
            return True
        if 'resources.py' in path:
            return True
        return False
    
    mocker.patch("os.path.exists", side_effect=exists_side_effect)
    mocker.patch("os.path.abspath", side_effect=lambda p: p)
    
    def open_side_effect(path, *args, **kwargs):
        if 'tools.py' in path:
            return mock_open(read_data=TOOLS_CONTENT_FULL)()
        if 'prompts.py' in path:
            return mock_open(read_data=PROMPTS_CONTENT_FULL)()
        if 'resources.py' in path:
            return mock_open(read_data=RESOURCES_CONTENT_FULL)()
        return mock_open(read_data="")()
    
    mocker.patch("builtins.open", side_effect=open_side_effect)
    
    inventory = analyzer.analyze("/fake/project")
    
    assert inventory.is_valid is True
    assert inventory.project_type == "mcp_server"
    assert "tool_one" in inventory.existing_tools
    assert "tool_two" in inventory.existing_tools
    assert "prompt_a" in inventory.existing_prompts
    assert "resource_x" in inventory.existing_resources
    assert "res://uri/{id}" in inventory.existing_resource_uris

