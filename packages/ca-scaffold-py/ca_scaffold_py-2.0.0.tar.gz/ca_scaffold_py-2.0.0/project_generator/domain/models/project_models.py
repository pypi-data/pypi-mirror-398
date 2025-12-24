from typing import Any, List, Dict, Protocol, Optional
from pydantic import BaseModel, Field, field_validator

class ProjectRequest(BaseModel):
    """Data model for a project generation request."""
    project_name: str = Field(
        ...,
        description="The name of the project to be generated.",
        examples=["MCP Library"]
    )
    project_type: str = Field(
        default="mcp_server",
        description="The type of project to generate ('mcp_server' or 'agent_procode')."
    )
    mcp_connections: List[Dict[str, str]] = Field(
        default_factory=list,
        description="A list of MCP connections for agent projects. E.g., [{'name': 'mcp1', 'endpoint': 'http://...'}].",
    )
    dynamic_tools: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of JSON objects that define the tools to be created (for 'mcp_server').",
    )
    dynamic_prompts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of JSON objects that define dynamic prompts (for 'mcp_server').",
    )
    dynamic_resources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of JSON objects that define dynamic resources (for 'mcp_server').",
    )


class GeneratedProjectInfo(BaseModel):
    temp_dir: str
    output_path: Optional[str] = None
    zip_path: Optional[str] = None
    zip_filename: Optional[str] = None


class ProjectGeneratorGateway(Protocol):
    """
    Defines the contract (interface) for any adapter that generates projects.
    """
    def generate(self, project_data: ProjectRequest, no_zip: bool = False) -> GeneratedProjectInfo:
        """
        Generates the project structure, compresses it, and returns the file path.
        """
        ...

class ProjectInventory(BaseModel):
    is_valid: bool
    project_path: str
    project_type: Optional[str] = None
    existing_tools: List[str] = Field(default_factory=list)
    existing_prompts: List[str] = Field(default_factory=list)
    existing_resources: List[str] = Field(default_factory=list)
    existing_resource_uris: List[str] = Field(default_factory=list)
    existing_mcp_connections: List[str] = Field(default_factory=list)

class ProjectAnalyzerGateway(Protocol):
    """Defines the contract for an adapter that analyzes a project's structure."""
    def analyze(self, path: str) -> ProjectInventory:
        ...

class CodeInjectorGateway(Protocol):
    def inject_tools(self, tools: List[Dict[str, Any]], inventory: ProjectInventory):
        ...
    def inject_prompts(self, prompts: List[Dict[str, Any]], inventory: ProjectInventory):
        ...
    def inject_resources(self, resources: List[Dict[str, Any]], inventory: ProjectInventory):
        ...
    def inject_mcp_connections(self, connections: List[Dict[str, str]], inventory: ProjectInventory):
        ...