import pytest
import base64
import json
from unittest.mock import Mock
from fastapi.testclient import TestClient
from project_generator.infrastructure.entry_points.application import create_application
from project_generator.applications.settings.container import container
from project_generator.domain.usecases.generation_use_case import GenerateProjectUseCase
from project_generator.domain.models.project_models import GeneratedProjectInfo, ProjectRequest


@pytest.fixture
def test_app_client():
    mock_use_case = Mock(spec=GenerateProjectUseCase)
    with container.generation_use_case.override(mock_use_case):
        app = create_application()
        yield TestClient(app), mock_use_case


def test_health_check(test_app_client):
    """
    Tests the health check endpoint.
    """
    client, _ = test_app_client
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "scaffold-generator",
        "version": "v1"
    }


def test_generate_project_post_success(test_app_client, tmp_path):
    """
    Tests a successful POST request to the endpoint using a real temporary file.
    """
    client, mock_use_case = test_app_client

    fake_zip_dir = tmp_path / "zips"
    fake_zip_dir.mkdir()
    fake_zip_file = fake_zip_dir / "mcp_library.zip"
    fake_zip_file.write_text("This is a fake zip")

    fake_info = GeneratedProjectInfo(
        zip_path=str(fake_zip_file),
        zip_filename="mcp_library.zip",
        temp_dir=str(fake_zip_dir)
    )
    mock_use_case.execute.return_value = fake_info

    request_payload = {"project_name": "MCP Library", "dynamic_tools": []}

    response = client.post("/v1/mcp-projects/", json=request_payload)

    assert response.status_code == 200
    assert response.content == b"This is a fake zip"
    mock_use_case.execute.assert_called_once()


def test_generate_project_post_use_case_fails(test_app_client):
    """
    Tests that if the use case raises an exception, the POST endpoint
    returns a 500 error with the correct detail.
    """
    client, mock_use_case = test_app_client
    mock_use_case.execute.side_effect = RuntimeError("Something went wrong")
    request_payload = {"project_name": "MCP Library", "dynamic_tools": []}

    response = client.post("/v1/mcp-projects/", json=request_payload)

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Error generating project: Something went wrong"
    }


def test_generate_project_from_backstage_success(test_app_client, tmp_path):
    """
    Tests a successful GET request from Backstage with base64 encoded data.
    """
    client, mock_use_case = test_app_client

    fake_zip_dir = tmp_path / "zips"
    fake_zip_dir.mkdir()
    fake_zip_file = fake_zip_dir / "backstage_project.zip"
    fake_zip_file.write_text("This is a backstage zip")

    fake_info = GeneratedProjectInfo(
        zip_path=str(fake_zip_file),
        zip_filename="backstage_project.zip",
        temp_dir=str(fake_zip_dir)
    )
    mock_use_case.execute.return_value = fake_info

    project_data = {
        "project_name": "Backstage Project",
        "dynamic_tools": [{"name": "tool1", "description": "Test tool"}]
    }
    encoded_data = base64.b64encode(json.dumps(project_data).encode()).decode()

    response = client.get(f"/v1/mcp-projects/from-backstage/?data={encoded_data}")

    assert response.status_code == 200
    assert response.content == b"This is a backstage zip"
    
    mock_use_case.execute.assert_called_once()
    called_args = mock_use_case.execute.call_args[0][0]
    assert isinstance(called_args, ProjectRequest)
    assert called_args.project_name == "Backstage Project"
    assert len(called_args.dynamic_tools) == 1


def test_generate_project_from_backstage_invalid_base64(test_app_client):
    """
    Tests that invalid base64 data returns a 400 error.
    """
    client, _ = test_app_client
    
    response = client.get("/v1/mcp-projects/from-backstage/?data=invalid_base64_!!!")
    
    assert response.status_code == 400
    assert "Invalid base64 encoding" in response.json()["detail"]


