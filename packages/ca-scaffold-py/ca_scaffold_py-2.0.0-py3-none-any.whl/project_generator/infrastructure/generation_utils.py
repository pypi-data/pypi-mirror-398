import json
import os
import re
import sys
from typing import List, Dict, Any

def add_code_to_file(filepath: str, anchor: str, code_to_add: str):
    """Inyecta un bloque de código en un archivo en la ubicación de un anchor."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        if not any(anchor in line for line in lines):
            print(f"ADVERTENCIA: Anchor '{anchor}' no encontrado en '{filepath}'. Añadiendo al final.")
            if lines and not lines[-1].endswith('\n'):
                lines.append('\n')
            lines.append(f"\n{code_to_add}\n")
        else:
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if anchor in line:
                    new_lines.append(code_to_add)
            lines = new_lines

        with open(filepath, 'w') as f:
            f.writelines(lines)

    except FileNotFoundError:
        print(f"ADVERTENCIA: Archivo '{filepath}' no encontrado. No se pudo inyectar código.")
        pass
    except Exception as e:
        print(f"ERROR inesperado al añadir código a '{filepath}': {e}")
        pass


def create_file(filepath: str, content: str):
    """Crea un nuevo archivo con el contenido dado, asegurándose de que el directorio exista."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
    except OSError as e:
        print(f"ERROR al crear archivo '{filepath}': {e}")
        pass
    except Exception as e:
        print(f"ERROR inesperado al crear archivo '{filepath}': {e}")
        pass

def to_camel_case(snake_str: str) -> str:
    """Convierte snake_case a PascalCase."""
    if not snake_str:
        return ""
    return "".join(word.capitalize() for word in snake_str.split('_'))

def parse_params(params_str: str) -> List[Dict[str, Any]]:
    if not params_str or not params_str.strip():
        return []
    
    params_list = []
    balance = 0
    current_param = ""
    for char in params_str:
        if char in '[{(':
            balance += 1
        elif char in ']})':
            balance -= 1
        
        if char == ',' and balance == 0:
            params_list.append(current_param.strip())
            current_param = ""
        else:
            current_param += char
    
    if current_param:
        params_list.append(current_param.strip())

    params = []
    for param in params_list:
        param = param.strip()
        if not param: continue

        name, p_type, default, is_optional = None, "Any", None, False

        if '=' in param:
            name_part, default_str = param.split('=', 1)
            default = default_str.strip()
            is_optional = True
        else:
            name_part = param

        if ':' in name_part:
            parts = name_part.split(':', 1)
            name = parts[0].strip()
            p_type = parts[1].strip()
        else:
            name = name_part.strip()

        if not name: continue

        if default is not None and '=' in p_type:
            p_type = p_type.split('=')[0].strip()

        params.append({
            "name": name,
            "type": p_type,
            "default": default,
            "optional": is_optional
        })
    return params

def format_params_for_sig(params: List[Dict[str, Any]], include_self=False) -> str:
    """Formatea los parámetros para una firma de método."""
    parts = []
    if include_self:
        parts.append("self")
    for p in params:
        part_str = f"{p['name']}: {p['type']}"
        if p['default'] is not None:
            part_str += f" = {p['default']}"
        parts.append(part_str)
    return ", ".join(parts)

def format_params_for_call(params: List[Dict[str, Any]], include_self=False) -> str:
    """Formatea los parámetros para una llamada de método."""
    parts = []
    if include_self:
        parts.append("self")
    parts.extend(p['name'] for p in params)
    return ", ".join(parts)

def format_params_for_test_values(params: List[Dict[str, Any]]) -> str:
    """Formatea valores de prueba para parámetros."""
    values = []
    for p in params:
        p_type_lower = p['type'].lower()

        if p.get('optional') and p.get('default') is None:
            values.append('None')
        elif 'str' in p_type_lower:
            values.append(f"'test_{p['name']}'")
        elif 'int' in p_type_lower:
            values.append("123")
        elif 'float' in p_type_lower:
            values.append("123.45")
        elif 'bool' in p_type_lower:
            default_lower = str(p.get('default', '')).lower()
            if default_lower == 'true':
                values.append('True')
            elif default_lower == 'false':
                values.append('False')
            else:
                values.append('True')

        else:
            values.append(f"'test_{p['name']}_value'")
    return ", ".join(values)

