import pytest
from unittest.mock import Mock, call, ANY
import os
from project_generator.domain.usecases.update_use_case import UpdateProjectUseCase
from project_generator.domain.models.project_models import ProjectInventory

@pytest.fixture
def mock_analyzer():
    analyzer = Mock()

    analyzer.analyze.return_value = ProjectInventory(
        is_valid=True,
        project_path="/fake/project",
        project_type="mcp_server",
        existing_tools=[],
        existing_prompts=[],
        existing_resources=[],
        existing_resource_uris=[],
        existing_mcp_connections=[]
    )
    return analyzer

@pytest.fixture
def mock_injector():
    return Mock()

@pytest.fixture
def update_use_case(mock_analyzer, mock_injector):
    return UpdateProjectUseCase(analyzer=mock_analyzer, injector=mock_injector)

def test_execute_invalid_project(update_use_case, mock_analyzer):
    mock_analyzer.analyze.return_value.is_valid = False
    with pytest.raises(FileNotFoundError, match="No se encontró un proyecto válido"):
        update_use_case.execute([], [], [])

def test_execute_no_components_to_add(update_use_case):
    count, warnings, msg = update_use_case.execute([], [], [])
    assert count == 0
    assert msg == "No components specified to add."
    assert warnings == []

def test_execute_name_collision_tool(update_use_case, mock_analyzer):
    mock_analyzer.analyze.return_value.existing_tools = ["existing_tool"]
    tools_to_add = [{"name": "existing_tool", "description": "desc", "params": "", "return_type": "dict"}]
    with pytest.raises(ValueError, match="La herramienta 'existing_tool' ya existe."):
        update_use_case.execute(tools_to_add, [], [])

def test_execute_validation_invalid_return_type(update_use_case):
    tools_to_add = [{"name": "bad_tool", "description": "desc", "params": "", "return_type": "List<>"}]
    with pytest.raises(ValueError, match="no es una anotación de tipo Python válida"):
        update_use_case.execute(tools_to_add, [], [])

def test_execute_validation_uri_collision_internal(update_use_case):
    resources_to_add = [
        {"name": "res1", "uri": "test://{id}", "description": "d", "params": "p", "return_type": "t"},
        {"name": "res2", "uri": "test://{other_id}", "description": "d", "params": "p", "return_type": "t"}
    ]
    with pytest.raises(ValueError, match="Conflicto de URI detectado entre nuevos resources"):
        update_use_case.execute([], [], resources_to_add)

def test_execute_validation_uri_collision_existing(update_use_case, mock_analyzer):
    mock_analyzer.analyze.return_value.existing_resource_uris = ["test://{id_existente}"]
    resources_to_add = [{"name": "res_new", "uri": "test://{new_id}", "description": "d", "params": "p", "return_type": "t"}]
    with pytest.raises(ValueError, match="colisiona con un resource existente"):
        update_use_case.execute([], [], resources_to_add)

def test_execute_backup_and_inject_success(update_use_case, mock_injector, mocker):
    mock_create_backup = mocker.patch.object(update_use_case, '_create_backup', return_value="/fake/backup/path")
    tools_to_add = [{"name": "new_tool", "description": "d", "params": "p", "return_type": "t"}]
    prompts_to_add = [{"name": "new_prompt", "description": "d"}]
    resources_to_add = [{"name": "new_res", "uri":"u", "description": "d", "params":"p", "return_type": "t"}]

    count, warnings, msg = update_use_case.execute(tools_to_add, prompts_to_add, resources_to_add)

    assert count == 3
    assert msg == "Backup exitoso en: /fake/backup/path"
    mock_create_backup.assert_called_once_with("/fake/project", "mcp_server")
    mock_injector.inject_tools.assert_called_once_with(tools_to_add, mocker.ANY)
    mock_injector.inject_prompts.assert_called_once_with(prompts_to_add, mocker.ANY)
    mock_injector.inject_resources.assert_called_once_with(resources_to_add, mocker.ANY)

