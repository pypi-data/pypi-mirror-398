import pytest
from unittest.mock import Mock, call, mock_open
from project_generator.infrastructure.driven_adapters.code_injector_adapter import CodeInjectorAdapter
from project_generator.domain.models.project_models import ProjectInventory

@pytest.fixture
def mock_utils(mocker):
    mock = mocker.patch('project_generator.infrastructure.driven_adapters.code_injector_adapter.utils')
    mock.to_camel_case.side_effect = lambda s: "".join(word.capitalize() for word in s.split('_'))
    mock.parse_params.return_value = [{"name": "p1", "type": "str"}]
    mock.format_params_for_sig.return_value = "p1: str"
    mock.format_params_for_call.return_value = "p1"
    

    mock.get_domain_model_template.return_value = "content"
    mock.get_domain_gateway_template.return_value = "content"
    mock.get_domain_error_template.return_value = "content"
    mock.get_use_case_template.return_value = "content"
    mock.get_adapter_template.return_value = "content"
    mock.get_settings_field_template.return_value = "content"
    mock.get_settings_validator_template.return_value = "content"
    mock.get_container_import_template.return_value = "content"
    mock.get_container_adapter_import_template.return_value = "content"
    mock.get_container_adapter_template.return_value = "content"
    mock.get_container_use_case_template.return_value = "content"
    mock.get_adapter_init_import_template.return_value = "content"
    mock.get_adapter_init_all_template.return_value = "content"
    mock.get_tools_import_template.return_value = "content"
    mock.get_tools_provide_template.return_value = "content"
    mock.get_tools_bind_template.return_value = "content"
    mock.get_prompt_use_case_template.return_value = "content"
    mock.get_prompt_content_template.return_value = "content"
    mock.get_container_prompt_import_template.return_value = "content"
    mock.get_container_prompt_use_case_template.return_value = "content"
    mock.get_prompts_import_template.return_value = "content"
    mock.get_prompts_provide_template.return_value = "content"
    mock.get_prompts_bind_template.return_value = "content"
    mock.get_resource_gateway_template.return_value = "content"
    mock.get_resource_use_case_template.return_value = "content"
    mock.get_resource_adapter_template.return_value = "content"
    mock.get_container_resource_import_template.return_value = "content"
    mock.get_container_resource_adapter_template.return_value = "content"
    mock.get_container_resource_use_case_template.return_value = "content"
    mock.get_resources_import_template.return_value = "content"
    mock.get_resources_provide_template.return_value = "content"
    mock.get_resources_bind_template.return_value = "content"

    mock.create_file = Mock()
    mock.add_code_to_file = Mock()
    return mock

@pytest.fixture
def code_injector():
    return CodeInjectorAdapter()

@pytest.fixture
def inventory():
    return ProjectInventory(is_valid=True, project_path="/fake/project")

def test_inject_tools_success(code_injector, mock_utils, inventory):
    tools = [{"name": "tool1", "description": "desc"}]
    mocker_os = Mock()
    mocker_os.path.exists.return_value = False
    with pytest.MonkeyPatch.context() as m:
        m.setattr("os.path.exists", lambda x: False)
        code_injector.inject_tools(tools, inventory)
    assert mock_utils.create_file.call_count > 0

def test_inject_tools_error(code_injector, mock_utils, inventory, capsys):
    mock_utils.create_file.side_effect = OSError("Disk error")
    code_injector.inject_tools([{"name": "tool1"}], inventory)
    captured = capsys.readouterr()
    assert "ERROR al inyectar tool" in captured.out

def test_inject_prompts_success(code_injector, mock_utils, inventory):
    prompts = [{"name": "prompt1", "description": "desc"}]
    code_injector.inject_prompts(prompts, inventory)
    assert mock_utils.create_file.call_count > 0

def test_inject_prompts_missing_name(code_injector, inventory, capsys):
    code_injector.inject_prompts([{"description": "no name"}], inventory)
    captured = capsys.readouterr()
    assert "Nombre de prompt no encontrado" in captured.out

def test_inject_resources_success(code_injector, mock_utils, inventory):
    resources = [{"name": "res1", "uri": "uri1"}]
    code_injector.inject_resources(resources, inventory)
    assert mock_utils.create_file.call_count > 0

def test_inject_resources_missing_name(code_injector, inventory, capsys):
    code_injector.inject_resources([{"uri": "uri1"}], inventory)
    captured = capsys.readouterr()
    assert "Nombre de resource no encontrado" in captured.out

def test_inject_mcp_connections_success(code_injector, inventory, mocker):
    mocker.patch("os.path.exists", return_value=True)
    

    mock_read_data = "MCP_CONNECTION_1_NAME=old\n"
    mock_file = mock_open(read_data=mock_read_data)
    mocker.patch("builtins.open", mock_file)
    
    connections = [{"name": "new_conn", "endpoint": "http://new"}]
    
    code_injector.inject_mcp_connections(connections, inventory)
    

    handle = mock_file()
    handle.write.assert_called()
    written_args = "".join([call.args[0] for call in handle.write.call_args_list])
    assert "MCP_CONNECTION_2_NAME=new_conn" in written_args
    assert "MCP_CONNECTION_2_ENDPOINT=http://new" in written_args

def test_inject_mcp_connections_error(code_injector, inventory, mocker, capsys):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", side_effect=IOError("Write denied"))
    
    connections = [{"name": "conn", "endpoint": "http://e"}]
    with pytest.raises(IOError):
        code_injector.inject_mcp_connections(connections, inventory)
    
    captured = capsys.readouterr()
    assert "ERROR al inyectar conexiones MCP" in captured.out