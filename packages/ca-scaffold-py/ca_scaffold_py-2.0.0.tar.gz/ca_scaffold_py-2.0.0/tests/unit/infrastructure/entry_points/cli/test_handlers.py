import json
import pytest
from pathlib import Path
from unittest.mock import Mock, mock_open, call
from rich.console import Console
import typer
import shutil
import os
import re

from project_generator.infrastructure.entry_points.cli.handlers import CLIHandlers
from project_generator.infrastructure.entry_points.cli.parsers import (
    ToolDefinitionParser, PromptDefinitionParser, ResourceDefinitionParser, McpConnectionParser
)
from project_generator.domain.models.project_models import ProjectRequest, GeneratedProjectInfo
from project_generator.domain.usecases.generation_use_case import GenerateProjectUseCase
from project_generator.domain.usecases.update_use_case import UpdateProjectUseCase
from project_generator.domain.usecases.restore_use_case import RestoreBackupUseCase
from project_generator.domain.models.project_models import ProjectAnalyzerGateway

@pytest.fixture
def mock_generation_use_case():
    use_case = Mock(spec=GenerateProjectUseCase)
    use_case.execute.return_value = GeneratedProjectInfo(
        zip_path="/tmp/test.zip",
        zip_filename="test_project_smcp.zip",
        temp_dir="/tmp/test_dir_gen"
    )
    return use_case

@pytest.fixture
def mock_update_use_case():
    use_case = Mock(spec=UpdateProjectUseCase)
    use_case.execute.return_value = (1, [], "Backup successful at /path/to/backup")
    return use_case

@pytest.fixture
def mock_restore_use_case():
    use_case = Mock(spec=RestoreBackupUseCase)
    use_case.list_backups.return_value = ["backup_1", "backup_2"]
    use_case.execute.return_value = "Project restored successfully from backup_1"
    return use_case

@pytest.fixture
def mock_analyzer():
    analyzer = Mock(spec=ProjectAnalyzerGateway)
    analyzer.analyze.return_value = Mock(is_valid=True, project_path="/fake/project")
    return analyzer

@pytest.fixture
def mock_console():
    return Mock(spec=Console)

@pytest.fixture
def cli_handlers(
    mock_generation_use_case,
    mock_update_use_case,
    mock_restore_use_case,
    mock_analyzer,
    mock_console
):
    return CLIHandlers(
        generation_use_case=mock_generation_use_case,
        update_use_case=mock_update_use_case,
        restore_use_case=mock_restore_use_case,
        analyzer=mock_analyzer,
        tool_parser=ToolDefinitionParser(),
        prompt_parser=PromptDefinitionParser(),
        resource_parser=ResourceDefinitionParser(),
        mcp_connection_parser=McpConnectionParser(),
        console=mock_console
    )

# --- Existing Tests ---

def test_handle_from_file_success(cli_handlers, mock_generation_use_case, mocker):
    config_data = {
        "project_name": "test_project_smcp",
        "dynamic_tools": [{"name": "test_tool", "description": "Test", "params":"", "return_type":"dict"}],
        "dynamic_prompts": [],
        "dynamic_resources": []
    }

    mock_file = mock_open(read_data=json.dumps(config_data))
    mocker.patch("pathlib.Path.open", mock_file)
    mock_move = mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")

    config_file = Path("/tmp/config.json")
    output_dir = Path("/tmp/output")

    cli_handlers.handle_from_file(config_file, output_dir)

    mock_generation_use_case.execute.assert_called_once()
    call_args = mock_generation_use_case.execute.call_args[0]
    assert isinstance(call_args[0], ProjectRequest)
    assert call_args[0].project_name == "test_project_smcp"
    assert call_args[1] is False
    mock_move.assert_called_once_with("/tmp/test.zip", output_dir / "test_project_smcp.zip")

def test_handle_create_success_zip(cli_handlers, mock_generation_use_case, mocker):
    mock_move = mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")

    project_name = "another_project_smcp"
    tool_definitions = ["tool1|Desc1|p1:str|str"]
    prompt_definitions = ["prompt1|DescP"]
    resource_definitions = ["res1|uri://{id}|DescR|id:int|dict"]
    output_dir = Path("/tmp/output")

    cli_handlers.handle_create(project_name, "mcp_server", [], tool_definitions, prompt_definitions, resource_definitions, output_dir, no_zip=False)

    mock_generation_use_case.execute.assert_called_once_with(mocker.ANY, False)
    call_args = mock_generation_use_case.execute.call_args[0][0]
    assert call_args.project_name == project_name
    assert len(call_args.dynamic_tools) == 1
    assert len(call_args.dynamic_prompts) == 1
    assert len(call_args.dynamic_resources) == 1
    mock_move.assert_called_once_with("/tmp/test.zip", output_dir / "test_project_smcp.zip")