def format_params_for_test_call_kwargs(params: List[Dict[str, Any]]) -> str:
    """Formatea kwargs para llamadas de prueba."""
    kwargs = []
    test_values_str = format_params_for_test_values(params)
    test_values = [v.strip() for v in test_values_str.split(',') if v.strip()]

    if len(test_values) != len(params):
         print(f"ADVERTENCIA: Discrepancia en número de parámetros ({len(params)}) y valores de test generados ({len(test_values)}) para kwargs.")
         return ", ".join([f"{p['name']}='test_{p['name']}'" for p in params])

    for i, p in enumerate(params):
        kwargs.append(f"{p['name']}={test_values[i]}")

    return ", ".join(kwargs)

def get_domain_model_template(tool_name: str, camel_name: str) -> str:
    return f"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class {camel_name}Data(BaseModel):
    key: str
    value: Any

class {camel_name}Response(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[List[{camel_name}Data]] = None
"""

def get_domain_gateway_template(tool_name: str, camel_name: str, params_sig_no_self: str, camel_response_name: str) -> str:
    return f"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from src.domain.model.{tool_name}.{tool_name}_model import {camel_response_name}

class {camel_name}Adapter(ABC):
    \"\"\"Gateway abstracto para la operación '{tool_name}'.\"\"\"

    @abstractmethod
    async def {tool_name}(self, {params_sig_no_self}) -> {camel_response_name}:
        \"\"\"Define el contrato para ejecutar la operación '{tool_name}'.\"\"\"
        raise NotImplementedError
"""

def get_domain_error_template(tool_name: str, camel_name: str) -> str:
    return f"""
class {camel_name}(Exception):
    \"\"\"Excepción personalizada para errores relacionados con '{tool_name}'.\"\"\"
    def __init__(self, message: str = "Ocurrió un error durante la operación '{tool_name}'"):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
"""

def get_use_case_template(tool_name: str, camel_name: str, params_sig_no_self: str, params_call_no_self: str, camel_response_name: str, camel_adapter_name: str, camel_error_name: str) -> str:
    use_case_class_name = f"{camel_name}UseCase"
    return f"""
import logging
from typing import Optional, List, Dict, Any
from src.domain.model.{tool_name}.gateways.{tool_name}_adapter import {camel_adapter_name}
from src.domain.model.{tool_name}.{tool_name}_model import {camel_response_name}
from src.domain.model.errors.{tool_name}_error import {camel_error_name}

logger = logging.getLogger(__name__)

class {use_case_class_name}:
    \"\"\"Caso de uso para orquestar la operación '{tool_name}'.\"\"\"

    def __init__(self, {tool_name}_adapter: {camel_adapter_name}):
        self._{tool_name}_adapter = {tool_name}_adapter

    async def execute(self, {params_sig_no_self}) -> {camel_response_name}:
        \"\"\"Ejecuta la lógica de negocio para '{tool_name}'.\"\"\"
        logger.info(f"Ejecutando caso de uso '{tool_name}'...")
        try:
            result = await self._{tool_name}_adapter.{tool_name}({params_call_no_self})
            logger.info(f"Caso de uso '{tool_name}' ejecutado exitosamente.")
            return result
        except {camel_error_name} as e:
             logger.error(f"Error de dominio en '{tool_name}': {{e}}", exc_info=True)
             raise
        except Exception as e:
            logger.error(f"Error inesperado en {use_case_class_name} ejecutando '{tool_name}': {{e}}", exc_info=True)
            raise {camel_error_name}(f"Fallo inesperado al ejecutar '{tool_name}': {{str(e)}}") from e
"""

def get_adapter_template(tool_name: str, camel_name: str, params_sig_no_self: str, params_call_no_self: str, camel_response_name: str, camel_adapter_name: str, camel_error_name: str) -> str:
    return f"""
import logging
from typing import Dict, Any, Optional, List
from src.domain.model.{tool_name}.gateways.{tool_name}_adapter import {camel_adapter_name}
from src.domain.model.{tool_name}.{tool_name}_model import {camel_response_name}
from src.domain.model.errors.{tool_name}_error import {camel_error_name}
from src.infrastructure.driven_adapters.api_connect_adapter.adapter.api_connect_adapter import ApiConnectAdapter
from src.infrastructure.driven_adapters.api_connect_adapter.errors import ApiConnectError

class {camel_name}ApiAdapter({camel_adapter_name}):
    \"\"\"Implementación del adaptador para '{tool_name}' usando ApiConnectAdapter genérico.\"\"\"

    def __init__(self, config: Dict[str, Any], api_adapter: ApiConnectAdapter):
        self.endpoint = config.get("{tool_name}_endpoint", "")
        if not self.endpoint:
             logging.warning(f"Endpoint para '{tool_name}' no encontrado en la configuración.")
        self.api_adapter = api_adapter
        self.logger = logging.getLogger(__name__)

    async def {tool_name}(self, {params_sig_no_self}) -> {camel_response_name}:
        \"\"\"Implementación de '{tool_name}' que consume la API via API Connect.\"\"\"
        self.logger.info(f"Iniciando llamada a API para '{tool_name}' en endpoint: {{self.endpoint}}")
        if not self.endpoint:
             raise {camel_error_name}("Endpoint no configurado para la operación '{tool_name}'.")

        try:
            api_params = {{ {params_call_no_self} }}
            self.logger.debug(f"Parámetros para GET '{tool_name}': {{api_params}}")
            result = await self.api_adapter.make_get_request(self.endpoint, params=api_params)

            await self.api_adapter.handle_api_error(result)
            response_data = result.get("body", {{}}).get("data", None)

            if response_data is None:
                 self.logger.warning(f"Respuesta de API para '{tool_name}' no contenía 'data'. Respuesta recibida: {{result.get('body')}}")
                 raise {camel_error_name}(f"Respuesta inesperada de API para '{tool_name}', campo 'data' ausente.")

            try:
                parsed_response = {camel_response_name}(**response_data)
                self.logger.info(f"API call para '{tool_name}' exitosa.")
                return parsed_response
            except Exception as pydantic_error:
                self.logger.error(f"Error al validar respuesta de API para '{tool_name}' con Pydantic: {{pydantic_error}}", exc_info=True)
                raise {camel_error_name}(f"Formato de respuesta inválido de API para '{tool_name}'.") from pydantic_error

        except ApiConnectError as e:
            self.logger.error(f"Error de API Connect en '{tool_name}': {{e}}", exc_info=False)
            raise {camel_error_name}(f"Fallo la comunicación con API para '{tool_name}': {{str(e)}}") from e
        except Exception as e:
            self.logger.error(f"Error inesperado en {camel_name}ApiAdapter ({tool_name}): {{e}}", exc_info=True)
            raise {camel_error_name}(f"Error inesperado en adaptador para '{tool_name}': {{str(e)}}") from e
"""

def get_adapter_test_template(tool_name: str, camel_name: str, camel_adapter_name: str, camel_error_name: str, camel_response_name: str, params_list: List[Dict[str, Any]]) -> str:
    test_params_kwargs_str = format_params_for_test_call_kwargs(params_list)
    mock_data_dict = f'{{ "success": True, "data": [] }}'

    return f"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any
from src.infrastructure.driven_adapters.api_connect_adapter.adapter.{tool_name}_api_adapter import {camel_name}ApiAdapter
from src.domain.model.{tool_name}.{tool_name}_model import {camel_response_name}
from src.domain.model.errors.{tool_name}_error import {camel_error_name}
from src.infrastructure.driven_adapters.api_connect_adapter.errors import ApiConnectError
from src.infrastructure.driven_adapters.api_connect_adapter.adapter.api_connect_adapter import ApiConnectAdapter

@pytest.fixture
def mock_api_adapter_generic() -> AsyncMock:
    return AsyncMock(spec=ApiConnectAdapter)

@pytest.fixture
def config() -> Dict[str, Any]:
    return {{"{tool_name}_endpoint": "https://api.test/{tool_name}"}}

@pytest.fixture
def adapter_instance(config: Dict[str, Any], mock_api_adapter_generic: AsyncMock) -> {camel_name}ApiAdapter:
    return {camel_name}ApiAdapter(config, mock_api_adapter_generic)

@pytest.mark.asyncio
async def test_{tool_name}_success(adapter_instance: {camel_name}ApiAdapter, mock_api_adapter_generic: AsyncMock):
    expected_internal_data = {mock_data_dict}
    mock_api_response = {{"status": 200, "body": {{"data": expected_internal_data}}}}
    mock_api_adapter_generic.make_get_request.return_value = mock_api_response
    expected_response_object = {camel_response_name}(**expected_internal_data)

    result = await adapter_instance.{tool_name}({test_params_kwargs_str})

    assert result == expected_response_object
    mock_api_adapter_generic.make_get_request.assert_called_once()
    mock_api_adapter_generic.handle_api_error.assert_called_once_with(mock_api_response)

@pytest.mark.asyncio
async def test_{tool_name}_api_connect_error(adapter_instance: {camel_name}ApiAdapter, mock_api_adapter_generic: AsyncMock):
    api_error = ApiConnectError("API returned 404")
    mock_api_adapter_generic.make_get_request.side_effect = api_error

    with pytest.raises({camel_error_name}) as exc_info:
        await adapter_instance.{tool_name}({test_params_kwargs_str})
    assert "Fallo la comunicación con API" in str(exc_info.value)
    assert exc_info.value.__cause__ is api_error

@pytest.mark.asyncio
async def test_{tool_name}_invalid_response_data(adapter_instance: {camel_name}ApiAdapter, mock_api_adapter_generic: AsyncMock):
    mock_api_response = {{"status": 200, "body": {{"message": "Success but no data"}}}}
    mock_api_adapter_generic.make_get_request.return_value = mock_api_response

    with pytest.raises({camel_error_name}) as exc_info:
        await adapter_instance.{tool_name}({test_params_kwargs_str})
    assert "campo 'data' ausente" in str(exc_info.value)

@pytest.mark.asyncio
async def test_{tool_name}_pydantic_validation_error(adapter_instance: {camel_name}ApiAdapter, mock_api_adapter_generic: AsyncMock):
    mock_invalid_data = {{"wrong_field": True}}
    mock_api_response = {{"status": 200, "body": {{"data": mock_invalid_data}}}}
    mock_api_adapter_generic.make_get_request.return_value = mock_api_response

    with pytest.raises({camel_error_name}) as exc_info:
        await adapter_instance.{tool_name}({test_params_kwargs_str})
    assert "Formato de respuesta inválido" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, Exception)
