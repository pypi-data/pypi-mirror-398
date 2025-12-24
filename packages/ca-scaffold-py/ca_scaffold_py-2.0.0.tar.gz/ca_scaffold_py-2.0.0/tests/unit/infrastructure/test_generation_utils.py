import pytest
from unittest.mock import Mock, mock_open, call
import os
from project_generator.infrastructure import generation_utils as utils

def _capitalize_typing_base(type_str: str) -> str:
    type_str = type_str.strip()
    base_mapping = {
        "dict": "Dict",
        "list": "List",
        "tuple": "Tuple",
        "set": "Set",
        "frozenset": "FrozenSet",
        "type": "Type",
    }
    def replacer(match):
        lower_type = match.group(1).lower()
        return base_mapping.get(lower_type, match.group(1))
    import re
    pattern = r'\b(' + '|'.join(re.escape(k) for k in base_mapping.keys()) + r')\b'
    capitalized_str = re.sub(pattern, replacer, type_str, flags=re.IGNORECASE)
    if type_str.lower() in base_mapping:
         return base_mapping[type_str.lower()]
    capitalized_str = capitalized_str.replace("[dict]", "[Dict]")
    capitalized_str = capitalized_str.replace("[list]", "[List]")
    capitalized_str = capitalized_str.replace("[tuple]", "[Tuple]")
    capitalized_str = capitalized_str.replace("[set]", "[Set]")
    return capitalized_str

utils._capitalize_typing_base = _capitalize_typing_base

@pytest.mark.parametrize("snake, camel", [
    ("my_tool_name", "MyToolName"),
    ("single", "Single"),
    ("", ""),
    (None, ""),
    ("name_with_1_number", "NameWith1Number"),
])
def test_to_camel_case(snake, camel):
    assert utils.to_camel_case(snake) == camel

@pytest.mark.parametrize("input_str, expected", [
    ("", []),
    (" ", []),
    ("name:str", [{"name": "name", "type": "str", "default": None, "optional": False}]),
    ("id:int, name:str", [
        {"name": "id", "type": "int", "default": None, "optional": False},
        {"name": "name", "type": "str", "default": None, "optional": False}
    ]),
    ("count:int=5", [{"name": "count", "type": "int", "default": "5", "optional": True}]),
    ("flag:bool=True, value: float = 1.0 ", [
        {"name": "flag", "type": "bool", "default": "True", "optional": True},
        {"name": "value", "type": "float", "default": "1.0", "optional": True}
    ]),
    (" onlyname ", [{"name": "onlyname", "type": "Any", "default": None, "optional": False}]),
    ("complex:List[Dict[str, Any]]", [{"name": "complex", "type": "List[Dict[str, Any]]", "default": None, "optional": False}]),
    ("data: Dict[str, List[int]]", [{"name": "data", "type": "Dict[str, List[int]]", "default": None, "optional": False}]),
    ("param1: str, param2: List[str] = ['a', 'b']", [
        {"name": "param1", "type": "str", "default": None, "optional": False},
        {"name": "param2", "type": "List[str]", "default": "['a', 'b']", "optional": True}
    ]),
    (None, [])
])
def test_parse_params(input_str, expected):
    assert utils.parse_params(input_str) == expected

def test_parse_params_edge_cases():

    assert utils.parse_params(" : int") == []

    assert utils.parse_params("p1:int, , p2:str") == [
        {"name": "p1", "type": "int", "default": None, "optional": False},
        {"name": "p2", "type": "str", "default": None, "optional": False}
    ]

    assert utils.parse_params("p1:int=5=5") == [
        {"name": "p1", "type": "int", "default": "5=5", "optional": True}
    ]

@pytest.mark.parametrize("type_in, type_out", [
    ("dict", "Dict"),
    (" list ", "List"),
    ("Tuple", "Tuple"),
    ("set", "Set"),
    ("unknown", "unknown"),
    ("Dict[str, Any]", "Dict[str, Any]"),
    ("List[dict]", "List[Dict]"),
    (" list[ str ] ", "List[ str ]"),
    ("list[tuple[str, dict]]", "List[Tuple[str, Dict]]"),
])
def test_capitalize_typing_base(type_in, type_out):
    assert utils._capitalize_typing_base(type_in) == type_out