def test_handle_create_success_no_zip(cli_handlers, mock_generation_use_case, mocker):
    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        output_path="/tmp/test_dir_gen/output/folder_project_smcp",
        temp_dir="/tmp/test_dir_gen"
    )
    mock_move = mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")

    project_name = "folder_project_smcp"
    tool_definitions = []
    prompt_definitions = []
    resource_definitions = []
    output_dir = Path("/tmp/output_folder")

    cli_handlers.handle_create(project_name, "mcp_server", [], tool_definitions, prompt_definitions, resource_definitions, output_dir, no_zip=True)

    mock_generation_use_case.execute.assert_called_once_with(mocker.ANY, True)
    mock_move.assert_called_once_with(
        "/tmp/test_dir_gen/output/folder_project_smcp",
        str(output_dir / "folder_project_smcp")
    )

def test_handle_create_invalid_name_suffix(cli_handlers, mock_console):
    project_name = "invalid_project"
    tool_definitions = []
    prompt_definitions = []
    resource_definitions = []
    output_dir = Path("/tmp/output")

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_create(project_name, "mcp_server", [], tool_definitions, prompt_definitions, resource_definitions, output_dir, no_zip=False)
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: Proyectos 'mcp_server' deben terminar con el sufijo '_smcp'. (Ej: 'invalid_project_smcp')")

def test_handle_create_invalid_name_format(cli_handlers, mock_console):
    project_name = "Invalid-Project_smcp"
    tool_definitions = []
    prompt_definitions = []
    resource_definitions = []
    output_dir = Path("/tmp/output")

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_create(project_name, "mcp_server", [], tool_definitions, prompt_definitions, resource_definitions, output_dir, no_zip=False)
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: Nombre de proyecto 'mcp_server' debe estar en snake_case y terminar con '_smcp'.")

def test_handle_create_invalid_tool_definition(cli_handlers, mock_console):
    project_name = "valid_project_smcp"
    tool_definitions = ["invalid_format"]
    prompt_definitions = []
    resource_definitions = []
    output_dir = Path("/tmp/output")

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_create(project_name, "mcp_server", [], tool_definitions, prompt_definitions, resource_definitions, output_dir, no_zip=False)
    assert excinfo.value.exit_code == 1
    assert "Error parsing definition: Tool definition must have 4 parts" in cli_handlers._console.print.call_args[0][0]

def test_handle_interactive_all_components(cli_handlers, mock_generation_use_case, mocker):
    mock_move = mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")

    mock_prompt = mocker.patch("rich.prompt.Prompt.ask")
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")

    mock_prompt.side_effect = [
        "mcp_server",
        "interactive_project_smcp",
        "tool_interactive", "Desc Tool", "p1:str", "dict",
        "prompt_interactive", "Desc Prompt",
        "resource_interactive", "uri://{id}", "Desc Res", "id:int", "list"
    ]
    mock_confirm.side_effect = [
        True, False,
        True, False,
        True, False,
        True
    ]

    cli_handlers.handle_interactive(Path("/tmp/output"))

    mock_generation_use_case.execute.assert_called_once()
    call_args = mock_generation_use_case.execute.call_args[0]
    request_arg = call_args[0]
    assert request_arg.project_name == "interactive_project_smcp"
    assert call_args[1] is False
    mock_move.assert_called_once()

def test_execute_generation_file_exists_error_zip(cli_handlers, mock_generation_use_case, mock_console, mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)

    project_request = ProjectRequest(project_name="test_zip_exists_smcp", dynamic_tools=[])
    expected_filename = mock_generation_use_case.execute.return_value.zip_filename
    expected_filepath = Path("/tmp/output") / expected_filename

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers._execute_generation(project_request, Path("/tmp/output"), no_zip=False)
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call(f"Error: El archivo '{expected_filepath}' ya existe.")

