import os
import re
from typing import List, Dict, Any
from project_generator.domain.models.project_models import ProjectInventory
from project_generator.infrastructure import generation_utils as utils

class CodeInjectorAdapter:
    """Inyecta nuevos componentes (Tools, Prompts, Resources) en un proyecto MCP existente."""

    def __init__(self):
        pass

    def inject_tools(self, tools: List[Dict[str, Any]], inventory: ProjectInventory):
        base_path = inventory.project_path

        for tool in tools:
            try:
                tool_name = tool['name']
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

                print(f"Tool '{tool_name}' inyectada correctamente.")
            except (ValueError, KeyError, OSError) as e:
                 print(f"ERROR al inyectar tool '{tool.get('name', 'desconocida')}': {e}")

    def inject_prompts(self, prompts: List[Dict[str, Any]], inventory: ProjectInventory):
        base_path = inventory.project_path
        for prompt in prompts:
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

                print(f"Prompt '{prompt_name}' inyectado correctamente.")
            except (ValueError, KeyError, OSError) as e:
                 print(f"ERROR al inyectar prompt '{prompt.get('name', 'desconocida')}': {e}")

    def inject_resources(self, resources: List[Dict[str, Any]], inventory: ProjectInventory):
        base_path = inventory.project_path
        for resource in resources:
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

                print(f"Resource '{resource_name}' inyectado correctamente.")
            except (ValueError, KeyError, OSError) as e:
                 print(f"ERROR al inyectar resource '{resource.get('name', 'desconocida')}': {e}")
    
    def inject_mcp_connections(self, connections: List[Dict[str, str]], inventory: ProjectInventory):
        env_path = os.path.join(inventory.project_path, "application/settings/.env")
        
        try:
            current_max_index = 0
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    content = f.read()
                    matches = re.findall(r'MCP_CONNECTION_(\d+)_NAME', content)
                    if matches:
                        indices = [int(m) for m in matches]
                        current_max_index = max(indices)
            
            lines_to_add = []
            for i, conn in enumerate(connections, start=1):
                next_index = current_max_index + i
                lines_to_add.append(f"\nMCP_CONNECTION_{next_index}_NAME={conn['name']}")
                lines_to_add.append(f"MCP_CONNECTION_{next_index}_ENDPOINT={conn['endpoint']}")
            
            with open(env_path, 'a') as f:
                f.write("\n".join(lines_to_add) + "\n")
                
            print(f"Inyectadas {len(connections)} nuevas conexiones MCP en .env")
            
        except Exception as e:
            print(f"ERROR al inyectar conexiones MCP: {e}")
            raise