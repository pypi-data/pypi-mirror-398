import json
import os
import pytest
from project_generator.infrastructure.driven_adapters.cookiecutter_adapter import CookiecutterAdapter
from project_generator.domain.models.project_models import ProjectRequest

COOKIECUTTER_PATH_IN_ADAPTER = 'project_generator.infrastructure.driven_adapters.cookiecutter_adapter.cookiecutter'

@pytest.fixture(autouse=True)
def mock_filesystem_basic(mocker):
    mocker.patch('tempfile.mkdtemp', return_value='/tmp/fake_tempdir')
    mocker.patch('shutil.copytree')
    mocker.patch('os.makedirs')
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('shutil.copy2')
    mocker.patch('shutil.rmtree')
    mock_file_open = mocker.mock_open(read_data='{"project_name": "default", "dynamic_tools": "[]", "dynamic_prompts": "[]", "dynamic_resources": "[]"}')
    mocker.patch('builtins.open', mock_file_open)

def test_generate_success_zip(mocker):
    mock_cookiecutter = mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mock_make_archive = mocker.patch('shutil.make_archive')

    request_data = ProjectRequest(
        project_name="MCP Demo Zip",
        dynamic_tools=[{"name": "test_tool"}],
        dynamic_prompts=[{"name": "test_prompt"}],
        dynamic_resources=[{"name": "test_resource"}]
    )
    adapter = CookiecutterAdapter()

    result = adapter.generate(request_data, no_zip=False)

    expected_slug = "mcp_demo_zip"
    expected_context_subset = {
        "dynamic_tools": json.dumps([{"name": "test_tool"}]),
        "dynamic_prompts": json.dumps([{"name": "test_prompt"}]),
        "dynamic_resources": json.dumps([{"name": "test_resource"}])
    }

    mock_cookiecutter.assert_called_once()
    call_args = mock_cookiecutter.call_args[1]
    assert call_args['extra_context']['project_name'] == request_data.project_name
    assert call_args['extra_context']['dynamic_tools'] == expected_context_subset['dynamic_tools']
    assert call_args['extra_context']['dynamic_prompts'] == expected_context_subset['dynamic_prompts']
    assert call_args['extra_context']['dynamic_resources'] == expected_context_subset['dynamic_resources']

    mock_make_archive.assert_called_once_with(
        base_name=f"/tmp/fake_tempdir/{expected_slug}",
        format='zip',
        root_dir='/tmp/fake_tempdir/output',
        base_dir=expected_slug
    )

    assert result.zip_path == f"/tmp/fake_tempdir/{expected_slug}.zip"
    assert result.zip_filename == f"{expected_slug}.zip"
    assert result.temp_dir == '/tmp/fake_tempdir'
    assert result.output_path is None

def test_generate_success_no_zip(mocker):
    mock_cookiecutter = mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mock_make_archive = mocker.patch('shutil.make_archive')

    request_data = ProjectRequest(project_name="MCP Demo NoZip_smcp", dynamic_tools=[])
    adapter = CookiecutterAdapter()

    result = adapter.generate(request_data, no_zip=True)

    mock_cookiecutter.assert_called_once()
    mock_make_archive.assert_not_called()

    expected_slug = "mcp_demo_nozip_smcp"
    expected_output_path = f"/tmp/fake_tempdir/output/{expected_slug}"

    assert result.output_path == expected_output_path
    assert result.temp_dir == '/tmp/fake_tempdir'
    assert result.zip_path is None
    assert result.zip_filename is None

def test_generate_cookiecutter_fails(mocker):
    from cookiecutter.exceptions import CookiecutterException
    mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER, side_effect=CookiecutterException("Cookiecutter failed test"))
    mock_rmtree = mocker.patch('shutil.rmtree')

    request_data = ProjectRequest(project_name="MCP Fail_smcp", dynamic_tools=[])
    adapter = CookiecutterAdapter()

    with pytest.raises(RuntimeError, match="Error generating project with Cookiecutter: Cookiecutter failed test"):
        adapter.generate(request_data)

    mock_rmtree.assert_called_once_with('/tmp/fake_tempdir')