def test_generate_project_from_backstage_invalid_json(test_app_client):
    """
    Tests that valid base64 but invalid JSON returns a 400 error.
    """
    client, _ = test_app_client
    
    invalid_json = "not a json"
    encoded_data = base64.b64encode(invalid_json.encode()).decode()
    
    response = client.get(f"/v1/mcp-projects/from-backstage/?data={encoded_data}")
    
    assert response.status_code == 400
    assert "Invalid JSON format" in response.json()["detail"]


def test_generate_project_from_backstage_invalid_schema(test_app_client):
    """
    Tests that valid JSON but invalid schema returns a 400 error.
    """
    client, _ = test_app_client
    
    invalid_project = {"wrong_field": "value"}
    encoded_data = base64.b64encode(json.dumps(invalid_project).encode()).decode()
    
    response = client.get(f"/v1/mcp-projects/from-backstage/?data={encoded_data}")
    
    assert response.status_code == 400
    assert "Invalid request data" in response.json()["detail"]


def test_generate_project_from_backstage_missing_data_param(test_app_client):
    """
    Tests that missing data parameter returns a 422 error.
    """
    client, _ = test_app_client
    
    response = client.get("/v1/mcp-projects/from-backstage/")
    
    assert response.status_code == 422

def test_generate_project_backstage_json_success(test_app_client, tmp_path):
    """
    Tests a successful POST request to the backstage-json endpoint.
    """
    client, mock_use_case = test_app_client

    fake_zip_dir = tmp_path / "zips"
    fake_zip_dir.mkdir()
    fake_zip_file = fake_zip_dir / "backstage_json_project.zip"
    fake_zip_content = b"This is fake zip binary content for backstage json"
    fake_zip_file.write_bytes(fake_zip_content)

    fake_info = GeneratedProjectInfo(
        zip_path=str(fake_zip_file),
        zip_filename="backstage_json_project.zip",
        temp_dir=str(fake_zip_dir)
    )
    mock_use_case.execute.return_value = fake_info

    request_payload = {
        "project_name": "Backstage JSON Project", 
        "dynamic_tools": [
            {
                "name": "test_tool",
                "description": "A test tool",
                "params": "param1: str",
                "return_type": "Dict[str, Any]"
            }
        ]
    }

    response = client.post("/v1/mcp-projects/backstage-json/", json=request_payload)

    assert response.status_code == 200
    
    response_data = response.json()
    
    assert response_data["success"] is True
    assert response_data["project_name"] == "Backstage JSON Project"
    assert response_data["filename"] == "backstage_json_project.zip"
    assert response_data["content_type"] == "application/zip"
    assert "file_content" in response_data
    assert "size_bytes" in response_data
    assert "generated_at" in response_data
    
    import base64
    decoded_content = base64.b64decode(response_data["file_content"])
    assert decoded_content == fake_zip_content
    
    assert response_data["size_bytes"] == len(fake_zip_content)
    
    mock_use_case.execute.assert_called_once()
    called_request = mock_use_case.execute.call_args[0][0]
    assert isinstance(called_request, ProjectRequest)
    assert called_request.project_name == "Backstage JSON Project"
    assert len(called_request.dynamic_tools) == 1


def test_generate_project_backstage_json_use_case_fails(test_app_client):
    """
    Tests that if the use case raises an exception, the backstage-json endpoint
    returns a 500 error with the correct detail.
    """
    client, mock_use_case = test_app_client
    mock_use_case.execute.side_effect = RuntimeError("Use case failed for backstage json")
    
    request_payload = {
        "project_name": "Failed Project", 
        "dynamic_tools": []
    }

    response = client.post("/v1/mcp-projects/backstage-json/", json=request_payload)

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Error generating project for Backstage: Use case failed for backstage json"
    }