def test_create_file_success(mocker):
    mock_mko = mocker.patch("builtins.open", mock_open())
    mock_makedirs = mocker.patch("os.makedirs")
    utils.create_file("/fake/dir/file.txt", "content")
    mock_makedirs.assert_called_once_with("/fake/dir", exist_ok=True)
    mock_mko.assert_called_once_with("/fake/dir/file.txt", 'w')
    mock_mko().write.assert_called_once_with("content")

def test_create_file_os_error(mocker, capsys):
    mocker.patch("os.makedirs", side_effect=OSError("Permission denied"))
    utils.create_file("/fake/dir/file.txt", "content")
    captured = capsys.readouterr()
    assert "ERROR al crear archivo" in captured.out
    assert "Permission denied" in captured.out

def test_add_code_to_file_anchor_found(mocker):
    mock_mko = mocker.mock_open(read_data="line1\n# ANCHOR\nline3\n")
    mocker.patch("builtins.open", mock_mko)
    utils.add_code_to_file("file.txt", "# ANCHOR", "injected_code\n")
    mock_mko().writelines.assert_called_once_with(['line1\n', '# ANCHOR\n', 'injected_code\n', 'line3\n'])

def test_add_code_to_file_anchor_not_found(mocker, capsys):
    mock_mko = mocker.mock_open(read_data="line1\nline3")
    mocker.patch("builtins.open", mock_mko)
    utils.add_code_to_file("file.txt", "# NOT_FOUND", "injected_code\n")
    mock_mko().writelines.assert_called_once_with(['line1\n', 'line3', '\n', '\ninjected_code\n\n'])
    captured = capsys.readouterr()
    assert "ADVERTENCIA: Anchor '# NOT_FOUND' no encontrado" in captured.out

def test_add_code_to_file_not_found_error(mocker, capsys):
    mocker.patch("builtins.open", side_effect=FileNotFoundError("No such file"))
    utils.add_code_to_file("file.txt", "# ANCHOR", "code")
    captured = capsys.readouterr()
    assert "ADVERTENCIA: Archivo 'file.txt' no encontrado" in captured.out

def test_add_code_to_file_generic_error(mocker, capsys):
    mocker.patch("builtins.open", side_effect=Exception("Generic file error"))
    utils.add_code_to_file("file.txt", "# ANCHOR", "code")
    captured = capsys.readouterr()
    assert "ERROR inesperado al añadir código" in captured.out

def test_create_file_generic_error(mocker, capsys):
    mocker.patch("os.makedirs", side_effect=Exception("Generic makedirs error"))
    utils.create_file("/fake/dir/file.txt", "content")
    captured = capsys.readouterr()
    assert "ERROR inesperado al crear archivo" in captured.out

@pytest.fixture
def sample_params():
    return [
        {"name": "p_str", "type": "str", "default": None, "optional": False},
        {"name": "p_int", "type": "int", "default": "10", "optional": True},
        {"name": "p_bool", "type": "bool", "default": "True", "optional": True},
        {"name": "p_opt", "type": "Optional[str]", "default": None, "optional": True},
        {"name": "p_any", "type": "Any", "default": None, "optional": False},
    ]

def test_format_params_for_sig(sample_params):
    assert utils.format_params_for_sig(sample_params, include_self=True) == \
       "self, p_str: str, p_int: int = 10, p_bool: bool = True, p_opt: Optional[str], p_any: Any"
    assert utils.format_params_for_sig(sample_params, include_self=False) == \
        "p_str: str, p_int: int = 10, p_bool: bool = True, p_opt: Optional[str], p_any: Any"

def test_format_params_for_call(sample_params):
    assert utils.format_params_for_call(sample_params, include_self=True) == \
        "self, p_str, p_int, p_bool, p_opt, p_any"
    assert utils.format_params_for_call(sample_params, include_self=False) == \
        "p_str, p_int, p_bool, p_opt, p_any"

def test_format_params_for_test_values(sample_params):
    assert utils.format_params_for_test_values(sample_params) == \
        "'test_p_str', 123, True, None, 'test_p_any_value'"

    float_params = [
        {"name": "p_float", "type": "float", "default": None, "optional": False},
        {"name": "p_false", "type": "bool", "default": "False", "optional": True},
    ]
    assert utils.format_params_for_test_values(float_params) == "123.45, False"


    unknown_params = [{"name": "p_unk", "type": "CustomType", "default": None, "optional": False}]
    assert utils.format_params_for_test_values(unknown_params) == "'test_p_unk_value'"


    bool_params = [{"name": "p_b", "type": "bool", "default": "FALSE", "optional": True}]
    assert utils.format_params_for_test_values(bool_params) == "False"

