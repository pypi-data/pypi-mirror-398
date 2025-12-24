import shutil
import base64
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from starlette.responses import FileResponse
from dependency_injector.wiring import inject, Provide

from project_generator.applications.settings.container import Container
from project_generator.domain.models.project_models import ProjectRequest
from project_generator.domain.usecases.generation_use_case import GenerateProjectUseCase

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Kubernetes probes
    """
    return {
        "status": "healthy",
        "service": "scaffold-generator",
        "version": "v1"
    }


@router.post("/v1/mcp-projects/", response_class=FileResponse)
@inject
async def generate_project_endpoint(
    request: ProjectRequest,
    background_tasks: BackgroundTasks,
    use_case: GenerateProjectUseCase = Depends(Provide[Container.generation_use_case])
):
    """
    Endpoint to generate and download an MCP project in ZIP format.
    Accepts JSON payload directly in the request body.
    """
    try:
        generated_info = use_case.execute(request)
        
        background_tasks.add_task(shutil.rmtree, generated_info.temp_dir)
        
        return FileResponse(
            path=generated_info.zip_path,
            media_type='application/zip',
            filename=generated_info.zip_filename
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating project: {e}"
        )


@router.get("/v1/mcp-projects/from-backstage/", response_class=FileResponse)
@inject
async def generate_project_from_backstage_endpoint(
    background_tasks: BackgroundTasks,
    data_b64: str = Query(..., alias="data", description="Base64 encoded project configuration"),
    use_case: GenerateProjectUseCase = Depends(Provide[Container.generation_use_case])
):
    try:
        decoded_data_str = base64.b64decode(data_b64).decode('utf-8')
        
        request_data = json.loads(decoded_data_str)
        
        validated_request = ProjectRequest.model_validate(request_data)
        
        generated_info = use_case.execute(validated_request)
        
        background_tasks.add_task(shutil.rmtree, generated_info.temp_dir)
        
        return FileResponse(
            path=generated_info.zip_path,
            media_type='application/zip',
            filename=generated_info.zip_filename
        )
    except base64.binascii.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid base64 encoding: {e}"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON format: {e}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request data: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Backstage request: {e}"
        )

@router.post("/v1/mcp-projects/backstage-json/")
@inject
async def generate_project_backstage_json_endpoint(
    request: ProjectRequest,
    background_tasks: BackgroundTasks,
    use_case: GenerateProjectUseCase = Depends(Provide[Container.generation_use_case])
):
    try:
        generated_info = use_case.execute(request)
        
        with open(generated_info.zip_path, "rb") as zip_file:
            zip_content = zip_file.read()
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
        
        background_tasks.add_task(shutil.rmtree, generated_info.temp_dir)
        
        return {
            "success": True,
            "project_name": request.project_name,
            "filename": generated_info.zip_filename,
            "content_type": "application/zip",
            "file_content": zip_base64,
            "size_bytes": len(zip_content),
            "generated_at": "2025-09-12T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating project for Backstage: {e}"
        )