"""

def get_use_case_test_template(tool_name: str, camel_name: str, camel_adapter_name: str, camel_error_name: str, camel_response_name: str, params_list: List[Dict[str, Any]]) -> str:
    test_params_kwargs_str = format_params_for_test_call_kwargs(params_list)
    mock_data_dict = f'{{ "success": True, "data": [] }}'
    use_case_class_name = f"{camel_name}UseCase"

    return f"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.domain.usecase.{tool_name}_use_case import {use_case_class_name}
from src.domain.model.{tool_name}.{tool_name}_model import {camel_response_name}
from src.domain.model.{tool_name}.gateways.{tool_name}_adapter import {camel_adapter_name}
from src.domain.model.errors.{tool_name}_error import {camel_error_name}

@pytest.fixture
def mock_adapter() -> AsyncMock:
    return AsyncMock(spec={camel_adapter_name})

@pytest.fixture
def use_case_instance(mock_adapter: AsyncMock) -> {use_case_class_name}:
    return {use_case_class_name}({tool_name}_adapter=mock_adapter)

@pytest.mark.asyncio
async def test_{tool_name}_use_case_success(use_case_instance: {use_case_class_name}, mock_adapter: AsyncMock):
    expected_response_data = {mock_data_dict}
    expected_response_object = {camel_response_name}(**expected_response_data)
    mock_adapter.{tool_name}.return_value = expected_response_object

    result = await use_case_instance.execute({test_params_kwargs_str})

    assert result == expected_response_object
    mock_adapter.{tool_name}.assert_awaited_once_with({test_params_kwargs_str})

@pytest.mark.asyncio
async def test_{tool_name}_use_case_adapter_error(use_case_instance: {use_case_class_name}, mock_adapter: AsyncMock):
    adapter_error = {camel_error_name}("Fallo en el adapter")
    mock_adapter.{tool_name}.side_effect = adapter_error

    with pytest.raises({camel_error_name}) as exc_info:
        await use_case_instance.execute({test_params_kwargs_str})
    assert exc_info.value is adapter_error
    mock_adapter.{tool_name}.assert_awaited_once_with({test_params_kwargs_str})

@pytest.mark.asyncio
async def test_{tool_name}_use_case_unexpected_error(use_case_instance: {use_case_class_name}, mock_adapter: AsyncMock):
    unexpected_error = ValueError("Algo salió mal inesperadamente")
    mock_adapter.{tool_name}.side_effect = unexpected_error

    with pytest.raises({camel_error_name}) as exc_info:
        await use_case_instance.execute({test_params_kwargs_str})
    assert "Fallo inesperado" in str(exc_info.value)
    assert exc_info.value.__cause__ is unexpected_error
    mock_adapter.{tool_name}.assert_awaited_once_with({test_params_kwargs_str})
"""