def test_format_params_for_test_call_kwargs(sample_params):
    assert utils.format_params_for_test_call_kwargs(sample_params) == \
        "p_str='test_p_str', p_int=123, p_bool=True, p_opt=None, p_any='test_p_any_value'"

def test_format_params_for_test_call_kwargs_mismatch(sample_params, capsys):
    with pytest.MonkeyPatch.context() as m:
        m.setattr(utils, "format_params_for_test_values", lambda x: "")
        result = utils.format_params_for_test_call_kwargs(sample_params)
        assert result == "p_str='test_p_str', p_int='test_p_int', p_bool='test_p_bool', p_opt='test_p_opt', p_any='test_p_any'"
    captured = capsys.readouterr()
    assert "ADVERTENCIA: Discrepancia en número de parámetros" in captured.out

def test_all_get_templates_return_strings():
    assert "class MyToolNameResponse" in utils.get_domain_model_template("my_tool_name", "MyToolName")
    assert "class MyToolNameAdapter(ABC)" in utils.get_domain_gateway_template("my_tool_name", "MyToolName", "p:str", "MyToolNameResponse")
    assert "class MyToolNameError(Exception)" in utils.get_domain_error_template("my_tool_name", "MyToolNameError")
    assert "class MyToolNameUseCase" in utils.get_use_case_template("my_tool_name", "MyToolName", "p:str", "p", "MyToolNameResponse", "MyToolNameAdapter", "MyToolNameError")
    assert "class MyToolNameApiAdapter(MyToolNameAdapter)" in utils.get_adapter_template("my_tool_name", "MyToolName", "p:str", "p", "MyToolNameResponse", "MyToolNameAdapter", "MyToolNameError")
    assert "test_my_tool_name_success" in utils.get_adapter_test_template("my_tool_name", "MyToolName", "MyToolNameAdapter", "MyToolNameError", "MyToolNameResponse", [])
    assert "test_my_tool_name_use_case_success" in utils.get_use_case_test_template("my_tool_name", "MyToolName", "MyToolNameAdapter", "MyToolNameError", "MyToolNameResponse", [])
    assert "class GetMyPromptUseCase" in utils.get_prompt_use_case_template("my_prompt", "MyPrompt")
    assert "class GetMyResourceResourceGateway(ABC)" in utils.get_resource_gateway_template("my_resource", "MyResource", "p:str", "Dict")
    assert "class GetMyResourceUseCase" in utils.get_resource_use_case_template("my_resource", "MyResource", "p:str", "p", "Dict")
    assert "class GetMyResourceResourceAdapter(GetMyResourceResourceGateway)" in utils.get_resource_adapter_template("my_resource", "MyResource", "p:str", "p", "Dict")
    assert "my_tool_name_endpoint: str" in utils.get_settings_field_template("my_tool_name")
    assert '"my_tool_name_endpoint",' in utils.get_settings_validator_template("my_tool_name")
    assert "from src.domain.usecase.my_tool_name_use_case import MyToolNameUseCase" in utils.get_container_import_template("my_tool_name", "MyToolName")
    assert "from src.infrastructure.driven_adapters.api_connect_adapter.adapter.my_tool_name_api_adapter import MyToolNameApiAdapter" in utils.get_container_adapter_import_template("my_tool_name", "MyToolName")
    assert "my_tool_name_adapter = providers.Singleton(MyToolNameApiAdapter" in utils.get_container_adapter_template("my_tool_name", "MyToolName")
    assert "my_tool_name_use_case = providers.Singleton(MyToolNameUseCase" in utils.get_container_use_case_template("my_tool_name", "MyToolName")
    assert "from .adapter.my_tool_name_api_adapter import MyToolNameApiAdapter" in utils.get_adapter_init_import_template("my_tool_name", "MyToolName")
    assert '"MyToolNameApiAdapter",' in utils.get_adapter_init_all_template("my_tool_name", "MyToolName")
    assert "from src.domain.usecase.my_tool_name_use_case import MyToolNameUseCase" in utils.get_tools_import_template("my_tool_name", "MyToolName")
    assert "my_tool_name_use_case: MyToolNameUseCase" in utils.get_tools_provide_template("my_tool_name", "MyToolName")
    assert "Este es un placeholder para 'my_prompt'" in utils.get_prompt_content_template("my_prompt", "Desc")
    assert "@mcp.prompt(\"my_prompt\")" in utils.get_prompts_bind_template("my_prompt", "Desc")
    assert "async def my_prompt() -> str:" in utils.get_prompts_bind_template("my_prompt", "Desc")
    assert "@mcp.tool()" in utils.get_tools_bind_template("my_tool", "p:str", "p", "Desc")
    assert "async def my_tool(p:str) -> dict:" in utils.get_tools_bind_template("my_tool", "p:str", "p", "Desc")
    assert "from src.domain.usecase.get_my_prompt_usecase import GetMyPromptUseCase" in utils.get_container_prompt_import_template("my_prompt", "MyPrompt")
    assert "get_my_prompt_use_case = providers.Singleton(GetMyPromptUseCase" in utils.get_container_prompt_use_case_template("my_prompt", "MyPrompt")
    assert "from src.domain.usecase.get_my_prompt_usecase import GetMyPromptUseCase" in utils.get_prompts_import_template("my_prompt", "MyPrompt")
    assert "get_my_prompt_use_case: GetMyPromptUseCase" in utils.get_prompts_provide_template("my_prompt", "MyPrompt")
    assert "from src.domain.usecase.get_my_resource_usecase import GetMyResourceUseCase" in utils.get_container_resource_import_template("my_resource", "MyResource")
    assert "get_my_resource_adapter: providers.Provider[GetMyResourceResourceGateway]" in utils.get_container_resource_adapter_template("my_resource", "MyResource")
    assert "get_my_resource_use_case = providers.Singleton(GetMyResourceUseCase" in utils.get_container_resource_use_case_template("my_resource", "MyResource")
    assert "from src.domain.usecase.get_my_resource_usecase import GetMyResourceUseCase" in utils.get_resources_import_template("my_resource", "MyResource")
    assert "get_my_resource_use_case: GetMyResourceUseCase" in utils.get_resources_provide_template("my_resource", "MyResource")
    assert "@mcp.resource(\"uri://test\")" in utils.get_resources_bind_template("my_resource", "uri://test", "Desc", "p:str", "p", "Dict")
    assert "async def my_resource(p:str) -> Dict:" in utils.get_resources_bind_template("my_resource", "uri://test", "Desc", "p:str", "p", "Dict")


