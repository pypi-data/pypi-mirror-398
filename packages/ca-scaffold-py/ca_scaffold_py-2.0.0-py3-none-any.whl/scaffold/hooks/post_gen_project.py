#!/usr/bin/env python
import json
import os
import sys
import shutil
from typing import List, Dict, Any

PROJECT_TYPE = "{{ cookiecutter.project_type }}"
PROJECT_NAME = "{{ cookiecutter.project_name }}"
PROJECT_SLUG = "{{ cookiecutter.project_slug }}"

BASE_PROJECT_PATH = os.getcwd()

TEMPLATE_DIR = os.path.join(BASE_PROJECT_PATH, "templates")
MCP_SERVER_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "mcp_server")
AGENT_PROCODE_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "agent_procode")

SELECTED_TEMPLATE_PATH = ""
if PROJECT_TYPE == "mcp_server":
    SELECTED_TEMPLATE_PATH = MCP_SERVER_TEMPLATE_PATH
elif PROJECT_TYPE == "agent_procode":
    SELECTED_TEMPLATE_PATH = AGENT_PROCODE_TEMPLATE_PATH
else:
    print(f"ERROR FATAL: Tipo de proyecto '{PROJECT_TYPE}' no reconocido.")
    sys.exit(1)

try:
    import generation_utils as utils
    GENERATION_UTILS_FOUND = True
    print(f"generation_utils.py importado exitosamente desde: /tmp")
except ImportError as e:
    print(f"ADVERTENCIA: No se encontró 'generation_utils.py'.")
    print(f"Buscando en: /tmp")
    print(f"Error: {e}")
    print("La generación dinámica para 'mcp_server' fallará.")
    utils = None
    GENERATION_UTILS_FOUND = False
except Exception as e:
    print(f"Error inesperado importando generation_utils: {e}")
    GENERATION_UTILS_FOUND = False
    utils = None

def move_template_files(template_path: str):
    """Mueve el contenido de la plantilla seleccionada (mcp_server o agent_procode)
    desde la subcarpeta 'templates' al directorio raíz del proyecto (CWD)."""
    
    print(f"Moviendo plantilla '{PROJECT_TYPE}' desde: {template_path}...")
    if not os.path.exists(template_path):
        print(f"ERROR FATAL: El directorio de plantilla '{template_path}' no existe.")
        sys.exit(1)

    for item in os.listdir(template_path):
        source_item = os.path.join(template_path, item)
        dest_item = os.path.join(BASE_PROJECT_PATH, item)
        
        try:

            if os.path.isdir(source_item):

                if os.path.exists(dest_item):
                    shutil.rmtree(dest_item)
                shutil.copytree(source_item, dest_item)
                shutil.rmtree(source_item)
            else:
                shutil.move(source_item, dest_item)
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo mover '{source_item}' a '{dest_item}': {e}")
    print(f"Plantilla '{PROJECT_TYPE}' movida a '{BASE_PROJECT_PATH}'")
def cleanup_template_dir():
    """Elimina la carpeta 'templates' (que ahora está vacía) después de mover los archivos."""
    print("Limpiando directorio 'templates'...")
    try:
        shutil.rmtree(TEMPLATE_DIR)
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo eliminar el directorio 'templates': {e}")
    
