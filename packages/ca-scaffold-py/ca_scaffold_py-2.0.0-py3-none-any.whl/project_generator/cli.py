import json
from pathlib import Path
from typing import List, Optional
from typing_extensions import Annotated
import typer
from rich.console import Console
from typing_extensions import Annotated

from project_generator.infrastructure.entry_points.cli.parsers import (
    ToolDefinitionParser,
    PromptDefinitionParser,
    ResourceDefinitionParser,
    McpConnectionParser
)

from project_generator.applications.settings.container import container
from project_generator.infrastructure.entry_points.cli.handlers import CLIHandlers

console = Console()
app = typer.Typer(help="Generar y gestionar proyectos (MCP y Agentes Pro-code) desde scaffolds")

ProjectTypeOption = Annotated[
    str,
    typer.Option(
        "--type", "-T",
        help="Tipo de proyecto a generar.",
        case_sensitive=False
    )
]

McpConnectionsOption = Annotated[
    List[str],
    typer.Option(
        "--mcp-connections", "-mcp",
        help="Conexión MCP para Agente: 'name|endpoint'. E.g., 'mcp_main|http://...'"
    )
]

ToolsOption = Annotated[
    List[str],
    typer.Option(
        "--tool", "-t",
        help="Tool para MCP Server: 'name|desc|params|return'"
    )
]

PromptsOption = Annotated[
    List[str],
    typer.Option(
        "--prompt", "-p",
        help="Prompt para MCP Server: 'name|desc'"
    )
]

ResourcesOption = Annotated[
    List[str],
    typer.Option(
        "--resource", "-r",
        help="Resource para MCP Server: 'name|uri|desc|params|return'"
    )
]


@app.command("from-file")
def generate_from_file(
    config_file: Annotated[Path, typer.Option("--config", "-c", help="Path to JSON config file.", exists=True, resolve_path=True)],
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o", help="Output directory.")] = Path.cwd()
):
    """Crea un nuevo proyecto (MCP o Agente) desde un archivo JSON."""
    cli_handlers = CLIHandlers(
        generation_use_case=container.generation_use_case(), 
        console=console
    )
    cli_handlers.handle_from_file(config_file, output_dir)

@app.command("restore-backup")
def restore_backup(
    backup_name: Annotated[Optional[str], typer.Argument(help="Nombre del backup a restaurar (ej: backup_YYYYMMDD_HHMMSS). Si se omite, se listarán los disponibles.")] = None,
    force: Annotated[bool, typer.Option("--force", "-f", help="Forzar restauración sin confirmación.")] = False
):
    """(Solo MCP Servers) Lista backups o restaura un proyecto desde un backup."""
    cli_handlers = CLIHandlers(
        restore_use_case=container.restore_backup_use_case(),
        analyzer=container.project_analyzer_adapter(),
        console=console
    )
    cli_handlers.handle_restore_backup(backup_name, force)

@app.command("create")
def generate_direct(
    project_name: Annotated[str, typer.Argument(help="Nombre del proyecto (e.g., my_project_smcp o my_agent)")],
    project_type: ProjectTypeOption = "mcp_server",
    mcp_connections: McpConnectionsOption = [],
    tools: ToolsOption = [],
    prompts: PromptsOption = [],
    resources: ResourcesOption = [],
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o", help="Output directory.")] = Path.cwd(),
    no_zip: Annotated[bool, typer.Option("--no-zip", help="Generate project files directly without creating a zip archive.")] = False
):
    """Crea un nuevo proyecto (MCP o Agente) via argumentos."""
    
    cli_handlers = CLIHandlers(
        generation_use_case=container.generation_use_case(),
        tool_parser=ToolDefinitionParser(),
        prompt_parser=PromptDefinitionParser(),
        resource_parser=ResourceDefinitionParser(),
        mcp_connection_parser=McpConnectionParser(),
        console=console
    )
    cli_handlers.handle_create(
        project_name,
        project_type,
        mcp_connections,
        tools,
        prompts,
        resources,
        output_dir,
        no_zip
    )


@app.command("interactive")
def generate_interactive(
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o", help="Output directory.")] = Path.cwd()
):
    """Crea un nuevo proyecto (MCP o Agente) interactivamente."""
    
    cli_handlers = CLIHandlers(
        generation_use_case=container.generation_use_case(),
        tool_parser=ToolDefinitionParser(),
        prompt_parser=PromptDefinitionParser(),
        resource_parser=ResourceDefinitionParser(),
        mcp_connection_parser=McpConnectionParser(),
        console=console
    )
    cli_handlers.handle_interactive(output_dir)


@app.command("add")
def add_to_project(
    tools: ToolsOption = [],
    prompts: PromptsOption = [],
    resources: ResourcesOption = [],
    mcp_connections: McpConnectionsOption = [],
):
    cli_handlers = CLIHandlers(
        update_use_case=container.update_project_use_case(),
        tool_parser=ToolDefinitionParser(),
        prompt_parser=PromptDefinitionParser(),
        resource_parser=ResourceDefinitionParser(),
        mcp_connection_parser=McpConnectionParser(),
        console=console,
        analyzer=container.project_analyzer_adapter()
    )
    cli_handlers.handle_add(tools, prompts, resources, mcp_connections)


@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


def main():
    app()


if __name__ == "__main__":
    main()