def get_prompt_use_case_template(prompt_name: str, camel_prompt_name: str) -> str:
    use_case_class_name = f"Get{camel_prompt_name}UseCase"
    return f"""
import logging

from src.domain.model.paper.gateway.prompt_repository import PromptRepository

logger = logging.getLogger(__name__)

class {use_case_class_name}:
    \"\"\"Caso de uso específico para obtener el prompt '{prompt_name}'.\"\"\"

    def __init__(self, prompt_adapter: PromptRepository):
        self._prompt_adapter = prompt_adapter
        self._prompt_name = "{prompt_name}"

    async def execute(self) -> str:
        \"\"\"Ejecuta la lectura del prompt '{prompt_name}' usando el adapter genérico.\"\"\"
        logger.info(f"Intentando obtener prompt '{{self._prompt_name}}'")
        try:

            prompt_content = await self._prompt_adapter.read_prompt(self._prompt_name)
            logger.info(f"Prompt '{{self._prompt_name}}' obtenido exitosamente.")
            return prompt_content
        except Exception as e:
            logger.error(f"Error inesperado al obtener prompt '{{self._prompt_name}}': {{e}}", exc_info=True)
            raise RuntimeError(f"Fallo al obtener prompt '{{self._prompt_name}}'") from e
"""


def _get_resource_typing_imports(return_type: str) -> (str, str):
    """
    Helper para capitalizar el tipo de retorno y determinar las importaciones correctas.
    """

    return_type_capitalized = _capitalize_typing_base(return_type)
    

    base_type_import = return_type_capitalized.split('[')[0]
    

    typing_imports = {"Dict", "Any", "List", "Tuple", "Set", "Optional", "Union", "Callable", "Protocol", "TypedDict", "Sequence", "Mapping", "Iterable", "Generator", "Type"}
    

    imports = {"Dict", "Any"}

    if base_type_import in typing_imports:
        imports.add(base_type_import)
    

    return_type_import_str = ", ".join(sorted(list(imports)))
    
    return return_type_capitalized, return_type_import_str