def create_mcp_server(final_project_path: str):
    """Ejecuta la lógica de post-generación para un mcp_server."""
    if not GENERATION_UTILS_FOUND:
        print("ERROR: No se pueden crear tools/prompts/resources porque 'generation_utils' no se importó.")
        return
    print("Ejecutando post-generación para 'mcp_server'...")

    source_env = os.path.join(final_project_path, "src/applications/config/settings_template.txt")
    target_env = os.path.join(final_project_path, "src/applications/config/.env.local")
    
    if os.path.exists(source_env):
        try:
            os.rename(source_env, target_env)
            print(f"Renombrado env.local a .env.local exitosamente.")
        except OSError as e:
            print(f"ADVERTENCIA: No se pudo renombrar {source_env}: {e}")
            
    tools_json = r'''{{ cookiecutter.dynamic_tools }}'''
    prompts_json = r'''{{ cookiecutter.dynamic_prompts }}'''
    resources_json = r'''{{ cookiecutter.dynamic_resources }}'''
    try:
        tools_to_create = json.loads(tools_json) if tools_json and tools_json.strip() != '[]' else []
        if tools_to_create:
            print(f"Creando {len(tools_to_create)} tool(s) dinámicas...")
            for tool in tools_to_create:
                if isinstance(tool, dict) and tool.get('name'):
                     create_tool(tool, final_project_path)
                else:
                     print(f"ADVERTENCIA: Ignorando entrada de tool inválida: {tool}")
        else:
            print("No se definieron tools dinámicas.")
        prompts_to_create = json.loads(prompts_json) if prompts_json and prompts_json.strip() != '[]' else []
        if prompts_to_create:
            print(f"Creando {len(prompts_to_create)} prompt(s) dinámicos...")
            for prompt in prompts_to_create:
                 if isinstance(prompt, dict) and prompt.get('name'):
                      create_prompt(prompt, final_project_path)
                 else:
                      print(f"ADVERTENCIA: Ignorando entrada de prompt inválida: {prompt}")
        else:
            print("No se definieron prompts dinámicos.")
        resources_to_create = json.loads(resources_json) if resources_json and resources_json.strip() != '[]' else []
        if resources_to_create:
            print(f"Creando {len(resources_to_create)} resource(s) dinámicos...")
            for resource in resources_to_create:
                 if isinstance(resource, dict) and resource.get('name'):
                      create_resource(resource, final_project_path)
                 else:
                      print(f"ADVERTENCIA: Ignorando entrada de resource inválida: {resource}")
        else:
            print("No se definieron resources dinámicos.")
    except json.JSONDecodeError as e:
        print(f"Error fatal (mcp_server): JSON de cookiecutter inválido.")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fatal inesperado (mcp_server): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