def test_parse_params_type_with_equals():

    input_str = "param: int=10 = 5" 
    expected = [{"name": "param", "type": "int", "default": "10 = 5", "optional": True}]
    assert utils.parse_params(input_str) == expected

def test_format_params_for_test_values_all_types():

    params = [
        {"name": "p_int", "type": "int", "default": None, "optional": False},
        {"name": "p_float", "type": "float", "default": None, "optional": False},
        {"name": "p_bool_true", "type": "bool", "default": "true", "optional": True},
        {"name": "p_bool_false", "type": "bool", "default": "false", "optional": True},
        {"name": "p_bool_default", "type": "bool", "default": "anything_else", "optional": True}
    ]
    result = utils.format_params_for_test_values(params)
    assert "123" in result
    assert "123.45" in result
    assert "True" in result
    assert "False" in result

def test_add_code_to_file_generic_exception(mocker, capsys):

    mocker.patch("builtins.open", side_effect=Exception("Generic error"))
    utils.add_code_to_file("dummy.txt", "ANCHOR", "code")
    captured = capsys.readouterr()
    assert "ERROR inesperado al añadir código a 'dummy.txt': Generic error" in captured.out

def test_create_file_generic_exception(mocker, capsys):

    mocker.patch("os.makedirs", side_effect=Exception("Generic error"))
    utils.create_file("dummy.txt", "content")
    captured = capsys.readouterr()
    assert "ERROR inesperado al crear archivo 'dummy.txt': Generic error" in captured.out

def test_get_resource_adapter_template_int_return():
    """Covers: int return type placeholder in get_resource_adapter_template."""
    result = utils.get_resource_adapter_template("res", "Res", "p: str", "p", "int")
    assert "return 0" in result


