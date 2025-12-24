import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import re

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from project_generator.domain.models.project_models import ProjectRequest
from project_generator.domain.usecases.generation_use_case import GenerateProjectUseCase
from project_generator.domain.usecases.update_use_case import UpdateProjectUseCase
from project_generator.infrastructure.entry_points.cli.parsers import (
    ToolDefinitionParser,
    PromptDefinitionParser,
    ResourceDefinitionParser,
    McpConnectionParser
)
from project_generator.domain.usecases.restore_use_case import RestoreBackupUseCase
from project_generator.domain.models.project_models import ProjectAnalyzerGateway

class CLIHandlers:
    """Handles CLI operations for project generation."""
    
    def __init__(
        self,
        console: Console,
        generation_use_case: GenerateProjectUseCase = None,
        update_use_case: UpdateProjectUseCase = None,
        restore_use_case: RestoreBackupUseCase = None,
        analyzer: ProjectAnalyzerGateway = None,
        tool_parser: ToolDefinitionParser = None,
        prompt_parser: PromptDefinitionParser = None,
        resource_parser: ResourceDefinitionParser = None,
        mcp_connection_parser: McpConnectionParser = None
    ):
        self._generation_use_case = generation_use_case
        self._update_use_case = update_use_case
        self._restore_use_case = restore_use_case
        self._analyzer = analyzer
        self._tool_parser = tool_parser
        self._prompt_parser = prompt_parser
        self._resource_parser = resource_parser
        self._mcp_connection_parser = mcp_connection_parser
        self._console = console
    
    def handle_add(
        self,
        tool_definitions: List[str],
        prompt_definitions: List[str],
        resource_definitions: List[str],
        mcp_connection_definitions: List[str]
    ) -> None:
        try:
            self._console.print("Analizando proyecto existente...")
            inventory = self._analyzer.analyze(".")
            if not inventory.is_valid:
                self._console.print("Error: No se encontró un proyecto válido en el directorio actual.")
                raise typer.Exit(code=1)

            tools_to_add = [self._tool_parser.parse(d) for d in tool_definitions]
            prompts_to_add = [self._prompt_parser.parse(d) for d in prompt_definitions]
            resources_to_add = [self._resource_parser.parse(d) for d in resource_definitions]
            mcp_to_add = [self._mcp_connection_parser.parse(d) for d in mcp_connection_definitions]

            if not any([tools_to_add, prompts_to_add, resources_to_add, mcp_to_add]):
                self._console.print("Advertencia: No se especificaron componentes para añadir.")
                raise typer.Exit()
            
            count, warnings, backup_message = self._update_use_case.execute(
                tools_to_add, prompts_to_add, resources_to_add, mcp_to_add
            )

            if warnings:
                self._console.print("\nAdvertencias durante la validación:")
                for warning in warnings:
                    self._console.print(f"- {warning}")

            self._console.print(f"\n¡Éxito! Se añadieron {count} componente(s) al proyecto.")
            self._console.print(f"Info Backup: {backup_message}")

        except typer.Exit as e:
            raise e
        except (ValueError, FileNotFoundError) as e:
            self._console.print(f"Error: {e}")
            raise typer.Exit(code=1)
        except RuntimeError as e:
            self._console.print(f"Error Crítico durante la inyección: {e}")
            raise typer.Exit(code=1)
        except Exception as e:
            self._console.print(f"Ocurrió un error inesperado:\n{e}")
            raise typer.Exit(code=1)
    
    def handle_from_file(self, config_file: Path, output_dir: Path) -> None:
        """Handle project generation from JSON file."""
        self._console.print(f"Reading configuration from: {config_file}")
        
        try:
            with config_file.open("r") as f:
                data = json.load(f)
            

            if 'project_type' not in data:
                data['project_type'] = 'mcp_server'

            project_request = ProjectRequest.model_validate(data)
            self._execute_generation(project_request, output_dir, no_zip=False)
            
        except Exception as e:
            self._console.print(f"An unexpected error occurred:\n{e}")
            raise typer.Exit(code=1)
    
    def handle_create(
        self,
        project_name: str,
        project_type: str,
        mcp_connection_definitions: List[str],
        tool_definitions: List[str],
        prompt_definitions: List[str],
        resource_definitions: List[str],
        output_dir: Path,
        no_zip: bool
    ) -> None:
        """Handle direct project creation with definitions."""
        try:

            valid_types = ["mcp_server", "agent_procode"]
            if project_type not in valid_types:
                self._console.print(f"Error: Tipo de proyecto '{project_type}' inválido. Opciones válidas: {valid_types}")
                raise typer.Exit(code=1)


            if project_type == "mcp_server":
                project_name_pattern = r"^[a-z]+(_[a-z0-9]+)*_smcp$"
                if not project_name.endswith("_smcp"):
                    self._console.print(f"Error: Proyectos 'mcp_server' deben terminar con el sufijo '_smcp'. (Ej: '{project_name}_smcp')")
                    raise typer.Exit(code=1)
                if not re.match(project_name_pattern, project_name):
                    self._console.print(f"Error: Nombre de proyecto 'mcp_server' debe estar en snake_case y terminar con '_smcp'.")
                    raise typer.Exit(code=1)
            

            if project_type == "agent_procode" and any([tool_definitions, prompt_definitions, resource_definitions]):
                self._console.print("Advertencia: --tool, --prompt, y --resource son ignorados para 'agent_procode'.")
            
            if project_type == "mcp_server" and mcp_connection_definitions:
                self._console.print("Advertencia: --mcp-connections es ignorado para 'mcp_server'.")

            self._console.print(f"Nombre de proyecto '{project_name}' validado.")


            dynamic_tools = [self._tool_parser.parse(d) for d in tool_definitions]
            dynamic_prompts = [self._prompt_parser.parse(d) for d in prompt_definitions]
            dynamic_resources = [self._resource_parser.parse(d) for d in resource_definitions]
            mcp_connections = [self._mcp_connection_parser.parse(d) for d in mcp_connection_definitions]

            self._console.print(f"Creando proyecto '{project_name}' (Tipo: {project_type}) con:")
            if project_type == "mcp_server":
                self._console.print(f"  - {len(dynamic_tools)} tools")
                self._console.print(f"  - {len(dynamic_prompts)} prompts")
                self._console.print(f"  - {len(dynamic_resources)} resources")
            else:
                self._console.print(f"  - {len(mcp_connections)} conexiones MCP")


            project_request = ProjectRequest(
                project_name=project_name,
                project_type=project_type,
                mcp_connections=mcp_connections,
                dynamic_tools=dynamic_tools,
                dynamic_prompts=dynamic_prompts,
                dynamic_resources=dynamic_resources
            )

            self._execute_generation(project_request, output_dir, no_zip)
             
        except ValueError as e:
            self._console.print(f"Error parsing definition: {e}")
            raise typer.Exit(code=1)
        except Exception as e:
            self._console.print(f"An unexpected error occurred:\n{e}")
            raise typer.Exit(code=1)
    
    def handle_interactive(self, output_dir: Path) -> None:
        """Handle interactive project creation."""
        try:
            self._console.print("Generador Interactivo de Proyectos\n")
            
            project_type = Prompt.ask(
                "¿Qué tipo de proyecto quieres generar?",
                choices=["mcp_server", "agent_procode"],
                default="mcp_server"
            )

            project_name = Prompt.ask("Nombre del proyecto")


            if project_type == "mcp_server":
                if not project_name.endswith("_smcp"):
                    project_name += "_smcp"
                    self._console.print(f"Nombre ajustado a: [bold]{project_name}[/bold]")

            dynamic_tools = []
            dynamic_prompts = []
            dynamic_resources = []
            mcp_connections = []

            if project_type == "mcp_server":
                dynamic_tools = self._collect_items_interactively("tool", self._create_tool_interactively)
                dynamic_prompts = self._collect_items_interactively("prompt", self._create_prompt_interactively)
                dynamic_resources = self._collect_items_interactively("resource", self._create_resource_interactively)
            else:
                mcp_connections = self._collect_items_interactively("conexión MCP", self._create_mcp_connection_interactively)
                if not mcp_connections:
                    self._console.print("Advertencia: No se definieron conexiones MCP. El agente se creará sin tools.")

            self._show_project_summary(project_name, project_type, mcp_connections, dynamic_tools, dynamic_prompts, dynamic_resources)
            
            if Confirm.ask("\n¿Generar proyecto?"):
                project_request = ProjectRequest(
                    project_name=project_name,
                    project_type=project_type,
                    mcp_connections=mcp_connections,
                    dynamic_tools=dynamic_tools,
                    dynamic_prompts=dynamic_prompts,
                    dynamic_resources=dynamic_resources
                )
                self._execute_generation(project_request, output_dir, no_zip=False)
            else:
                self._console.print("Generación de proyecto cancelada.")
        
        except Exception as e:
            self._console.print(f"An unexpected error occurred:\n{e}")
            raise typer.Exit(code=1)
    
    def _collect_items_interactively(self, item_name: str, creation_func) -> List[dict]:
        """Generic function to collect items (tools, prompts, etc.) interactively."""
        items = []
        self._console.print(f"\n--- Definición de {item_name.capitalize()}s ---")
        while True:
            add_item = Confirm.ask(f"¿Añadir un/a {item_name}?")
            if add_item:
                item = creation_func()
                items.append(item)
            else:
                break
        return items
    
    def _create_mcp_connection_interactively(self) -> dict:
        self._console.print("\nCreando una nueva Conexión MCP:")
        name = Prompt.ask("Nombre de la conexión (e.g., 'mcp_principal')")
        endpoint = Prompt.ask("Endpoint URL (e.g., 'http://localhost:3000')")
        return {"name": name, "endpoint": endpoint}

    def _create_tool_interactively(self) -> dict:
        self._console.print("\nCreando una nueva tool:")
        name = Prompt.ask("Nombre de la Tool (snake_case)")
        description = Prompt.ask("Descripción")
        params = Prompt.ask("Parámetros (e.g., 'location: str, limit: int = 10')", default="")
        return_type = Prompt.ask("Tipo de Retorno", default="Dict[str, Any]")
        return {"name": name, "description": description, "params": params, "return_type": return_type}

    def _create_prompt_interactively(self) -> dict:
        self._console.print("\nCreando un nuevo prompt:")
        name = Prompt.ask("Nombre del Prompt (snake_case)")
        description = Prompt.ask("Descripción")
        return {"name": name, "description": description}

    def _create_resource_interactively(self) -> dict:
        self._console.print("\nCreando un nuevo resource:")
        name = Prompt.ask("Nombre del Resource (snake_case)")
        uri = Prompt.ask("URI del Resource (e.g., 'policy://{id}')")
        description = Prompt.ask("Descripción")
        params = Prompt.ask("Parámetros (e.g., 'id: str')", default="")
        return_type = Prompt.ask("Tipo de Retorno", default="Dict[str, Any]")
        return {"name": name, "uri": uri, "description": description, "params": params, "return_type": return_type}

    def _show_project_summary(
        self,
        project_name: str,
        project_type: str,
        mcp_connections: List[Dict],
        tools: List[Dict],
        prompts: List[Dict],
        resources: List[Dict]
    ) -> None:
        self._console.print(f"\n Resumen del Proyecto ")
        self._console.print(f"Proyecto: {project_name}")
        self._console.print(f"Tipo:     {project_type}")
        
        if project_type == "agent_procode":
            self._console.print(f"\n Conexiones MCP ({len(mcp_connections)}):")
            if not mcp_connections: self._console.print("   Ninguna")
            for i, conn in enumerate(mcp_connections, 1): self._console.print(f"  {i}. {conn['name']} ({conn['endpoint']})")
        else:
            self._console.print(f"\n Tools ({len(tools)}):")
            if not tools: self._console.print("   Ninguna")
            for i, tool in enumerate(tools, 1): self._console.print(f"  {i}. {tool['name']}")

            self._console.print(f"\n Prompts ({len(prompts)}):")
            if not prompts: self._console.print("   Ninguno")
            for i, prompt in enumerate(prompts, 1): self._console.print(f"  {i}. {prompt['name']}")

            self._console.print(f"\n Resources ({len(resources)}):")
            if not resources: self._console.print("   Ninguno")
            for i, resource in enumerate(resources, 1): self._console.print(f"  {i}. {resource['name']} ({resource['uri']})")
    
    def _execute_generation(self, project_request: ProjectRequest, output_dir: Path, no_zip: bool) -> None:
            result = None
            temp_dir_to_clean = None
            try:
                self._console.print(f"\nIniciando generación para: '{project_request.project_name}' (Tipo: {project_request.project_type})")

                result = self._generation_use_case.execute(project_request, no_zip)
                temp_dir_to_clean = result.temp_dir

                if result.zip_path:
                    final_zip_path = output_dir / result.zip_filename
                    if final_zip_path.exists():
                        self._console.print(f"Error: El archivo '{final_zip_path}' ya existe.")
                        raise typer.Exit(code=1)
                    shutil.move(result.zip_path, final_zip_path)
                    self._console.print(f"\n ¡Éxito! Proyecto ZIP creado en: {final_zip_path}")
                elif result.output_path:
                    source_folder_path = Path(result.output_path)
                    generated_folder_name = source_folder_path.name
                    final_folder_path = output_dir / generated_folder_name

                    if final_folder_path.exists():
                        self._console.print(f"Error: El directorio '{final_folder_path}' ya existe.")
                        if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
                            shutil.rmtree(temp_dir_to_clean)
                        raise typer.Exit(code=1)

                    shutil.move(str(source_folder_path), str(final_folder_path))
                    self._console.print(f"\n ¡Éxito! Archivos del proyecto generados en: {final_folder_path}")
                else:
                    raise RuntimeError("La generación finalizó pero no se proporcionó ruta de salida (zip o carpeta).")

            except Exception as e:
                self._console.print(f"Ocurrió un error inesperado:\n{e}")
                if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
                    try:
                        shutil.rmtree(temp_dir_to_clean)
                    except Exception as cleanup_error:
                        self._console.print(f"Error limpiando directorio temporal {temp_dir_to_clean}: {cleanup_error}")
                raise typer.Exit(code=1)
            finally:
                if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
                    try:
                        shutil.rmtree(temp_dir_to_clean)
                    except Exception as cleanup_error:
                        self._console.print(f"Advertencia: Fallo al limpiar directorio temporal {temp_dir_to_clean}: {cleanup_error}")
    
    def handle_restore_backup(self, backup_name: Optional[str], force: bool) -> None:
        try:
            inventory = self._analyzer.analyze(".")
            if not inventory.is_valid:
                self._console.print("Error: No se encontró un proyecto válido en el directorio actual.")
                raise typer.Exit(code=1)
            

            # if inventory.project_type != "mcp_server":
            #     self._console.print(f"Error: El comando 'restore-backup' solo está disponible para proyectos 'mcp_server'.")
            #     self._console.print(f"Este proyecto fue detectado como: '{inventory.project_type}'")
            #     raise typer.Exit(code=1)


            project_path = inventory.project_path
            available_backups = self._restore_use_case.list_backups(project_path)

            if not available_backups:
                self._console.print("No se encontraron backups disponibles.")
                raise typer.Exit()

            if backup_name is None:
                self._console.print("Backups disponibles (más recientes primero):")
                for i, bk_name in enumerate(available_backups):
                    self._console.print(f"  {i + 1}. {bk_name}")
                self._console.print("\nUsa 'scaffold-py restore-backup <nombre_backup>' para restaurar.")
                return
            else:
                if backup_name not in available_backups:
                    self._console.print(f"Error: El backup '{backup_name}' no existe.")
                    self._console.print("Backups disponibles:")
                    for bk_name in available_backups:
                        self._console.print(f"  - {bk_name}")
                    raise typer.Exit(code=1)

                if not force:
                    confirmed = Confirm.ask(
                        f"¿Estás seguro de que quieres restaurar desde '{backup_name}'?\n"
                        f"Esto reemplazará el contenido actual de la carpeta 'src'.",
                        default=False
                    )
                    if not confirmed:
                        self._console.print("Restauración cancelada.")
                        raise typer.Exit()

                self._console.print(f"Restaurando desde '{backup_name}'...")
                result_message = self._restore_use_case.execute(project_path, backup_name)
                self._console.print(f"¡Éxito! {result_message}")


        except typer.Exit as e:
            raise e
        except (FileNotFoundError, ValueError) as e:
            self._console.print(f"Error: {e}")
            raise typer.Exit(code=1)
        except RuntimeError as e:
            self._console.print(f"Error Crítico durante la restauración: {e}")
            raise typer.Exit(code=1)
        except Exception as e:
            self._console.print(f"Ocurrió un error inesperado:\n{e}")
            raise typer.Exit(code=1)