def create_tool(tool: Dict[str, Any], base_path: str):
    """Lógica para crear una única tool (de tu script original)."""
    try:
        tool_name = tool.get('name')
        if not tool_name: raise ValueError("Nombre de tool no encontrado.")
        description = tool.get('description', f'Tool para {tool_name}')
        params_str = tool.get('params', '')
        internal_return_type = tool.get('return_type', 'Dict[str, Any]')
        camel_name = utils.to_camel_case(tool_name)
        camel_response_name = f"{camel_name}Response"
        camel_adapter_name = f"{camel_name}Adapter"
        camel_error_name = f"{camel_name}Error"
        params_list = utils.parse_params(params_str)
        params_sig_no_self = utils.format_params_for_sig(params_list, include_self=False)
        params_call_no_self = utils.format_params_for_call(params_list, include_self=False)
        model_path = os.path.join(base_path, f"src/domain/model/{tool_name}/{tool_name}_model.py")
        gateway_path = os.path.join(base_path, f"src/domain/model/{tool_name}/gateways/{tool_name}_adapter.py")
        error_path = os.path.join(base_path, f"src/domain/model/errors/{tool_name}_error.py")
        use_case_path = os.path.join(base_path, f"src/domain/usecase/{tool_name}_use_case.py")
        adapter_path = os.path.join(base_path, f"src/infrastructure/driven_adapters/api_connect_adapter/adapter/{tool_name}_api_adapter.py")
        use_case_test_path = os.path.join(base_path, f"tests/unit-test/src/domain/usecase/test_{tool_name}_use_case.py")
        adapter_test_path = os.path.join(base_path, f"tests/unit-test/src/infrastructure/driven_adapters/test_{tool_name}_api_adapter.py")
        settings_path = os.path.join(base_path, "src/applications/settings/settings.py")
        container_path = os.path.join(base_path, "src/applications/settings/container.py")
        adapter_init_path = os.path.join(base_path, "src/infrastructure/driven_adapters/api_connect_adapter/__init__.py")
        tools_path = os.path.join(base_path, "src/infrastructure/entry_points/mcp/tools.py")
        errors_init_path = os.path.join(base_path, "src/domain/model/errors/__init__.py")
        print(f"Creando archivos para tool '{tool_name}'...")
        utils.create_file(model_path, utils.get_domain_model_template(tool_name, camel_name))
        utils.create_file(gateway_path, utils.get_domain_gateway_template(tool_name, camel_name, params_sig_no_self, camel_response_name))
        utils.create_file(error_path, utils.get_domain_error_template(tool_name, camel_error_name))
        utils.create_file(use_case_path, utils.get_use_case_template(tool_name, camel_name, params_sig_no_self, params_call_no_self, camel_response_name, camel_adapter_name, camel_error_name))
        utils.create_file(adapter_path, utils.get_adapter_template(tool_name, camel_name, params_sig_no_self, params_call_no_self, camel_response_name, camel_adapter_name, camel_error_name))
        utils.create_file(use_case_test_path, utils.get_use_case_test_template(tool_name, camel_name, camel_adapter_name, camel_error_name, camel_response_name, params_list))
        utils.create_file(adapter_test_path, utils.get_adapter_test_template(tool_name, camel_name, camel_adapter_name, camel_error_name, camel_response_name, params_list))
        utils.create_file(os.path.join(base_path, f"src/domain/model/{tool_name}/__init__.py"), "")
        utils.create_file(os.path.join(base_path, f"src/domain/model/{tool_name}/gateways/__init__.py"), "")
        if not os.path.exists(errors_init_path):
             utils.create_file(errors_init_path, f"# Automatically generated __init__.py\n\n__all__ = []\n")
        utils.add_code_to_file(errors_init_path, "# Automatically generated __init__.py", f"from .{tool_name}_error import {camel_error_name}\n__all__.append(\"{camel_error_name}\")\n")
        print(f"Registrando tool '{tool_name}' en archivos centrales...")
        utils.add_code_to_file(settings_path, "# ANCHOR_SETTINGS_FIELD (no borrar)", utils.get_settings_field_template(tool_name))
        utils.add_code_to_file(settings_path, "# ANCHOR_SETTINGS_VALIDATOR (no borrar)", utils.get_settings_validator_template(tool_name))
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_IMPORT (no borrar)", utils.get_container_import_template(tool_name, camel_name))
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_ADAPTER_IMPORT (no borrar)", utils.get_container_adapter_import_template(tool_name, camel_name))
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_ADAPTER (no borrar)", utils.get_container_adapter_template(tool_name, camel_name))
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_USE_CASE (no borrar)", utils.get_container_use_case_template(tool_name, camel_name))
        utils.add_code_to_file(adapter_init_path, "# ANCHOR_ADAPTER_INIT_IMPORT (no borrar)", utils.get_adapter_init_import_template(tool_name, camel_name))
        utils.add_code_to_file(adapter_init_path, "# ANCHOR_ADAPTER_INIT_ALL (no borrar)", utils.get_adapter_init_all_template(tool_name, camel_name))
        utils.add_code_to_file(tools_path, "# ANCHOR_TOOLS_IMPORT (no borrar)", utils.get_tools_import_template(tool_name, camel_name))
        utils.add_code_to_file(tools_path, "# ANCHOR_TOOLS_PROVIDE (no borrar)", utils.get_tools_provide_template(tool_name, camel_name))
        utils.add_code_to_file(tools_path, "# ANCHOR_TOOLS_BIND (no borrar)", utils.get_tools_bind_template(tool_name, params_sig_no_self, params_call_no_self, description))
        print(f"Tool '{tool_name}' creada exitosamente.")
    except ValueError as ve:
         print(f"ERROR al procesar datos para la tool '{tool.get('name', 'desconocida')}': {ve}")
    except Exception as e:
         print(f"ERROR inesperado creando tool '{tool.get('name', 'desconocida')}': {e}")
         pass