def test_generate_project_backstage_json_invalid_request_data(test_app_client):
    """
    Tests that invalid request data returns a 422 validation error.
    """
    client, _ = test_app_client
    
    invalid_payload = {
        "dynamic_tools": []
    }

    response = client.post("/v1/mcp-projects/backstage-json/", json=invalid_payload)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_generate_project_backstage_json_empty_dynamic_tools(test_app_client, tmp_path):
    """
    Tests the backstage-json endpoint with empty dynamic_tools array.
    """
    client, mock_use_case = test_app_client

    fake_zip_dir = tmp_path / "zips"
    fake_zip_dir.mkdir()
    fake_zip_file = fake_zip_dir / "empty_tools_project.zip"
    fake_zip_content = b"Empty tools project content"
    fake_zip_file.write_bytes(fake_zip_content)

    fake_info = GeneratedProjectInfo(
        zip_path=str(fake_zip_file),
        zip_filename="empty_tools_project.zip",
        temp_dir=str(fake_zip_dir)
    )
    mock_use_case.execute.return_value = fake_info

    request_payload = {
        "project_name": "Empty Tools Project",
        "dynamic_tools": []
    }

    response = client.post("/v1/mcp-projects/backstage-json/", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["success"] is True
    assert response_data["project_name"] == "Empty Tools Project"
    
    mock_use_case.execute.assert_called_once()
    called_request = mock_use_case.execute.call_args[0][0]
    assert len(called_request.dynamic_tools) == 0


def test_generate_project_backstage_json_large_file(test_app_client, tmp_path):
    """
    Tests the backstage-json endpoint with a larger file to verify base64 encoding works correctly.
    """
    client, mock_use_case = test_app_client

    fake_zip_dir = tmp_path / "zips"
    fake_zip_dir.mkdir()
    fake_zip_file = fake_zip_dir / "large_project.zip"
    
    fake_zip_content = b"Large project content " * 50
    fake_zip_file.write_bytes(fake_zip_content)

    fake_info = GeneratedProjectInfo(
        zip_path=str(fake_zip_file),
        zip_filename="large_project.zip",
        temp_dir=str(fake_zip_dir)
    )
    mock_use_case.execute.return_value = fake_info

    request_payload = {
        "project_name": "Large Project",
        "dynamic_tools": [
            {
                "name": "complex_tool",
                "description": "A complex tool with many features",
                "params": "param1: str, param2: int, param3: Optional[List[str]]",
                "return_type": "ComplexResponse"
            }
        ]
    }

    response = client.post("/v1/mcp-projects/backstage-json/", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    
    import base64
    decoded_content = base64.b64decode(response_data["file_content"])
    assert decoded_content == fake_zip_content
    assert response_data["size_bytes"] == len(fake_zip_content)
    assert len(fake_zip_content) > 1000


def test_generate_project_backstage_json_file_not_found(test_app_client):
    """
    Tests the backstage-json endpoint when the generated zip file doesn't exist or can't be read.
    """
    client, mock_use_case = test_app_client

    fake_info = GeneratedProjectInfo(
        zip_path="/non/existent/path/project.zip",
        zip_filename="project.zip",
        temp_dir="/non/existent/temp"
    )
    mock_use_case.execute.return_value = fake_info

    request_payload = {
        "project_name": "Non Existent Project",
        "dynamic_tools": []
    }

    response = client.post("/v1/mcp-projects/backstage-json/", json=request_payload)

    assert response.status_code == 500
    assert "Error generating project for Backstage" in response.json()["detail"]

def test_generate_project_post_generic_exception(test_app_client):
    client, mock_use_case = test_app_client
    mock_use_case.execute.side_effect = Exception("Generic unexpected error")
    request_payload = {"project_name": "MCP Library", "dynamic_tools": []}
    response = client.post("/v1/mcp-projects/", json=request_payload)
    assert response.status_code == 500
    assert "Error generating project: Generic unexpected error" in response.json()["detail"]

def test_generate_project_from_backstage_generic_exception(test_app_client):
    client, mock_use_case = test_app_client
    mock_use_case.execute.side_effect = Exception("Generic backstage error")
    project_data = {"project_name": "Backstage Project"}
    encoded_data = base64.b64encode(json.dumps(project_data).encode()).decode()
    response = client.get(f"/v1/mcp-projects/from-backstage/?data={encoded_data}")
    assert response.status_code == 500
    assert "Error processing Backstage request: Generic backstage error" in response.json()["detail"]