def test_execute_generation_folder_exists_error_nozip(cli_handlers, mock_generation_use_case, mock_console, mocker):
    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        output_path="/tmp/temp_gen/output/test_folder_exists_smcp",
        temp_dir="/tmp/temp_gen"
    )
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("os.path.exists", return_value=True)
    mock_rmtree = mocker.patch("shutil.rmtree")

    project_request = ProjectRequest(project_name="test_folder_exists_smcp", dynamic_tools=[])

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers._execute_generation(project_request, Path("/tmp/output"), no_zip=True)
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call(f"Error: El directorio '/tmp/output/test_folder_exists_smcp' ya existe.")
    mock_rmtree.assert_called_with("/tmp/temp_gen")

def test_handle_interactive_cancel_generation(cli_handlers, mocker):
    mock_prompt = mocker.patch("rich.prompt.Prompt.ask")
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")

    mock_prompt.side_effect = ["mcp_server", "cancel_project_smcp"]
    mock_confirm.side_effect = [False, False, False, False]

    cli_handlers.handle_interactive(Path("/tmp/output"))

    cli_handlers._console.print.assert_any_call("Generación de proyecto cancelada.")

def test_handle_create_general_exception(cli_handlers, mock_generation_use_case, mocker):
    mock_generation_use_case.execute.side_effect = Exception("Unexpected Generation Error")

    project_name = "error_project_smcp"
    tool_definitions = []
    prompt_definitions = []
    resource_definitions = []
    output_dir = Path("/tmp/output")

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_create(project_name, "mcp_server", [], tool_definitions, prompt_definitions, resource_definitions, output_dir, no_zip=False)
    assert excinfo.value.exit_code == 1
    cli_handlers._console.print.assert_any_call("Ocurrió un error inesperado:\nUnexpected Generation Error")

def test_handle_add_success(cli_handlers, mock_update_use_case, mock_analyzer):
    tool_defs = ["add_tool|Desc Tool|p:int|dict"]
    prompt_defs = ["add_prompt|Desc Prompt"]
    resource_defs = ["add_res|uri|Desc Res|p:str|list"]

    cli_handlers.handle_add(tool_defs, prompt_defs, resource_defs, [])

    mock_analyzer.analyze.assert_called_once_with(".")
    mock_update_use_case.execute.assert_called_once()
    call_args = mock_update_use_case.execute.call_args[0]

    assert len(call_args) == 4

    tools_arg = call_args[0]
    assert isinstance(tools_arg, list)
    assert len(tools_arg) == 1
    assert tools_arg[0]['name'] == 'add_tool'
    assert tools_arg[0]['params'] == 'p:int'

    prompts_arg = call_args[1]
    assert isinstance(prompts_arg, list)
    assert len(prompts_arg) == 1
    assert prompts_arg[0]['name'] == 'add_prompt'

    resources_arg = call_args[2]
    assert isinstance(resources_arg, list)
    assert len(resources_arg) == 1
    assert resources_arg[0]['name'] == 'add_res'
    assert resources_arg[0]['uri'] == 'uri'

    cli_handlers._console.print.assert_any_call("\n¡Éxito! Se añadieron 1 componente(s) al proyecto.")

def test_handle_add_no_components(cli_handlers, mock_console, mock_analyzer):
    mock_analyzer.analyze.return_value.is_valid = True
    with pytest.raises(typer.Exit):
        cli_handlers.handle_add([], [], [], [])
    mock_console.print.assert_any_call("Advertencia: No se especificaron componentes para añadir.")

def test_handle_add_invalid_project(cli_handlers, mock_analyzer, mock_console):
    mock_analyzer.analyze.return_value.is_valid = False
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_add(["tool|d|p|r"], [], [], [])
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: No se encontró un proyecto válido en el directorio actual.")

def test_handle_add_validation_error(cli_handlers, mock_update_use_case, mock_console):
    mock_update_use_case.execute.side_effect = ValueError("Name collision!")
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_add(["tool|d|p|r"], [], [], [])
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: Name collision!")

def test_handle_add_runtime_error(cli_handlers, mock_update_use_case, mock_console):
    mock_update_use_case.execute.side_effect = RuntimeError("Injection failed!")
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_add(["tool|d|p|r"], [], [], [])
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error Crítico durante la inyección: Injection failed!")