def create_prompt(prompt: Dict[str, Any], base_path: str):
    """Lógica para crear un único prompt (de tu script original)."""
    try:
        prompt_name = prompt.get('name')
        if not prompt_name: raise ValueError("Nombre de prompt no encontrado.")
        description = prompt.get('description', f'Prompt {prompt_name}')
        camel_prompt_name = utils.to_camel_case(prompt_name)
        use_case_module_name = f"get_{prompt_name}_usecase"
        use_case_path = os.path.join(base_path, f"src/domain/usecase/{use_case_module_name}.py")
        adapter_content_dir = os.path.join(base_path, "src/infrastructure/driven_adapters/prompts/content")
        txt_filepath = os.path.join(adapter_content_dir, f"{prompt_name}.txt")
        container_path = os.path.join(base_path, "src/applications/settings/container.py")
        prompts_path = os.path.join(base_path, "src/infrastructure/entry_points/mcp/prompts.py")
        print(f"Creando archivos para prompt '{prompt_name}'...")
        utils.create_file(use_case_path, utils.get_prompt_use_case_template(prompt_name, camel_prompt_name))
        utils.create_file(txt_filepath, utils.get_prompt_content_template(prompt_name, description))
        print(f"Registrando prompt '{prompt_name}' en archivos centrales...")
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_IMPORT (no borrar)", utils.get_container_prompt_import_template(prompt_name, camel_prompt_name))
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_USE_CASE (no borrar)", utils.get_container_prompt_use_case_template(prompt_name, camel_prompt_name))
        utils.add_code_to_file(prompts_path, "# ANCHOR_PROMPTS_IMPORT (no borrar)", utils.get_prompts_import_template(prompt_name, camel_prompt_name))
        utils.add_code_to_file(prompts_path, "# ANCHOR_PROMPTS_PROVIDE (no borrar)", utils.get_prompts_provide_template(prompt_name, camel_prompt_name))
        utils.add_code_to_file(prompts_path, "# ANCHOR_PROMPTS_BIND (no borrar)", utils.get_prompts_bind_template(prompt_name, description))
        print(f"Prompt '{prompt_name}' creado exitosamente.")
    except ValueError as ve:
         print(f"ERROR al procesar datos para el prompt '{prompt.get('name', 'desconocida')}': {ve}")
    except Exception as e:
         print(f"ERROR inesperado creando prompt '{prompt.get('name', 'desconocida')}': {e}")
         pass
def create_resource(resource: Dict[str, Any], base_path: str):
    """Lógica para crear un único resource (de tu script original)."""
    try:
        resource_name = resource.get('name')
        if not resource_name: raise ValueError("Nombre de resource no encontrado.")
        uri = resource.get('uri', f"resource://{resource_name}")
        description = resource.get('description', f'Resource {resource_name}')
        params_str = resource.get('params', '')
        return_type = resource.get('return_type', 'Dict[str, Any]')
        camel_resource_name = utils.to_camel_case(resource_name)
        use_case_module_name = f"get_{resource_name}_usecase"
        adapter_module_name = f"{resource_name}_adapter"
        gateway_module_name = f"{resource_name}_gateway"
        params_list = utils.parse_params(params_str)
        params_sig_no_self = utils.format_params_for_sig(params_list, include_self=False)
        params_call_no_self = utils.format_params_for_call(params_list, include_self=False)
        gateway_path = os.path.join(base_path, f"src/domain/model/{resource_name}/gateways/{gateway_module_name}.py")
        use_case_path = os.path.join(base_path, f"src/domain/usecase/{use_case_module_name}.py")
        adapter_path = os.path.join(base_path, f"src/infrastructure/driven_adapters/local_files/{adapter_module_name}.py")
        container_path = os.path.join(base_path, "src/applications/settings/container.py")
        resources_path = os.path.join(base_path, "src/infrastructure/entry_points/mcp/resources.py")
        print(f"Creando archivos para resource '{resource_name}'...")
        utils.create_file(gateway_path, utils.get_resource_gateway_template(resource_name, camel_resource_name, params_sig_no_self, return_type))
        utils.create_file(use_case_path, utils.get_resource_use_case_template(resource_name, camel_resource_name, params_sig_no_self, params_call_no_self, return_type))
        utils.create_file(adapter_path, utils.get_resource_adapter_template(resource_name, camel_resource_name, params_sig_no_self, params_call_no_self, return_type))
        utils.create_file(os.path.join(base_path, f"src/domain/model/{resource_name}/__init__.py"), "")
        utils.create_file(os.path.join(base_path, f"src/domain/model/{resource_name}/gateways/__init__.py"), "")
        print(f"Registrando resource '{resource_name}' en archivos centrales...")
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_IMPORT (no borrar)", utils.get_container_resource_import_template(resource_name, camel_resource_name))
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_ADAPTER (no borrar)", utils.get_container_resource_adapter_template(resource_name, camel_resource_name))
        utils.add_code_to_file(container_path, "# ANCHOR_CONTAINER_USE_CASE (no borrar)", utils.get_container_resource_use_case_template(resource_name, camel_resource_name))
        utils.add_code_to_file(resources_path, "# ANCHOR_RESOURCES_IMPORT (no borrar)", utils.get_resources_import_template(resource_name, camel_resource_name))
        utils.add_code_to_file(resources_path, "# ANCHOR_RESOURCES_PROVIDE (no borrar)", utils.get_resources_provide_template(resource_name, camel_resource_name))
        utils.add_code_to_file(resources_path, "# ANCHOR_RESOURCES_BIND (no borrar)", utils.get_resources_bind_template(resource_name, uri, description, params_sig_no_self, params_call_no_self, return_type))
        print(f"Resource '{resource_name}' creado exitosamente.")
    except ValueError as ve:
         print(f"ERROR al procesar datos para el resource '{resource.get('name', 'desconocida')}': {ve}")
    except Exception as e:
         print(f"ERROR inesperado creando resource '{resource.get('name', 'desconocida')}': {e}")
         pass
    