def get_resource_gateway_template(resource_name: str, camel_resource_name: str, params_sig_no_self: str, return_type: str) -> str:
    gateway_class_name = f"Get{camel_resource_name}ResourceGateway"
    method_name = resource_name
    
    return_type_capitalized, return_type_import_str = _get_resource_typing_imports(return_type)

    return f"""
from abc import ABC, abstractmethod
from typing import {return_type_import_str}

class {gateway_class_name}(ABC):
    \"\"\"Gateway abstracto para obtener el recurso '{resource_name}'.\"\"\"

    @abstractmethod
    async def {method_name}(self, {params_sig_no_self}) -> {return_type_capitalized}:
        \"\"\"Define el contrato para obtener el recurso '{resource_name}'.\"\"\"
        raise NotImplementedError
"""

def get_resource_use_case_template(resource_name: str, camel_resource_name: str, params_sig_no_self: str, params_call_no_self: str, return_type: str) -> str:
    use_case_class_name = f"Get{camel_resource_name}UseCase"
    gateway_class_name = f"Get{camel_resource_name}ResourceGateway"
    
    return_type_capitalized, return_type_import_str = _get_resource_typing_imports(return_type)

    return f"""
import logging
from typing import {return_type_import_str}
from src.domain.model.{resource_name}.gateways.{resource_name}_gateway import {gateway_class_name}

logger = logging.getLogger(__name__)

class {use_case_class_name}:
    \"\"\"Caso de uso para obtener el recurso '{resource_name}'.\"\"\"

    def __init__(self, resource_gateway: {gateway_class_name}):
        self._resource_gateway = resource_gateway

    async def execute(self, {params_sig_no_self}) -> {return_type_capitalized}:
        \"\"\"Ejecuta la lógica para obtener el recurso '{resource_name}'.\"\"\"
        logger.info(f"Ejecutando caso de uso para recurso '{resource_name}'")
        try:
            result = await self._resource_gateway.{resource_name}({params_call_no_self})
            logger.info(f"Recurso '{resource_name}' obtenido exitosamente.")
            return result
        except Exception as e:
            logger.error(f"Error al obtener recurso '{resource_name}': {{e}}", exc_info=True)
            raise RuntimeError(f"Fallo al obtener recurso '{resource_name}'") from e
"""