def test_handle_restore_backup_list(cli_handlers, mock_restore_use_case, mock_console):
    cli_handlers.handle_restore_backup(backup_name=None, force=False)
    mock_restore_use_case.list_backups.assert_called_once()
    mock_console.print.assert_any_call("Backups disponibles (más recientes primero):")
    mock_console.print.assert_any_call("  1. backup_1")
    mock_console.print.assert_any_call("  2. backup_2")
    mock_restore_use_case.execute.assert_not_called()

def test_handle_restore_backup_no_backups(cli_handlers, mock_restore_use_case, mock_console):
    mock_restore_use_case.list_backups.return_value = []
    with pytest.raises(typer.Exit):
        cli_handlers.handle_restore_backup(backup_name=None, force=False)
    mock_console.print.assert_any_call("No se encontraron backups disponibles.")

def test_handle_restore_backup_invalid_project(cli_handlers, mock_analyzer, mock_console):
    mock_analyzer.analyze.return_value.is_valid = False
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_restore_backup(backup_name="backup_1", force=False)
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: No se encontró un proyecto válido en el directorio actual.")

def test_handle_restore_backup_name_not_found(cli_handlers, mock_restore_use_case, mock_console):
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_restore_backup(backup_name="non_existent", force=False)
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: El backup 'non_existent' no existe.")

def test_handle_restore_backup_confirm_yes(cli_handlers, mock_restore_use_case, mocker):
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask", return_value=True)
    cli_handlers.handle_restore_backup(backup_name="backup_1", force=False)
    mock_confirm.assert_called_once()
    mock_restore_use_case.execute.assert_called_once_with("/fake/project", "backup_1")
    cli_handlers._console.print.assert_any_call(f"¡Éxito! {mock_restore_use_case.execute.return_value}")

def test_handle_restore_backup_confirm_no(cli_handlers, mock_restore_use_case, mocker):
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask", return_value=False)
    with pytest.raises(typer.Exit):
        cli_handlers.handle_restore_backup(backup_name="backup_1", force=False)
    mock_confirm.assert_called_once()
    mock_restore_use_case.execute.assert_not_called()
    cli_handlers._console.print.assert_any_call("Restauración cancelada.")

def test_handle_restore_backup_force(cli_handlers, mock_restore_use_case, mocker):
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    cli_handlers.handle_restore_backup(backup_name="backup_1", force=True)
    mock_confirm.assert_not_called()
    mock_restore_use_case.execute.assert_called_once_with("/fake/project", "backup_1")
    cli_handlers._console.print.assert_any_call(f"¡Éxito! {mock_restore_use_case.execute.return_value}")

def test_handle_restore_backup_runtime_error(cli_handlers, mock_restore_use_case, mock_console, mocker):
    mock_restore_use_case.execute.side_effect = RuntimeError("Restore failed!")
    mocker.patch("rich.prompt.Confirm.ask", return_value=True)
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_restore_backup(backup_name="backup_1", force=False)
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error Crítico durante la restauración: Restore failed!")

def test_execute_generation_cleanup_error(cli_handlers, mock_generation_use_case, mock_console, mocker):
    temp_dir_path = "/tmp/test_dir_gen_cleanup_fail"
    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        zip_path="/tmp/temp_zip.zip", 
        zip_filename="test_cleanup_fail_smcp.zip",
        temp_dir=temp_dir_path
    )
    move_exception = Exception("Move failed")
    mocker.patch("shutil.move", side_effect=move_exception)
    mocker.patch("os.path.exists", return_value=True) 
    cleanup_exception = Exception("Cleanup failed in finally")
    mocker.patch("shutil.rmtree", side_effect=cleanup_exception)
    mocker.patch("pathlib.Path.exists", return_value=False)

    project_request = ProjectRequest(project_name="test_cleanup_fail_smcp", dynamic_tools=[])

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers._execute_generation(project_request, Path("/tmp/output"), no_zip=False)

    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call(f"Ocurrió un error inesperado:\n{move_exception}")
    
    expected_warning_call = call(f"Advertencia: Fallo al limpiar directorio temporal {temp_dir_path}: {cleanup_exception}")
    assert expected_warning_call in mock_console.print.call_args_list

def test_handle_add_generic_exception(cli_handlers, mock_update_use_case, mock_console):
    mock_update_use_case.execute.side_effect = Exception("Generic Add Error")
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_add(["tool|d|p|r"], [], [], [])
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Ocurrió un error inesperado:\nGeneric Add Error")

