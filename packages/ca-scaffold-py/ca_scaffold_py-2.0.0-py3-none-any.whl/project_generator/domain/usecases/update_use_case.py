import os
import shutil
import logging
import re
import ast
from datetime import datetime
from typing import List, Dict, Any, Tuple
from project_generator.domain.models.project_models import ProjectAnalyzerGateway, CodeInjectorGateway, ProjectInventory

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class UpdateProjectUseCase:
    """Use case that orchestrates updating an existing project with backups and validations."""
    def __init__(self, analyzer: ProjectAnalyzerGateway, injector: CodeInjectorGateway):
        self._analyzer = analyzer
        self._injector = injector
        self._backup_dir_name = ".mcp_backups"
        self._max_backups = 5

    def execute(self, tools_to_add: List[Dict], prompts_to_add: List[Dict], resources_to_add: List[Dict], mcp_connections_to_add: List[Dict] = []) -> Tuple[int, List[str], str]:
        inventory = self._analyzer.analyze(".")
        if not inventory.is_valid:
            raise FileNotFoundError("No se encontró un proyecto válido en el directorio actual.")
        
        if inventory.project_type == "mcp_server":
            if mcp_connections_to_add:
                raise ValueError("No se pueden añadir conexiones MCP a un proyecto tipo 'mcp_server'.")
        elif inventory.project_type == "agent_procode":
            if any([tools_to_add, prompts_to_add, resources_to_add]):
                raise ValueError("Solo se pueden añadir conexiones MCP a un proyecto tipo 'agent_procode'.")

        warnings = []
        backup_path = None

        try:
            logger.info("Validando nuevos componentes...")
            if inventory.project_type == "mcp_server":
                self._validate_name_collisions(tools_to_add, prompts_to_add, resources_to_add, inventory)
                validation_warnings = self._validate_components(tools_to_add, prompts_to_add, resources_to_add, inventory)
                warnings.extend(validation_warnings)
            elif inventory.project_type == "agent_procode":
                self._validate_mcp_collisions(mcp_connections_to_add, inventory)

            component_count = len(tools_to_add) + len(prompts_to_add) + len(resources_to_add) + len(mcp_connections_to_add)
            
            if component_count == 0:
                return 0, warnings, "No components specified to add."

            logger.info("Creando backup del proyecto...")
            backup_path = self._create_backup(inventory.project_path, inventory.project_type)
            logger.info(f"Backup creado en: {backup_path}")

            logger.info("Inyectando código...")
            try:
                if inventory.project_type == "mcp_server":
                    if tools_to_add: self._injector.inject_tools(tools_to_add, inventory)
                    if prompts_to_add: self._injector.inject_prompts(prompts_to_add, inventory)
                    if resources_to_add: self._injector.inject_resources(resources_to_add, inventory)
                elif inventory.project_type == "agent_procode":
                    if mcp_connections_to_add: self._injector.inject_mcp_connections(mcp_connections_to_add, inventory)
            
            except Exception as injection_error:
                logger.error(f"¡Fallo durante la inyección de código!: {injection_error}")
                logger.info("Intentando restaurar desde el backup...")
                self._restore_backup(backup_path, inventory.project_path, inventory.project_type)
                raise RuntimeError(f"La inyección falló y el proyecto fue restaurado. Error: {injection_error}") from injection_error

            success_message = f"Backup exitoso en: {backup_path}"
            return component_count, warnings, success_message

        except (ValueError, FileNotFoundError) as validation_error:
            logger.error(f"Error de validación: {validation_error}")
            raise validation_error
        except Exception as general_error:
            logger.error(f"Error inesperado durante la actualización: {general_error}")
            if backup_path and os.path.exists(backup_path):
                try:
                    shutil.rmtree(backup_path)
                except Exception:
                    pass
            raise general_error

    def _validate_name_collisions(self, tools, prompts, resources, inventory):
        """Check for name collisions."""
        for tool in tools:
            if tool['name'] in inventory.existing_tools:
                raise ValueError(f"La herramienta '{tool['name']}' ya existe.")
        for prompt in prompts:
            if prompt['name'] in inventory.existing_prompts:
                raise ValueError(f"El prompt '{prompt['name']}' ya existe.")
        for resource in resources:
            if resource['name'] in inventory.existing_resources:
                raise ValueError(f"El recurso '{resource['name']}' ya existe.")

    def _validate_components(self, tools, prompts, resources, inventory) -> List[str]:
            """Perform advanced validations (, ) and collect warnings ()."""
            warnings = []

            logger.info(": Validando sintaxis de tipos de retorno...")
            for item in tools + resources:
                item_type = "Tool" if "return_type" in item and "uri" not in item else "Resource"
                name = item.get("name", "N/A")
                return_type = item.get("return_type")
                if return_type:
                    logger.debug(f"Validando tipo '{return_type}' para {item_type} '{name}'...")
                    try:
                        ast.parse(f"var: {return_type}")
                        logger.info(f"-> Tipo '{return_type}' para {item_type} '{name}' es VÁLIDO.")
                    except SyntaxError:
                        logger.error(f"-> Tipo '{return_type}' para {item_type} '{name}' es INVÁLIDO.")
                        raise ValueError(f"El tipo de retorno '{return_type}' para {item_type} '{name}' no es una anotación de tipo Python válida.")
                else:
                    warn_msg = f"{item_type} '{name}': No se especificó tipo de retorno, se usará Dict[str, Any] por defecto."
                    warnings.append(warn_msg)
                    logger.warning(f"-> {warn_msg}")
            logger.info(": Validación de tipos de retorno completada.")

            logger.info(": Validando colisiones de URI para Resources...")
            existing_uris = inventory.existing_resource_uris
            uri_patterns_to_add = {}
            logger.debug(f"URIs existentes normalizadas: {[re.sub(r'\{[^}]+\}', '{}', u) for u in existing_uris]}")

            for r in resources:
                name = r.get("name", "N/A")
                uri = r.get("uri")
                if not uri:
                    warn_msg = f"Resource '{name}': No se especificó URI, se usará 'resource://{name}' por defecto."
                    warnings.append(warn_msg)
                    logger.warning(f"-> {warn_msg}")
                    uri = f"resource://{name}"

                uri_pattern = re.sub(r'\{[^}]+\}', '{}', uri)
                logger.debug(f"Validando URI '{uri}' (patrón '{uri_pattern}') para Resource '{name}'...")

                if uri_pattern in uri_patterns_to_add:
                    collision_with = uri_patterns_to_add[uri_pattern]
                    logger.error(f"-> Conflicto INTERNO: '{uri}' colisiona con URI de '{collision_with}'.")
                    raise ValueError(f"Conflicto de URI detectado entre nuevos resources: '{uri}' (de '{name}') colisiona con URI de '{collision_with}'.")
                uri_patterns_to_add[uri_pattern] = name

                collision_found = False
                for existing_uri in existing_uris:
                    existing_pattern = re.sub(r'\{[^}]+\}', '{}', existing_uri)
                    if uri_pattern == existing_pattern:
                        logger.error(f"-> Conflicto EXISTENTE: '{uri}' colisiona con URI existente '{existing_uri}'.")
                        raise ValueError(f"Conflicto de URI detectado: El URI '{uri}' (de '{name}') colisiona con un resource existente ('{existing_uri}').")
                logger.info(f"-> URI '{uri}' para Resource '{name}' no colisiona.")

            logger.info(": Validación de URIs completada.")
            logger.info("--- Validaciones avanzadas finalizadas ---")
            return warnings

    def _validate_mcp_collisions(self, connections, inventory):
        for conn in connections:
            if conn['name'] in inventory.existing_mcp_connections:
                raise ValueError(f"La conexión MCP '{conn['name']}' ya existe.")

    def _create_backup(self, project_path: str, project_type: str) -> str:
        backup_root = os.path.join(project_path, self._backup_dir_name)
        os.makedirs(backup_root, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(backup_root, backup_name)
        
        try:
            if project_type == "mcp_server":
                source_path = os.path.join(project_path, "src")
                shutil.copytree(source_path, backup_path)
            elif project_type == "agent_procode":
                source_path = os.path.join(project_path, "application", "settings")
                shutil.copytree(source_path, backup_path)
            
            self._cleanup_old_backups(backup_root)
            return backup_path
        except Exception as e:
            raise OSError(f"No se pudo crear el backup en '{backup_path}': {e}") from e

    def _cleanup_old_backups(self, backup_root: str):
        """Removes the oldest backups if there are more than max_backups."""
        try:
            backups = sorted(
                [os.path.join(backup_root, d) for d in os.listdir(backup_root) if os.path.isdir(os.path.join(backup_root, d)) and d.startswith("backup_")],
                key=os.path.getmtime
            )

            while len(backups) > self._max_backups:
                oldest = backups.pop(0)
                shutil.rmtree(oldest)
                logger.info(f"Backup antiguo eliminado: {oldest}")
        except Exception as e:
            logger.warning(f"No se pudo limpiar backups antiguos: {e}")

    def _restore_backup(self, backup_path: str, project_path: str, project_type: str):
        try:
            target_path = ""
            if project_type == "mcp_server":
                target_path = os.path.join(project_path, "src")
            elif project_type == "agent_procode":
                target_path = os.path.join(project_path, "application", "settings")
            
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(backup_path, target_path)
        except Exception as e:
            logger.critical(f"¡FALLO CRÍTICO DURANTE LA RESTAURACIÓN!: {e}")