def get_resource_adapter_template(resource_name: str, camel_resource_name: str, params_sig_no_self: str, params_call_no_self: str, return_type: str) -> str:
    adapter_class_name = f"Get{camel_resource_name}ResourceAdapter"
    gateway_class_name = f"Get{camel_resource_name}ResourceGateway"
    method_name = resource_name
    
    return_type_capitalized, return_type_import_str = _get_resource_typing_imports(return_type)


    placeholder_return = "{}"
    if return_type_capitalized == "int":
        placeholder_return = "0"
    elif return_type_capitalized == "float":
        placeholder_return = "0.0"
    elif return_type_capitalized == "bool":
        placeholder_return = "False"
    elif return_type_capitalized.startswith("List"):
        placeholder_return = "[]"
    elif return_type_capitalized.startswith("str"):
        placeholder_return = "''"


    return f"""
import logging
from typing import {return_type_import_str}
from src.domain.model.{resource_name}.gateways.{resource_name}_gateway import {gateway_class_name}

logger = logging.getLogger(__name__)

class {adapter_class_name}({gateway_class_name}):
    \"\"\"Implementación placeholder específica para obtener el recurso '{resource_name}'.\"\"\"

    async def {method_name}(self, {params_sig_no_self}) -> {return_type_capitalized}:
        \"\"\"Lógica placeholder para obtener el recurso '{resource_name}'.\"\"\"
        logger.warning(f"Lógica para recurso '{resource_name}' no implementada. Retornando placeholder.")

        return {placeholder_return}
"""


def get_settings_field_template(tool_name: str) -> str:
    endpoint_name = tool_name.upper()
    return f"""
    {tool_name}_endpoint: str = Field(default="", alias="{endpoint_name}_ENDPOINT", description="URL del endpoint para la API de '{tool_name}'.")
"""

def get_settings_validator_template(tool_name: str) -> str:
    return f'"{tool_name}_endpoint",'

