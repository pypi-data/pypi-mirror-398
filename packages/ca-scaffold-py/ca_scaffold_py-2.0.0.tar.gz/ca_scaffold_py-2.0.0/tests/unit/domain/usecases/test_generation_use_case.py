from unittest.mock import Mock
import pytest
from project_generator.domain.usecases.generation_use_case import GenerateProjectUseCase
from project_generator.domain.models.project_models import ProjectRequest, GeneratedProjectInfo

@pytest.fixture
def mock_adapter():
    return Mock()

@pytest.fixture
def use_case(mock_adapter):
    return GenerateProjectUseCase(generator_adapter=mock_adapter)

def test_execute_calls_adapter_zip(use_case, mock_adapter):
    request_data = ProjectRequest(project_name="Test Zip", dynamic_tools=[])
    expected_info = GeneratedProjectInfo(zip_path="/tmp/zip.zip", zip_filename="test_zip_smcp.zip", temp_dir="/tmp/zip")
    mock_adapter.generate.return_value = expected_info

    result = use_case.execute(project_data=request_data, no_zip=False)

    assert result == expected_info
    mock_adapter.generate.assert_called_once_with(request_data, False)

def test_execute_calls_adapter_no_zip(use_case, mock_adapter):
    request_data = ProjectRequest(project_name="Test NoZip", dynamic_tools=[])
    expected_info = GeneratedProjectInfo(output_path="/tmp/nozip_folder", temp_dir="/tmp/nozip")
    mock_adapter.generate.return_value = expected_info

    result = use_case.execute(project_data=request_data, no_zip=True)

    assert result == expected_info
    mock_adapter.generate.assert_called_once_with(request_data, True)