def test_handle_create_agent_procode_success(cli_handlers, mock_generation_use_case, mocker):
    mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    
    cli_handlers.handle_create(
        project_name="my_agent",
        project_type="agent_procode",
        mcp_connection_definitions=["mcp1|http://url"],
        tool_definitions=[],
        prompt_definitions=[],
        resource_definitions=[],
        output_dir=Path("/out"),
        no_zip=False
    )
    
    mock_generation_use_case.execute.assert_called_once()
    req = mock_generation_use_case.execute.call_args[0][0]
    assert req.project_type == "agent_procode"
    assert len(req.mcp_connections) == 1
    assert req.mcp_connections[0]['name'] == "mcp1"

def test_handle_create_invalid_project_type(cli_handlers):
    with pytest.raises(typer.Exit):
        cli_handlers.handle_create("p", "invalid_type", [], [], [], [], Path("."), False)

def test_handle_create_agent_procode_ignores_tools(cli_handlers, mock_console, mocker):
    mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)

    cli_handlers.handle_create(
        "agent", "agent_procode", [], ["tool|d|p|r"], [], [], Path("."), False
    )
    mock_console.print.assert_any_call("Advertencia: --tool, --prompt, y --resource son ignorados para 'agent_procode'.")

def test_handle_create_mcp_server_ignores_connections(cli_handlers, mock_console, mocker):
    mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)

    cli_handlers.handle_create(
        "server_smcp", "mcp_server", ["mcp1|http://url"], [], [], [], Path("."), False
    )
    mock_console.print.assert_any_call("Advertencia: --mcp-connections es ignorado para 'mcp_server'.")

def test_handle_interactive_agent_procode(cli_handlers, mock_generation_use_case, mocker):
    mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    mock_prompt = mocker.patch("rich.prompt.Prompt.ask")
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    

    mock_prompt.side_effect = [
        "agent_procode",
        "my_agent",
        "mcp1",
        "http://url"
    ]
    mock_confirm.side_effect = [
        True,
        False,
        True
    ]
    
    cli_handlers.handle_interactive(Path("."))
    
    req = mock_generation_use_case.execute.call_args[0][0]
    assert req.project_type == "agent_procode"
    assert len(req.mcp_connections) == 1

def test_handle_interactive_agent_procode_no_connections(cli_handlers, mock_generation_use_case, mocker, mock_console):
    mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    mock_prompt = mocker.patch("rich.prompt.Prompt.ask")
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    
    mock_prompt.side_effect = ["agent_procode", "my_agent"]
    mock_confirm.side_effect = [False, True]
    
    cli_handlers.handle_interactive(Path("."))
    
    mock_console.print.assert_any_call("Advertencia: No se definieron conexiones MCP. El agente se creará sin tools.")

def test_handle_add_calls_update_use_case(cli_handlers, mock_update_use_case, mock_analyzer):
    mock_analyzer.analyze.return_value.is_valid = True
    cli_handlers.handle_add([], [], [], ["mcp1|http://url"])
    mock_update_use_case.execute.assert_called_once()
    args = mock_update_use_case.execute.call_args[0]
    assert len(args[3]) == 1

def test_handle_restore_backup_success_restore(cli_handlers, mock_restore_use_case, mocker):
    mock_restore_use_case.list_backups.return_value = ["bk1"]
    mock_restore_use_case.execute.return_value = "Restored"
    mocker.patch("rich.prompt.Confirm.ask", return_value=True)
    
    cli_handlers.handle_restore_backup("bk1", False)
    mock_restore_use_case.execute.assert_called_with("/fake/project", "bk1")

def test_handle_restore_backup_invalid_backup(cli_handlers, mock_restore_use_case):
    mock_restore_use_case.list_backups.return_value = ["bk1"]
    with pytest.raises(typer.Exit):
        cli_handlers.handle_restore_backup("bk2", False)

def test_execute_generation_output_path(cli_handlers, mock_generation_use_case, mocker):

    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        output_path="/tmp/gen/folder",
        temp_dir="/tmp/gen",
        zip_path=None
    )
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mock_move = mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    
    cli_handlers.handle_create("p_smcp", "mcp_server", [], [], [], [], Path("/out"), True)
    
    mock_move.assert_called_once()
    assert "folder" in str(mock_move.call_args[0][1])