def get_container_import_template(tool_name: str, camel_name: str) -> str:
    camel_adapter_name = f"{camel_name}Adapter"
    use_case_class_name = f"{camel_name}UseCase"
    return f"""
from src.domain.usecase.{tool_name}_use_case import {use_case_class_name}
from src.domain.model.{tool_name}.gateways.{tool_name}_adapter import {camel_adapter_name}
"""

def get_container_adapter_import_template(tool_name: str, camel_name: str) -> str:
    return f"from src.infrastructure.driven_adapters.api_connect_adapter.adapter.{tool_name}_api_adapter import {camel_name}ApiAdapter\n"

def get_container_adapter_template(tool_name: str, camel_name: str) -> str:
    return f"""
    {tool_name}_adapter = providers.Singleton({camel_name}ApiAdapter, config=config.provided, api_adapter=api_connect_adapter)
"""

def get_container_use_case_template(tool_name: str, camel_name: str) -> str:
    use_case_class_name = f"{camel_name}UseCase"
    return f"""
    {tool_name}_use_case = providers.Singleton({use_case_class_name}, {tool_name}_adapter={tool_name}_adapter)
"""

def get_adapter_init_import_template(tool_name: str, camel_name: str) -> str:
    return f"from .adapter.{tool_name}_api_adapter import {camel_name}ApiAdapter\n"

def get_adapter_init_all_template(tool_name: str, camel_name: str) -> str:
    return f'"{camel_name}ApiAdapter",\n'

def get_tools_import_template(tool_name: str, camel_name: str) -> str:
    use_case_class_name = f"{camel_name}UseCase"
    return f"from src.domain.usecase.{tool_name}_use_case import {use_case_class_name}\n"

def get_tools_provide_template(tool_name: str, camel_name: str) -> str:
    use_case_class_name = f"{camel_name}UseCase"
    return f"    {tool_name}_use_case: {use_case_class_name} = Provide[Container.{tool_name}_use_case],\n"

def get_prompt_content_template(prompt_name: str, description: str) -> str:
    """Genera el contenido placeholder para un archivo .txt de prompt."""
    return f"""# Archivo de prompt: {prompt_name}.txt

# {description}
---

(Este es un placeholder para '{prompt_name}')

Eres un asistente de IA muy servicial.
"""

def get_prompts_bind_template(prompt_name: str, description: str) -> str:
    use_case_provider_name = f"get_{prompt_name}_use_case"

    return f"""

    from src.applications.settings.container import Container

    @mcp.prompt("{prompt_name}")
    async def {prompt_name}() -> str:
        \"\"\"
        {description}
        Returns:
            str: El contenido del prompt. MCP inferirá el rol.
        \"\"\"

        container = Container()
        use_case = container.{use_case_provider_name}()

        result = await use_case.execute()
        return result
    """

def get_tools_bind_template(tool_name: str, params_sig_no_self: str, params_call_no_self: str, description: str) -> str:
    use_case_provider_name = f"{tool_name}_use_case"
    return f"""
    @mcp.tool()
    async def {tool_name}({params_sig_no_self}) -> dict:
        \"\"\"
        {description}
        Args:
            {params_sig_no_self}
        Returns:
            dict: Resultado de la operación.
        \"\"\"
        result_model = await {use_case_provider_name}.execute({params_call_no_self})
        return result_model.model_dump(mode="json")
    """


def get_container_prompt_import_template(prompt_name: str, camel_prompt_name: str) -> str:
    use_case_class_name = f"Get{camel_prompt_name}UseCase"
    return f"""
from src.domain.usecase.get_{prompt_name}_usecase import {use_case_class_name}
"""

def get_container_prompt_use_case_template(prompt_name: str, camel_prompt_name: str) -> str:
    use_case_class_name = f"Get{camel_prompt_name}UseCase"
    use_case_provider_name = f"get_{prompt_name}_use_case"
    return f"""
    {use_case_provider_name} = providers.Singleton({use_case_class_name}, prompt_adapter=prompt_adapter)
"""

def get_prompts_import_template(prompt_name: str, camel_prompt_name: str) -> str:
    use_case_class_name = f"Get{camel_prompt_name}UseCase"
    return f"from src.domain.usecase.get_{prompt_name}_usecase import {use_case_class_name}\n"