def test_execute_injection_fails_rollback_called(update_use_case, mock_injector, mocker):
    mock_create_backup = mocker.patch.object(update_use_case, '_create_backup', return_value="/fake/backup/rollback")
    mock_restore_backup = mocker.patch.object(update_use_case, '_restore_backup')
    mock_injector.inject_tools.side_effect = Exception("Injection failed!")
    tools_to_add = [{"name": "fail_tool", "description": "d", "params": "p", "return_type": "t"}]

    with pytest.raises(RuntimeError, match="La inyección falló y el proyecto fue restaurado"):
        update_use_case.execute(tools_to_add, [], [])

    mock_create_backup.assert_called_once()
    mock_injector.inject_tools.assert_called_once()
    mock_restore_backup.assert_called_once_with("/fake/backup/rollback", "/fake/project", "mcp_server")

def test_create_backup_success(update_use_case, mocker):
    mocker.patch("os.makedirs")
    mock_copytree = mocker.patch("shutil.copytree")
    mock_cleanup = mocker.patch.object(update_use_case, '_cleanup_old_backups')
    mocker.patch("datetime.datetime")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

    backup_path = update_use_case._create_backup("/fake/project", "mcp_server")

    assert backup_path.startswith("/fake/project/.mcp_backups/backup_")
    mock_copytree.assert_called_once_with("/fake/project/src", backup_path)
    mock_cleanup.assert_called_once()

def test_cleanup_old_backups(update_use_case, mocker):
    mocker.patch("os.listdir", return_value=["backup_1", "backup_2", "backup_3", "backup_4", "backup_5", "backup_6", "other_file"])
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    mocker.patch("os.path.getmtime", side_effect=[1, 2, 3, 4, 5, 6])
    mock_rmtree = mocker.patch("shutil.rmtree")

    update_use_case._max_backups = 5
    update_use_case._cleanup_old_backups("/fake/project/.mcp_backups")

    mock_rmtree.assert_called_once_with("/fake/project/.mcp_backups/backup_1")