def test_execute_generation_no_output_error(cli_handlers, mock_generation_use_case, mock_console, mocker):
    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        output_path=None, zip_path=None, temp_dir="/tmp/t"
    )
    mocker.patch("shutil.rmtree")
    with pytest.raises(typer.Exit):
        cli_handlers._execute_generation(ProjectRequest(project_name="p", dynamic_tools=[]), Path("."), False)
    
    mock_console.print.assert_any_call("Ocurrió un error inesperado:\nLa generación finalizó pero no se proporcionó ruta de salida (zip o carpeta).")

def test_handle_add_typer_exit_exception(cli_handlers, mock_analyzer):

    mock_analyzer.analyze.side_effect = typer.Exit(code=1)
    with pytest.raises(typer.Exit):
        cli_handlers.handle_add([], [], [], [])

# --- Nuevos Tests para aumentar cobertura (Loops y validaciones) ---

def test_collect_items_interactively_loop(cli_handlers, mocker):
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")

    mock_confirm.side_effect = [True, True, False]
    
    mock_creator = Mock()
    mock_creator.side_effect = [{"name": "item1"}, {"name": "item2"}]
    
    items = cli_handlers._collect_items_interactively("test_item", mock_creator)
    
    assert len(items) == 2
    assert items[0]["name"] == "item1"
    assert items[1]["name"] == "item2"

def test_collect_items_interactively_immediate_exit(cli_handlers, mocker):
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")

    mock_confirm.side_effect = [False]
    
    mock_creator = Mock()
    items = cli_handlers._collect_items_interactively("test_item", mock_creator)
    
    assert len(items) == 0
    mock_creator.assert_not_called()

def test_handle_create_invalid_name_pattern_match(cli_handlers, mock_console):

    project_name = "Invalid_Name_smcp" 
    
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_create(project_name, "mcp_server", [], [], [], [], Path("/out"), False)
    
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: Nombre de proyecto 'mcp_server' debe estar en snake_case y terminar con '_smcp'.")

def test_handle_interactive_exception(cli_handlers, mocker, mock_console):
    mocker.patch("rich.console.Console.print", side_effect=Exception("Interactive Error"))
    
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_interactive(Path("."))
    
    assert excinfo.value.exit_code == 1

def test_execute_generation_cleanup_exception_in_finally(cli_handlers, mock_generation_use_case, mock_console, mocker):

    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        temp_dir="/tmp/temp", zip_path="/tmp/z.zip", zip_filename="z.zip"
    )
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.move")
    

    mocker.patch("shutil.rmtree", side_effect=Exception("Cleanup error"))
    
    cli_handlers._execute_generation(ProjectRequest(project_name="p", dynamic_tools=[]), Path("."), False)
    

    args_list = mock_console.print.call_args_list
    assert any("Advertencia: Fallo al limpiar directorio temporal" in str(call) for call in args_list)

def test_handle_create_invalid_regex_name(cli_handlers, mock_console):



    with pytest.raises(typer.Exit):
        cli_handlers.handle_create("Bad_Name_smcp", "mcp_server", [], [], [], [], Path("."), False)
    mock_console.print.assert_any_call("Error: Nombre de proyecto 'mcp_server' debe estar en snake_case y terminar con '_smcp'.")


def test_handle_interactive_cancel_generation(cli_handlers, mocker, mock_console):
    """Covers: else branch when user cancels generation in handle_interactive."""
    mocker.patch("rich.prompt.Prompt.ask", side_effect=["mcp_server", "my_project_smcp"])
    mocker.patch("rich.prompt.Confirm.ask", side_effect=[False, False, False, False])
    
    cli_handlers.handle_interactive(Path("."))
    
    mock_console.print.assert_any_call("Generación de proyecto cancelada.")


def test_handle_interactive_name_adjusted_suffix(cli_handlers, mocker, mock_generation_use_case, mock_console):
    """Covers: the if not project_name.endswith('_smcp') branch in handle_interactive."""
    mocker.patch("shutil.move")
    mocker.patch("shutil.rmtree")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("rich.prompt.Prompt.ask", side_effect=["mcp_server", "my_project"])
    mocker.patch("rich.prompt.Confirm.ask", side_effect=[False, False, False, True])
    
    cli_handlers.handle_interactive(Path("."))
    

    mock_console.print.assert_any_call("Nombre ajustado a: [bold]my_project_smcp[/bold]")