def test_generate_project_slug_normalization(mocker):
    mock_cookiecutter = mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mock_make_archive = mocker.patch('shutil.make_archive')

    test_cases = [
        ("My Project_smcp", "my_project_smcp"),
        ("test-with-dashes_smcp", "test_with_dashes_smcp"),
        ("CamelCase_smcp", "camelcase_smcp"),
        ("Multiple  Spaces_smcp", "multiple__spaces_smcp"),
    ]

    adapter = CookiecutterAdapter()

    for project_name, expected_slug in test_cases:
        mock_make_archive.reset_mock()
        request_data = ProjectRequest(project_name=project_name, dynamic_tools=[])
        result = adapter.generate(request_data, no_zip=False)

        assert result.zip_filename == f"{expected_slug}.zip"
        mock_make_archive.assert_called_once()
        call_args = mock_make_archive.call_args[1]
        assert call_args['base_name'].endswith(expected_slug)

def test_generate_handles_io_error(mocker):
    mocker.patch('shutil.copytree', side_effect=IOError("File system error test"))
    mock_rmtree = mocker.patch('shutil.rmtree')

    request_data = ProjectRequest(project_name="TestIO_smcp", dynamic_tools=[])
    adapter = CookiecutterAdapter()

    with pytest.raises(RuntimeError, match="Error generating project with Cookiecutter: File system error test"):
        adapter.generate(request_data)

    mock_rmtree.assert_called_once_with('/tmp/fake_tempdir')

def test_generate_creates_proper_structure(mocker):
    mock_copytree = mocker.patch('shutil.copytree')
    mock_makedirs = mocker.patch('os.makedirs')
    mock_cookiecutter = mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mock_make_archive = mocker.patch('shutil.make_archive')
    mock_copy2 = mocker.patch('shutil.copy2')

    request_data = ProjectRequest(project_name="Test Structure_smcp", dynamic_tools=[])
    adapter = CookiecutterAdapter()

    adapter.generate(request_data)

    assert mocker.call('/tmp/fake_tempdir/output') in mock_makedirs.call_args_list
    
    mock_copytree.assert_called_once()
    args_copytree = mock_copytree.call_args[0]
    assert args_copytree[0].endswith('scaffold')
    assert args_copytree[1] == '/tmp/fake_tempdir/scaffold_template'

    mock_copy2.assert_called_once()
    args_copy2 = mock_copy2.call_args[0]
    assert args_copy2[0].endswith('generation_utils.py')
    assert args_copy2[1] == '/tmp/generation_utils.py'

def test_generate_missing_generation_utils(mocker, capsys):
    mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mocker.patch('shutil.make_archive')

    def exists_side_effect(path):
        if 'hooks/generation_utils.py' in path:
            return False
        return True
    mocker.patch('os.path.exists', side_effect=exists_side_effect)
    
    adapter = CookiecutterAdapter()
    adapter.generate(ProjectRequest(project_name="Test_smcp"), no_zip=False)
    captured = capsys.readouterr()
    assert "ADVERTENCIA CRÍTICA: No se encontró hook utility" in captured.out

def test_generate_cookiecutter_json_read_fails(mocker, capsys):
    mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mocker.patch('shutil.make_archive')

    mocker.patch('builtins.open', side_effect=IOError("Cannot read file"))
    
    adapter = CookiecutterAdapter()
    adapter.generate(ProjectRequest(project_name="Test_smcp"), no_zip=False)
    captured = capsys.readouterr()
    assert "ADVERTENCIA: No se pudo modificar cookiecutter.json" in captured.out

def test_generate_cookiecutter_does_not_create_dir(mocker):
    mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mocker.patch('shutil.make_archive')

    def exists_side_effect(path):
        if 'output/mcp_fail_smcp' in path:
            return False
        return True
    mocker.patch('os.path.exists', side_effect=exists_side_effect)

    adapter = CookiecutterAdapter()
    with pytest.raises(RuntimeError, match="El directorio del proyecto generado no se encontró en"):
        adapter.generate(ProjectRequest(project_name="MCP Fail_smcp"), no_zip=False)

def test_generate_cleanup_error_suppression(mocker):

    mocker.patch('shutil.copytree', side_effect=RuntimeError("Trigger Exception Handler"))
    mocker.patch('os.path.exists', return_value=True)

    mocker.patch('os.remove', side_effect=OSError("Remove failed"))
    
    adapter = CookiecutterAdapter()
    

    with pytest.raises(RuntimeError, match="Error generating project with Cookiecutter"):
        adapter.generate(ProjectRequest(project_name="FailCleanup", dynamic_tools=[]))