def test_restore_backup_success(update_use_case, mocker):
    mocker.patch("os.path.exists", return_value=True)
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_copytree = mocker.patch("shutil.copytree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

    update_use_case._restore_backup("/fake/backup/path", "/fake/project", "mcp_server")

    mock_rmtree.assert_called_once_with("/fake/project/src")
    mock_copytree.assert_called_once_with("/fake/backup/path", "/fake/project/src")

def test_create_backup_fails(update_use_case, mocker):
    mocker.patch("os.makedirs")
    mocker.patch("shutil.copytree", side_effect=OSError("Disk full"))
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    with pytest.raises(OSError, match="No se pudo crear el backup"):
        update_use_case._create_backup("/fake/project", "mcp_server")

def test_cleanup_old_backups_fails(update_use_case, mocker, caplog):
    mocker.patch("os.listdir", return_value=["backup_1", "backup_2", "backup_3", "backup_4", "backup_5", "backup_6"])
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("os.path.getmtime", side_effect=[1, 2, 3, 4, 5, 6])
    mocker.patch("shutil.rmtree", side_effect=OSError("File in use"))
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    update_use_case._max_backups = 5
    update_use_case._cleanup_old_backups("/fake/backups")
    assert "No se pudo limpiar backups antiguos: File in use" in caplog.text

def test_restore_backup_fails(update_use_case, mocker, caplog):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree", side_effect=OSError("Cannot delete src"))
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

    try:
        update_use_case._restore_backup("/fake/backup/path", "/fake/project", "mcp_server")
    except OSError:
        pass
    assert "¡FALLO CRÍTICO DURANTE LA RESTAURACIÓN" in caplog.text

def test_execute_general_error_pre_injection(update_use_case, mock_analyzer, mocker):
    mock_analyzer.analyze.return_value.is_valid = True
    mocker.patch.object(update_use_case, '_create_backup', side_effect=Exception("Backup failed"))
    tools_to_add = [{"name": "new_tool", "description": "d", "params": "p", "return_type": "t"}]
    with pytest.raises(Exception, match="Backup failed"):
        update_use_case.execute(tools_to_add, [], [])

def test_execute_general_error_and_cleanup_fails(update_use_case, mock_injector, mocker, caplog):
    mock_create_backup = mocker.patch.object(update_use_case, '_create_backup', return_value="/fake/backup/path")
    mocker.patch("os.path.exists", return_value=True)
    mock_injector.inject_tools.side_effect = Exception("Injection failed")
    mock_rmtree_cleanup = mocker.patch("shutil.rmtree", side_effect=OSError("Cleanup failed"))
    tools_to_add = [{"name": "new_tool", "description": "d", "params": "p", "return_type": "t"}]

    with pytest.raises(RuntimeError, match="La inyección falló"):
        update_use_case.execute(tools_to_add, [], [])

    assert "¡Fallo durante la inyección de código!: Injection failed" in caplog.text
    assert "¡FALLO CRÍTICO DURANTE LA RESTAURACIÓN" in caplog.text 
    assert "Cleanup failed" in caplog.text

    mock_create_backup.assert_called_once()
    mock_injector.inject_tools.assert_called_once()
    mock_rmtree_cleanup.assert_called()

def test_execute_mcp_server_add_connection_fail(update_use_case):
    with pytest.raises(ValueError, match="No se pueden añadir conexiones MCP a un proyecto tipo 'mcp_server'"):
        update_use_case.execute([], [], [], [{"name": "conn"}])

def test_execute_agent_procode_add_tools_fail(update_use_case, mock_analyzer):
    mock_analyzer.analyze.return_value.project_type = "agent_procode"
    with pytest.raises(ValueError, match="Solo se pueden añadir conexiones MCP a un proyecto tipo 'agent_procode'"):
        update_use_case.execute([{"name": "tool"}], [], [], [])

def test_execute_agent_procode_success(update_use_case, mock_analyzer, mock_injector, mocker):
    mock_analyzer.analyze.return_value.project_type = "agent_procode"
    mocker.patch("os.makedirs")
    mocker.patch("shutil.copytree")
    mocker.patch("shutil.rmtree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    mocker.patch("os.listdir", return_value=[])

    conns = [{"name": "new_conn", "endpoint": "http://"}]
    
    count, warnings, msg = update_use_case.execute([], [], [], conns)
    
    assert count == 1
    mock_injector.inject_mcp_connections.assert_called_once_with(conns, ANY)
    assert "Backup exitoso" in msg

def test_execute_agent_procode_collision(update_use_case, mock_analyzer):
    mock_analyzer.analyze.return_value.project_type = "agent_procode"
    mock_analyzer.analyze.return_value.existing_mcp_connections = ["conn1"]
    
    conns = [{"name": "conn1", "endpoint": "http://"}]
    
    with pytest.raises(ValueError, match="La conexión MCP 'conn1' ya existe"):
        update_use_case.execute([], [], [], conns)

def test_restore_backup_agent_procode(update_use_case, mock_analyzer, mock_injector, mocker):
    mock_analyzer.analyze.return_value.project_type = "agent_procode"
    
    mocker.patch("os.makedirs")
    mocker.patch("shutil.copytree")
    mock_rmtree = mocker.patch("shutil.rmtree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    mocker.patch("os.path.exists", return_value=True)
    
    mock_injector.inject_mcp_connections.side_effect = Exception("Injection fail")
    
    with pytest.raises(RuntimeError, match="La inyección falló"):
        update_use_case.execute([], [], [], [{"name": "c"}])
        
    mock_rmtree.assert_any_call("/fake/project/application/settings")

def test_validate_components_defaults(update_use_case, mock_injector, mocker):
    mocker.patch.object(update_use_case, '_create_backup', return_value="/bkp")
    mocker.patch("os.makedirs")
    mocker.patch("shutil.copytree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    mocker.patch("os.listdir", return_value=[])
    
    tools = [{"name": "tool1", "description": "desc"}] 
    resources = [{"name": "res1", "description": "desc"}] 
    count, warnings, _ = update_use_case.execute(tools, [], resources)
    assert any("No se especificó tipo de retorno" in w for w in warnings)
    assert any("No se especificó URI" in w for w in warnings)

def test_validate_return_type_valid(update_use_case, mocker):
    mocker.patch("os.makedirs")
    mocker.patch("shutil.copytree")
    mocker.patch("shutil.rmtree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    mocker.patch("os.listdir", return_value=[])
    
    tools = [{"name": "t", "description": "d", "return_type": "List[str]"}]
    update_use_case.execute(tools, [], [])

def test_validate_return_type_invalid_syntax(update_use_case):
    tools = [{"name": "t", "description": "d", "return_type": "List[String"}]
    with pytest.raises(ValueError, match="no es una anotación de tipo Python válida"):
        update_use_case.execute(tools, [], [])

def test_validate_resource_uri_internal_collision(update_use_case):
    res = [
        {"name": "r1", "uri": "res://{id}", "description": "d"},
        {"name": "r2", "uri": "res://{key}", "description": "d"} 
    ]
    with pytest.raises(ValueError, match="Conflicto de URI detectado entre nuevos resources"):
        update_use_case.execute([], [], res)

def test_validate_resource_uri_existing_collision(update_use_case, mock_analyzer):
    mock_analyzer.analyze.return_value.existing_resource_uris = ["res://{id}"]
    res = [{"name": "r1", "uri": "res://{key}", "description": "d"}]
    with pytest.raises(ValueError, match="colisiona con un resource existente"):
        update_use_case.execute([], [], res)

def test_cleanup_old_backups_exception(update_use_case, mocker, caplog):

    mocker.patch("os.listdir", side_effect=Exception("List failed"))
    update_use_case._cleanup_old_backups("/tmp")
    assert "No se pudo limpiar backups antiguos: List failed" in caplog.text

def test_execute_agent_procode_mcp_connections_error(update_use_case, mock_analyzer):
    """Covers: raise ValueError for mcp_connections on mcp_server project."""
    mock_analyzer.analyze.return_value.project_type = "mcp_server"
    mock_analyzer.analyze.return_value.is_valid = True
    
    with pytest.raises(ValueError, match="No se pueden añadir conexiones MCP a un proyecto tipo 'mcp_server'"):
        update_use_case.execute([], [], [], mcp_connections_to_add=[{"name": "conn", "endpoint": "http://"}])


def test_execute_agent_procode_tools_error(update_use_case, mock_analyzer):
    """Covers: raise ValueError for tools/prompts/resources on agent_procode project."""
    mock_analyzer.analyze.return_value.project_type = "agent_procode"
    mock_analyzer.analyze.return_value.is_valid = True
    mock_analyzer.analyze.return_value.existing_mcp_connections = []
    
    with pytest.raises(ValueError, match="Solo se pueden añadir conexiones MCP a un proyecto tipo 'agent_procode'"):
        update_use_case.execute([{"name": "tool"}], [], [])


def test_execute_agent_procode_success(update_use_case, mock_analyzer, mock_injector, mocker):
    """Covers: successful MCP connection injection for agent_procode."""
    mock_analyzer.analyze.return_value.project_type = "agent_procode"
    mock_analyzer.analyze.return_value.is_valid = True
    mock_analyzer.analyze.return_value.existing_mcp_connections = []
    
    mocker.patch.object(update_use_case, '_create_backup', return_value="/backup")
    
    mcp_connections = [{"name": "new_conn", "endpoint": "http://test"}]
    
    count, warnings, msg = update_use_case.execute([], [], [], mcp_connections_to_add=mcp_connections)
    
    assert count == 1
    mock_injector.inject_mcp_connections.assert_called_once()


def test_validate_mcp_collisions(update_use_case, mock_analyzer):
    """Covers: _validate_mcp_collisions detecting collision."""
    mock_analyzer.analyze.return_value.project_type = "agent_procode"
    mock_analyzer.analyze.return_value.is_valid = True
    mock_analyzer.analyze.return_value.existing_mcp_connections = ["existing_conn"]
    
    with pytest.raises(ValueError, match="La conexión MCP 'existing_conn' ya existe"):
        update_use_case.execute([], [], [], mcp_connections_to_add=[{"name": "existing_conn", "endpoint": "http://"}])


def test_create_backup_agent_procode(update_use_case, mocker):
    """Covers: elif project_type == 'agent_procode' branch in _create_backup."""
    mocker.patch("os.makedirs")
    mock_copytree = mocker.patch("shutil.copytree")
    mocker.patch.object(update_use_case, '_cleanup_old_backups')
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    
    backup_path = update_use_case._create_backup("/fake/project", "agent_procode")
    

    assert mock_copytree.call_count == 1
    call_args = mock_copytree.call_args[0]
    assert "application/settings" in call_args[0]


def test_restore_backup_agent_procode(update_use_case, mocker):
    """Covers: elif project_type == 'agent_procode' branch in _restore_backup."""
    mocker.patch("os.path.exists", return_value=True)
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_copytree = mocker.patch("shutil.copytree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    
    update_use_case._restore_backup("/backup/path", "/project", "agent_procode")
    

    call_args_rmtree = mock_rmtree.call_args[0][0]
    assert "application/settings" in call_args_rmtree


def test_restore_backup_target_not_exists(update_use_case, mocker):
    """Covers: if os.path.exists(target_path) is False branch."""
    mocker.patch("os.path.exists", return_value=False)
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_copytree = mocker.patch("shutil.copytree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    
    update_use_case._restore_backup("/backup", "/project", "mcp_server")
    

    mock_rmtree.assert_not_called()
    mock_copytree.assert_called_once()





def test_validate_name_collisions_prompt(update_use_case, mock_analyzer):
    """Covers: prompt collision detection in _validate_name_collisions."""
    mock_analyzer.analyze.return_value.existing_prompts = ["existing_prompt"]
    mock_analyzer.analyze.return_value.existing_tools = []
    mock_analyzer.analyze.return_value.existing_resources = []
    
    with pytest.raises(ValueError, match="El prompt 'existing_prompt' ya existe"):
        update_use_case.execute([], [{"name": "existing_prompt"}], [])


def test_validate_name_collisions_resource(update_use_case, mock_analyzer):
    """Covers: resource collision detection in _validate_name_collisions."""
    mock_analyzer.analyze.return_value.existing_resources = ["existing_resource"]
    mock_analyzer.analyze.return_value.existing_tools = []
    mock_analyzer.analyze.return_value.existing_prompts = []
    mock_analyzer.analyze.return_value.existing_resource_uris = []
    
    with pytest.raises(ValueError, match="El recurso 'existing_resource' ya existe"):
        update_use_case.execute([], [], [{"name": "existing_resource", "uri": "test://", "description": "d"}])


def test_validate_components_warning_no_return_type(update_use_case, mock_analyzer, mock_injector, mocker):
    """Covers: warning when return_type is not specified for tool."""
    mock_analyzer.analyze.return_value.existing_tools = []
    mock_analyzer.analyze.return_value.existing_prompts = []
    mock_analyzer.analyze.return_value.existing_resources = []
    mock_analyzer.analyze.return_value.existing_resource_uris = []
    
    mocker.patch.object(update_use_case, '_create_backup', return_value="/backup")
    
    tools_without_return_type = [{"name": "tool1", "description": "d", "params": ""}]
    
    count, warnings, msg = update_use_case.execute(tools_without_return_type, [], [])
    
    assert any("No se especificó tipo de retorno" in w for w in warnings)


def test_validate_components_warning_no_uri(update_use_case, mock_analyzer, mock_injector, mocker):
    """Covers: warning when URI is not specified for resource."""
    mock_analyzer.analyze.return_value.existing_tools = []
    mock_analyzer.analyze.return_value.existing_prompts = []
    mock_analyzer.analyze.return_value.existing_resources = []
    mock_analyzer.analyze.return_value.existing_resource_uris = []
    
    mocker.patch.object(update_use_case, '_create_backup', return_value="/backup")
    
    resources_without_uri = [{"name": "res1", "description": "d", "params": ""}]
    
    count, warnings, msg = update_use_case.execute([], [], resources_without_uri)
    
    assert any("No se especificó URI" in w for w in warnings)