def test_show_project_summary_agent_no_connections(cli_handlers, mock_console):
    """Covers: if not mcp_connections: branch in _show_project_summary for agent_procode."""
    cli_handlers._show_project_summary(
        project_name="test_agent",
        project_type="agent_procode",
        mcp_connections=[],
        tools=[],
        prompts=[],
        resources=[]
    )
    mock_console.print.assert_any_call("   Ninguna")


def test_show_project_summary_agent_with_connections(cli_handlers, mock_console):
    """Covers: for loop in _show_project_summary for agent_procode with connections."""
    cli_handlers._show_project_summary(
        project_name="test_agent",
        project_type="agent_procode",
        mcp_connections=[{"name": "conn1", "endpoint": "http://url1"}],
        tools=[],
        prompts=[],
        resources=[]
    )
    mock_console.print.assert_any_call("  1. conn1 (http://url1)")


def test_show_project_summary_mcp_server_with_all(cli_handlers, mock_console):
    """Covers: all branches in _show_project_summary for mcp_server with items."""
    cli_handlers._show_project_summary(
        project_name="test_smcp",
        project_type="mcp_server",
        mcp_connections=[],
        tools=[{"name": "tool1"}],
        prompts=[{"name": "prompt1"}],
        resources=[{"name": "res1", "uri": "uri://test"}]
    )
    mock_console.print.assert_any_call("  1. tool1")
    mock_console.print.assert_any_call("  1. prompt1")
    mock_console.print.assert_any_call("  1. res1 (uri://test)")


def test_show_project_summary_mcp_server_no_items(cli_handlers, mock_console):
    """Covers: all 'Ninguna/Ninguno' branches in _show_project_summary for mcp_server."""
    cli_handlers._show_project_summary(
        project_name="test_smcp",
        project_type="mcp_server",
        mcp_connections=[],
        tools=[],
        prompts=[],
        resources=[]
    )

    call_args_list = [str(call) for call in mock_console.print.call_args_list]
    ninguna_count = sum(1 for c in call_args_list if "Ninguna" in c)
    ninguno_count = sum(1 for c in call_args_list if "Ninguno" in c)
    assert ninguna_count >= 1
    assert ninguno_count >= 2


def test_create_tool_interactively(cli_handlers, mocker):
    """Covers: _create_tool_interactively method."""
    mocker.patch("rich.prompt.Prompt.ask", side_effect=["my_tool", "Description", "param: str", "Dict"])
    
    result = cli_handlers._create_tool_interactively()
    
    assert result["name"] == "my_tool"
    assert result["description"] == "Description"
    assert result["params"] == "param: str"
    assert result["return_type"] == "Dict"


def test_create_prompt_interactively(cli_handlers, mocker):
    """Covers: _create_prompt_interactively method."""
    mocker.patch("rich.prompt.Prompt.ask", side_effect=["my_prompt", "Prompt description"])
    
    result = cli_handlers._create_prompt_interactively()
    
    assert result["name"] == "my_prompt"
    assert result["description"] == "Prompt description"


def test_create_resource_interactively(cli_handlers, mocker):
    """Covers: _create_resource_interactively method."""
    mocker.patch("rich.prompt.Prompt.ask", side_effect=["my_resource", "uri://{id}", "Resource desc", "id: str", "Dict"])
    
    result = cli_handlers._create_resource_interactively()
    
    assert result["name"] == "my_resource"
    assert result["uri"] == "uri://{id}"
    assert result["description"] == "Resource desc"
    assert result["params"] == "id: str"
    assert result["return_type"] == "Dict"


def test_create_mcp_connection_interactively(cli_handlers, mocker):
    """Covers: _create_mcp_connection_interactively method."""
    mocker.patch("rich.prompt.Prompt.ask", side_effect=["mcp_conn", "http://localhost:3000"])
    
    result = cli_handlers._create_mcp_connection_interactively()
    
    assert result["name"] == "mcp_conn"
    assert result["endpoint"] == "http://localhost:3000"


def test_execute_generation_zip_exists_error(cli_handlers, mock_generation_use_case, mock_console, mocker):
    """Covers: if final_zip_path.exists() branch in _execute_generation."""
    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        zip_path="/tmp/test.zip",
        zip_filename="test_smcp.zip",
        temp_dir="/tmp/temp"
    )
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")
    
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers._execute_generation(
            ProjectRequest(project_name="test_smcp", dynamic_tools=[]),
            Path("/out"),
            no_zip=False
        )
    
    assert excinfo.value.exit_code == 1

    assert any("ya existe" in str(call) for call in mock_console.print.call_args_list)