def get_prompts_provide_template(prompt_name: str, camel_prompt_name: str) -> str:
    use_case_class_name = f"Get{camel_prompt_name}UseCase"
    use_case_provider_name = f"get_{prompt_name}_use_case"
    return f"    {use_case_provider_name}: {use_case_class_name} = Provide[Container.{use_case_provider_name}],\n"



def get_container_resource_import_template(resource_name: str, camel_resource_name: str) -> str:
    use_case_class_name = f"Get{camel_resource_name}UseCase"
    adapter_class_name = f"Get{camel_resource_name}ResourceAdapter"
    gateway_class_name = f"Get{camel_resource_name}ResourceGateway"
    return f"""
from src.domain.usecase.get_{resource_name}_usecase import {use_case_class_name}
from src.domain.model.{resource_name}.gateways.{resource_name}_gateway import {gateway_class_name}
from src.infrastructure.driven_adapters.local_files.{resource_name}_adapter import {adapter_class_name}
"""

def get_container_resource_adapter_template(resource_name: str, camel_resource_name: str) -> str:
    adapter_class_name = f"Get{camel_resource_name}ResourceAdapter"
    adapter_provider_name = f"get_{resource_name}_adapter"
    gateway_class_name = f"Get{camel_resource_name}ResourceGateway"
    return f"""
    {adapter_provider_name}: providers.Provider[{gateway_class_name}] = providers.Singleton({adapter_class_name})
"""

def get_container_resource_use_case_template(resource_name: str, camel_resource_name: str) -> str:
    use_case_class_name = f"Get{camel_resource_name}UseCase"
    use_case_provider_name = f"get_{resource_name}_use_case"
    adapter_provider_name = f"get_{resource_name}_adapter"
    return f"""
    {use_case_provider_name} = providers.Singleton({use_case_class_name}, resource_gateway={adapter_provider_name})
"""

def get_resources_import_template(resource_name: str, camel_resource_name: str) -> str:
    use_case_class_name = f"Get{camel_resource_name}UseCase"
    return f"from src.domain.usecase.get_{resource_name}_usecase import {use_case_class_name}\n"

def get_resources_provide_template(resource_name: str, camel_resource_name: str) -> str:
    use_case_class_name = f"Get{camel_resource_name}UseCase"
    use_case_provider_name = f"get_{resource_name}_use_case"
    return f"    {use_case_provider_name}: {use_case_class_name} = Provide[Container.{use_case_provider_name}],\n"

def get_resources_bind_template(resource_name: str, uri: str, description: str, params_sig_no_self: str, params_call_no_self: str, return_type: str) -> str:
    use_case_provider_name = f"get_{resource_name}_use_case"
    

    return_type_capitalized = _capitalize_typing_base(return_type)

    return f"""
    @mcp.resource("{uri}")
    async def {resource_name}({params_sig_no_self}) -> {return_type_capitalized}:
        \"\"\"
        {description}
        Args:
            {params_sig_no_self}
        Returns:
            {return_type_capitalized}: Contenido del recurso.
        \"\"\"
        result = await {use_case_provider_name}.execute({params_call_no_self})
        return result
    """

def _capitalize_typing_base(type_str: str) -> str:
    """
    Convierte 'dict' a 'Dict', 'list' a 'List', etc., incluso dentro de genéricos.
    """
    type_str = type_str.strip()
    base_mapping = {
        "dict": "Dict",
        "list": "List",
        "tuple": "Tuple",
        "set": "Set",
        "frozenset": "FrozenSet",
        "type": "Type",
    }
    

    if type_str.lower() in base_mapping:
         return base_mapping[type_str.lower()]


    def replacer(match):
        lower_type = match.group(1).lower()
        return base_mapping.get(lower_type, match.group(1))


    pattern = r'\b(' + '|'.join(re.escape(k) for k in base_mapping.keys()) + r')\b'
    capitalized_str = re.sub(pattern, replacer, type_str, flags=re.IGNORECASE)

    return capitalized_str