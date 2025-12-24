import pytest
from project_generator.infrastructure.entry_points.cli.parsers import (
    ToolDefinitionParser, 
    PromptDefinitionParser, 
    ResourceDefinitionParser,
    McpConnectionParser
)

# --- ToolDefinitionParser Tests ---

def test_parse_valid_tool_definition():
    parser = ToolDefinitionParser()
    tool_def = "search_books|Search books by author|author: str, genre: str = None|List[Dict[str, Any]]"
    result = parser.parse(tool_def)
    assert result == {
        "name": "search_books",
        "description": "Search books by author",
        "params": "author: str, genre: str = None",
        "return_type": "List[Dict[str, Any]]"
    }

def test_parse_with_empty_params():
    parser = ToolDefinitionParser()
    tool_def = "get_status|Check API status||str"
    result = parser.parse(tool_def)
    assert result == {
        "name": "get_status",
        "description": "Check API status",
        "params": "",
        "return_type": "str"
    }

def test_parse_with_empty_return_type():
    parser = ToolDefinitionParser()
    tool_def = "update_data|Update system data|data: dict|"
    result = parser.parse(tool_def)
    assert result == {
        "name": "update_data",
        "description": "Update system data",
        "params": "data: dict",
        "return_type": "Dict[str, Any]"
    }

def test_parse_with_whitespace():
    parser = ToolDefinitionParser()
    tool_def = " search_books | Search books by author | author: str | List[Dict] "
    result = parser.parse(tool_def)
    assert result == {
        "name": "search_books",
        "description": "Search books by author",
        "params": "author: str",
        "return_type": "List[Dict]"
    }

def test_parse_invalid_part_count():
    parser = ToolDefinitionParser()
    with pytest.raises(ValueError, match="Tool definition must have 4 parts"):
        parser.parse("search_books|Search books")

def test_parse_empty_name():
    parser = ToolDefinitionParser()
    with pytest.raises(ValueError, match="Tool name cannot be empty"):
        parser.parse("|Search books|author: str|List[Dict]")

def test_parse_empty_description():
    parser = ToolDefinitionParser()
    with pytest.raises(ValueError, match="Tool description cannot be empty"):
        parser.parse("search_books||author: str|List[Dict]")

# --- PromptDefinitionParser Tests ---

def test_parse_valid_prompt_definition():
    parser = PromptDefinitionParser()
    prompt_def = "system_prompt|Main system prompt"
    result = parser.parse(prompt_def)
    assert result == {"name": "system_prompt", "description": "Main system prompt"}

def test_parse_prompt_invalid_part_count():
    parser = PromptDefinitionParser()
    with pytest.raises(ValueError, match="Prompt definition must have 2 parts"):
        parser.parse("prompt_only")

def test_parse_prompt_empty_name():
    parser = PromptDefinitionParser()
    with pytest.raises(ValueError, match="Prompt name cannot be empty"):
        parser.parse("|Main system prompt")

def test_parse_prompt_empty_description():
    parser = PromptDefinitionParser()
    with pytest.raises(ValueError, match="Prompt description cannot be empty"):
        parser.parse("system_prompt|")

# --- ResourceDefinitionParser Tests ---

def test_parse_valid_resource_definition():
    parser = ResourceDefinitionParser()
    res_def = "get_policy|policy://{id}|Get policy|id:str|Dict"
    result = parser.parse(res_def)
    assert result == {
        "name": "get_policy",
        "uri": "policy://{id}",
        "description": "Get policy",
        "params": "id:str",
        "return_type": "Dict"
    }

def test_parse_resource_empty_params_and_return():
    parser = ResourceDefinitionParser()
    res_def = "get_status|status://check|Check status||"
    result = parser.parse(res_def)
    assert result == {
        "name": "get_status",
        "uri": "status://check",
        "description": "Check status",
        "params": "",
        "return_type": "Dict[str, Any]"
    }

def test_parse_resource_invalid_part_count():
    parser = ResourceDefinitionParser()
    with pytest.raises(ValueError, match="Resource definition must have 5 parts"):
        parser.parse("res|uri|desc")

def test_parse_resource_empty_name():
    parser = ResourceDefinitionParser()
    with pytest.raises(ValueError, match="Resource name cannot be empty"):
        parser.parse("|uri|desc|params|return")

def test_parse_resource_empty_uri():
    parser = ResourceDefinitionParser()
    with pytest.raises(ValueError, match="Resource URI cannot be empty"):
        parser.parse("name||desc|params|return")

def test_parse_resource_empty_description():
    parser = ResourceDefinitionParser()
    with pytest.raises(ValueError, match="Resource description cannot be empty"):
        parser.parse("name|uri||params|return")

# --- McpConnectionParser Tests ---

def test_parse_valid_mcp_connection():
    parser = McpConnectionParser()
    conn_def = "mcp_sales|http://sales.com"
    result = parser.parse(conn_def)
    assert result == {
        "name": "mcp_sales",
        "endpoint": "http://sales.com"
    }

def test_parse_mcp_connection_whitespace():
    parser = McpConnectionParser()
    conn_def = " mcp_sales | http://sales.com "
    result = parser.parse(conn_def)
    assert result == {
        "name": "mcp_sales",
        "endpoint": "http://sales.com"
    }

def test_parse_mcp_connection_invalid_parts():
    parser = McpConnectionParser()
    with pytest.raises(ValueError, match="Definición de Conexión MCP debe tener 2 partes"):
        parser.parse("mcp_sales")

def test_parse_mcp_connection_empty_name():
    parser = McpConnectionParser()
    with pytest.raises(ValueError, match="El nombre de la conexión MCP no puede estar vacío"):
        parser.parse("|http://sales.com")

def test_parse_mcp_connection_empty_endpoint():
    parser = McpConnectionParser()
    with pytest.raises(ValueError, match="El endpoint de la conexión MCP no puede estar vacío"):
        parser.parse("mcp_sales|")