def test_execute_generation_folder_exists_error(cli_handlers, mock_generation_use_case, mock_console, mocker):
    """Covers: if final_folder_path.exists() branch in _execute_generation for no_zip."""
    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        output_path="/tmp/gen/test_smcp",
        temp_dir="/tmp/gen"
    )
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")
    
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers._execute_generation(
            ProjectRequest(project_name="test_smcp", dynamic_tools=[]),
            Path("/out"),
            no_zip=True
        )
    
    assert excinfo.value.exit_code == 1


def test_execute_generation_cleanup_fails_in_catch_block(cli_handlers, mock_generation_use_case, mock_console, mocker):
    """Covers: except block in cleanup within the main except handler."""
    mock_generation_use_case.execute.return_value = GeneratedProjectInfo(
        temp_dir="/tmp/temp",
        zip_path="/tmp/z.zip", 
        zip_filename="z.zip"
    )
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.move", side_effect=Exception("Move error"))
    mocker.patch("shutil.rmtree", side_effect=Exception("Cleanup failed in catch"))
    
    with pytest.raises(typer.Exit):
        cli_handlers._execute_generation(
            ProjectRequest(project_name="p", dynamic_tools=[]),
            Path("."),
            no_zip=False
        )
    

    assert any("Error limpiando directorio temporal" in str(call) for call in mock_console.print.call_args_list)


def test_handle_from_file_default_project_type(cli_handlers, mock_generation_use_case, mocker):
    """Covers: if 'project_type' not in data branch in handle_from_file."""
    config_data = {
        "project_name": "test_project_smcp",
        "dynamic_tools": [],
        "dynamic_prompts": [],
        "dynamic_resources": []

    }
    
    mock_file = mock_open(read_data=json.dumps(config_data))
    mocker.patch("pathlib.Path.open", mock_file)
    mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")
    
    cli_handlers.handle_from_file(Path("/tmp/config.json"), Path("/tmp/output"))
    

    req = mock_generation_use_case.execute.call_args[0][0]
    assert req.project_type == "mcp_server"


def test_handle_restore_backup_file_not_found_error(cli_handlers, mock_restore_use_case, mock_console, mocker):
    """Covers: except FileNotFoundError branch in handle_restore_backup."""
    mock_restore_use_case.execute.side_effect = FileNotFoundError("Backup not found")
    mock_restore_use_case.list_backups.return_value = ["backup_1"]
    mocker.patch("rich.prompt.Confirm.ask", return_value=True)
    
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_restore_backup(backup_name="backup_1", force=False)
    
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: Backup not found")


def test_handle_restore_backup_value_error(cli_handlers, mock_restore_use_case, mock_console, mocker):
    """Covers: except ValueError branch in handle_restore_backup."""
    mock_restore_use_case.execute.side_effect = ValueError("Invalid backup")
    mock_restore_use_case.list_backups.return_value = ["backup_1"]
    mocker.patch("rich.prompt.Confirm.ask", return_value=True)
    
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_restore_backup(backup_name="backup_1", force=False)
    
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Error: Invalid backup")


def test_handle_restore_backup_generic_exception(cli_handlers, mock_restore_use_case, mock_console, mocker):
    """Covers: generic Exception branch in handle_restore_backup."""
    mock_restore_use_case.execute.side_effect = Exception("Unexpected error")
    mock_restore_use_case.list_backups.return_value = ["backup_1"]
    mocker.patch("rich.prompt.Confirm.ask", return_value=True)
    
    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_restore_backup(backup_name="backup_1", force=False)
    
    assert excinfo.value.exit_code == 1
    mock_console.print.assert_any_call("Ocurrió un error inesperado:\nUnexpected error")


def test_handle_create_value_error_parsing(cli_handlers, mock_console, mocker):
    """Covers: except ValueError in handle_create for parsing errors."""

    with pytest.raises(typer.Exit) as excinfo:
        cli_handlers.handle_create(
            project_name="test_smcp",
            project_type="mcp_server",
            mcp_connection_definitions=[],
            tool_definitions=["invalid_format"],
            prompt_definitions=[],
            resource_definitions=[],
            output_dir=Path("."),
            no_zip=False
        )
    
    assert excinfo.value.exit_code == 1
    assert any("Error parsing definition" in str(call) for call in mock_console.print.call_args_list)