def create_agent_procode(final_project_path: str):
    """Ejecuta la lógica de post-generación para un agent_procode."""
    print("Ejecutando post-generación para 'agent_procode'...")

    source_env = os.path.join(final_project_path, "application/settings/settings_template.txt")
    target_env = os.path.join(final_project_path, "application/settings/.env.example")
    
    if os.path.exists(source_env):
        try:
            os.rename(source_env, target_env)
            print(f"Renombrado env.example a .env.example exitosamente.")
        except OSError as e:
            print(f"ADVERTENCIA: No se pudo renombrar {source_env}: {e}")
            target_env = source_env

    mcp_connections_json = r'''{{ cookiecutter.mcp_connections_json }}'''
    
    try:
        connections = json.loads(mcp_connections_json)
        if not isinstance(connections, list) or not all(isinstance(c, dict) for c in connections):
            raise ValueError("mcp_connections_json no es una lista de diccionarios válida.")
        
        print(f"Configurando {len(connections)} conexión(es) MCP...")
        
        # Generar contenido para .env.example
        env_example_path = os.path.join(final_project_path, "application", "settings", ".env.example")
        if os.path.exists(env_example_path):
            append_to_env_example(env_example_path, connections)
        else:
            print(f"ADVERTENCIA: No se encontró .env.example en {env_example_path}. No se pudieron añadir variables de entorno de MCP.")
            
    except json.JSONDecodeError as e:
        print(f"Error fatal (agent_procode): JSON de 'mcp_connections_json' inválido.")
        print(f"Error: {e}")
        print(f"JSON recibido: {mcp_connections_json}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fatal inesperado (agent_procode): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
def append_to_env_example(filepath: str, connections: List[Dict[str, str]]):
    """Añade las variables de entorno de conexión MCP al .env.example."""
    print(f"Actualizando {filepath} con variables de conexión MCP...")
    
    env_content = """\n\n# ============================================
# MCP (Model Context Protocol) Connections
# ============================================
# Variables generadas dinámicamente por el scaffold.
# El archivo settings.py las leerá automáticamente.
"""
    
    for i, conn in enumerate(connections, 1):
        name = conn.get("name", f"mcp_conn_{i}")
        endpoint = conn.get("endpoint", "http://example.com")
        
        env_content += f"\nMCP_CONNECTION_{i}_NAME={name}\n"
        env_content += f"MCP_CONNECTION_{i}_ENDPOINT={endpoint}\n"
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(env_content)
        print("Variables de entorno de MCP añadidas a .env.example.")
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo escribir en {filepath}: {e}")
def main():
    print(f"Iniciando hook post_gen_project.py para '{PROJECT_NAME}'...")
    print(f"Tipo de proyecto seleccionado: {PROJECT_TYPE}")

    move_template_files(SELECTED_TEMPLATE_PATH)

    if PROJECT_TYPE == "mcp_server":
        create_mcp_server(BASE_PROJECT_PATH)
    elif PROJECT_TYPE == "agent_procode":
        create_agent_procode(BASE_PROJECT_PATH)
        
    cleanup_template_dir()
    print(f"Hook post_gen_project.py finalizado exitosamente para '{BASE_PROJECT_PATH}'.")
    sys.exit(0)
if __name__ == "__main__":
    main()