def test_generate_hook_copy_fails(mocker, capsys):

    mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mocker.patch('shutil.make_archive')
    mocker.patch('shutil.rmtree')
    mocker.patch('os.makedirs')
    mocker.patch('shutil.copytree')
    

    def exists_side_effect(path):
        if 'hooks/generation_utils.py' in path:
            return True
        return True
    mocker.patch('os.path.exists', side_effect=exists_side_effect)
    

    mocker.patch('shutil.copy2', side_effect=Exception("Copy failed"))
    
    adapter = CookiecutterAdapter()
    adapter.generate(ProjectRequest(project_name="Test_smcp"), no_zip=False)
    
    captured = capsys.readouterr()
    assert "ADVERTENCIA: No se pudo copiar hook utility" in captured.out

def test_generate_cleanup_hook_fails(mocker, capsys):

    mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mocker.patch('shutil.make_archive')
    mocker.patch('shutil.rmtree')
    mocker.patch('os.makedirs')
    mocker.patch('shutil.copytree')
    mocker.patch('shutil.copy2')
    

    mocker.patch('os.path.exists', return_value=True)
    

    mocker.patch('os.remove', side_effect=Exception("Remove failed"))
    
    adapter = CookiecutterAdapter()
    adapter.generate(ProjectRequest(project_name="Test_smcp"), no_zip=False)
    
    captured = capsys.readouterr()
    assert "ADVERTENCIA: No se pudo limpiar" in captured.out

def test_generate_agent_procode_type(mocker):
    """Covers: project_type passed correctly for agent_procode."""
    mocker.patch('tempfile.mkdtemp', return_value='/tmp/fake_tempdir')
    mocker.patch('shutil.copytree')
    mocker.patch('os.makedirs')
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('shutil.copy2')
    mocker.patch('shutil.rmtree')
    mock_file_open = mocker.mock_open(read_data='{"project_name": "default", "dynamic_tools": "[]", "dynamic_prompts": "[]", "dynamic_resources": "[]"}')
    mocker.patch('builtins.open', mock_file_open)
    
    mock_cookiecutter = mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mocker.patch('shutil.make_archive')
    
    request_data = ProjectRequest(
        project_name="my_agent",
        project_type="agent_procode",
        mcp_connections=[{"name": "conn1", "endpoint": "http://test"}]
    )
    adapter = CookiecutterAdapter()
    
    adapter.generate(request_data, no_zip=False)
    
    call_args = mock_cookiecutter.call_args[1]
    assert call_args['extra_context']['project_type'] == "agent_procode"


def test_generate_with_mcp_connections_json(mocker):
    """Covers: mcp_connections_json is properly serialized."""
    import json
    
    mocker.patch('tempfile.mkdtemp', return_value='/tmp/fake_tempdir')
    mocker.patch('shutil.copytree')
    mocker.patch('os.makedirs')
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('shutil.copy2')
    mocker.patch('shutil.rmtree')
    mock_file_open = mocker.mock_open(read_data='{"project_name": "default", "dynamic_tools": "[]", "dynamic_prompts": "[]", "dynamic_resources": "[]", "mcp_connections_json": "[]"}')
    mocker.patch('builtins.open', mock_file_open)
    
    mock_cookiecutter = mocker.patch(COOKIECUTTER_PATH_IN_ADAPTER)
    mocker.patch('shutil.make_archive')
    
    connections = [{"name": "c1", "endpoint": "http://e1"}, {"name": "c2", "endpoint": "http://e2"}]
    
    request_data = ProjectRequest(
        project_name="agent_test",
        project_type="agent_procode",
        mcp_connections=connections
    )
    adapter = CookiecutterAdapter()
    
    adapter.generate(request_data, no_zip=False)
    
    call_args = mock_cookiecutter.call_args[1]
    mcp_json = call_args['extra_context']['mcp_connections_json']
    parsed = json.loads(mcp_json)
    assert len(parsed) == 2
    assert parsed[0]['name'] == 'c1'