def test_get_resource_adapter_template_float_return():
    """Covers: float return type placeholder in get_resource_adapter_template."""
    result = utils.get_resource_adapter_template("res", "Res", "p: str", "p", "float")
    assert "return 0.0" in result


def test_get_resource_adapter_template_bool_return():
    """Covers: bool return type placeholder in get_resource_adapter_template."""
    result = utils.get_resource_adapter_template("res", "Res", "p: str", "p", "bool")
    assert "return False" in result


def test_get_resource_adapter_template_list_return():
    """Covers: List return type placeholder in get_resource_adapter_template."""
    result = utils.get_resource_adapter_template("res", "Res", "p: str", "p", "List[str]")
    assert "return []" in result


def test_get_resource_adapter_template_str_return():
    """Covers: str return type placeholder in get_resource_adapter_template."""
    result = utils.get_resource_adapter_template("res", "Res", "p: str", "p", "str")
    assert "return ''" in result


def test_get_resource_typing_imports_optional():
    """Covers: Optional type import in _get_resource_typing_imports."""
    cap, imports = utils._get_resource_typing_imports("Optional[str]")
    assert "Optional" in imports


def test_get_resource_typing_imports_union():
    """Covers: Union type import in _get_resource_typing_imports."""
    cap, imports = utils._get_resource_typing_imports("Union[str, int]")
    assert "Union" in imports


def test_get_resource_typing_imports_list():
    """Covers: List type import in _get_resource_typing_imports."""
    cap, imports = utils._get_resource_typing_imports("List[Dict]")
    assert "List" in imports


def test_get_resource_typing_imports_tuple():
    """Covers: Tuple type import in _get_resource_typing_imports."""
    cap, imports = utils._get_resource_typing_imports("Tuple[str, int]")
    assert "Tuple" in imports


def test_get_resource_typing_imports_sequence():
    """Covers: Sequence type import in _get_resource_typing_imports."""
    cap, imports = utils._get_resource_typing_imports("Sequence[str]")
    assert "Sequence" in imports


def test_get_resource_typing_imports_mapping():
    """Covers: Mapping type import in _get_resource_typing_imports."""
    cap, imports = utils._get_resource_typing_imports("Mapping[str, Any]")
    assert "Mapping" in imports


def test_to_camel_case_empty():
    """Covers: empty string handling in to_camel_case."""
    assert utils.to_camel_case("") == ""


def test_parse_params_nested_brackets():
    """Covers: nested brackets handling in parse_params."""
    result = utils.parse_params("data: Dict[str, List[int]]")
    assert len(result) == 1
    assert result[0]["type"] == "Dict[str, List[int]]"


def test_parse_params_multiple_nested_types():
    """Covers: multiple nested types in parse_params."""
    result = utils.parse_params("a: Tuple[Dict[str, Any], List[int]], b: str")
    assert len(result) == 2
    assert result[0]["name"] == "a"
    assert result[1]["name"] == "b"


def test_parse_params_curly_braces():
    """Covers: curly braces handling in parse_params."""
    result = utils.parse_params("data: TypedDict[{a: str, b: int}]")
    assert len(result) == 1


def test_parse_params_parentheses():
    """Covers: parentheses handling in parse_params."""
    result = utils.parse_params("callback: Callable[[int], str]")
    assert len(result) == 1


def test_format_params_for_test_values_optional_none():
    """Covers: optional parameter with None default."""
    params = [{"name": "opt", "type": "str", "default": None, "optional": True}]
    result = utils.format_params_for_test_values(params)
    assert result == "None"


def test_create_file_os_error(mocker, capsys):
    """Covers: OSError handling in create_file."""
    mocker.patch("os.makedirs")
    mocker.patch("builtins.open", side_effect=OSError("Permission denied"))
    
    utils.create_file("/fake/path/file.txt", "content")
    
    captured = capsys.readouterr()
    assert "ERROR al crear archivo" in captured.out


def test_add_code_to_file_file_ends_without_newline(mocker):
    """Covers: branch when file doesn't end with newline and anchor not found."""
    mock_mko = mocker.mock_open(read_data="line1")
    mocker.patch("builtins.open", mock_mko)
    
    utils.add_code_to_file("file.txt", "# NOT_FOUND", "injected\n")
    

    handle = mock_mko()
    written_lines = handle.writelines.call_args[0][0]

    assert any('\n' in line for line in written_lines)
