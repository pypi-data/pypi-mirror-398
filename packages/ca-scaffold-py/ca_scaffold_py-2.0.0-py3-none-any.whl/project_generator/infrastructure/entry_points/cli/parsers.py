from typing import Dict, Any

class McpConnectionParser:
    """Parser for MCP connection definition strings."""
    
    def parse(self, conn_def: str) -> Dict[str, str]:
        """
        Parse an MCP connection string in format:
        'name|endpoint'
        
        Example: 'mcp_sales|http://sales-mcp-server.default.svc.cluster.local'
        """
        parts = conn_def.split('|')
        if len(parts) != 2:
            raise ValueError(
                f"Definición de Conexión MCP debe tener 2 partes separadas por '|': {conn_def}\n"
                f"Formato: 'name|endpoint'\n"
                f"Ejemplo: 'mcp_ventas|http://mcp-ventas.com'"
            )
        
        name, endpoint = [part.strip() for part in parts]
        
        if not name:
            raise ValueError("El nombre de la conexión MCP no puede estar vacío")
        if not endpoint:
            raise ValueError("El endpoint de la conexión MCP no puede estar vacío")
        
        return {
            "name": name,
            "endpoint": endpoint
        }

class ToolDefinitionParser:
    """Parser for tool definition strings."""
    
    def parse(self, tool_def: str) -> Dict[str, str]:
        """
        Parse a tool definition string in format:
        'name|description|params|return_type'
        """
        parts = tool_def.split('|')
        if len(parts) != 4:
            raise ValueError(
                f"Tool definition must have 4 parts separated by '|': {tool_def}\n"
                f"Format: 'name|description|params|return_type'\n"
                f"Example: 'search_books|Search books by author|author: str|List[Dict]'"
            )
        
        name, description, params, return_type = [part.strip() for part in parts]
        
        if not name:
            raise ValueError("Tool name cannot be empty")
        if not description:
            raise ValueError("Tool description cannot be empty")
        
        return {
            "name": name,
            "description": description,
            "params": params if params else "",
            "return_type": return_type if return_type else "Dict[str, Any]"
        }


class PromptDefinitionParser:
    """Parser for prompt definition strings."""

    def parse(self, prompt_def: str) -> Dict[str, str]:
        """
        Parse a prompt definition string in format:
        'name|description'
        
        Example: 'system_prompt|The main system prompt for the assistant'
        """
        parts = prompt_def.split('|')
        if len(parts) != 2:
            raise ValueError(
                f"Prompt definition must have 2 parts separated by '|': {prompt_def}\n"
                f"Format: 'name|description'"
            )
        
        name, description = [part.strip() for part in parts]

        if not name:
            raise ValueError("Prompt name cannot be empty")
        if not description:
            raise ValueError("Prompt description cannot be empty")

        return {"name": name, "description": description}


class ResourceDefinitionParser:
    """Parser for resource definition strings."""

    def parse(self, resource_def: str) -> Dict[str, str]:
        """
        Parse a resource definition string in format:
        'name|uri|description|params|return_type'
        
        Example: 'get_policy|policy://company/{policy_name}|Get a policy document|policy_name: str|Dict'
        """
        parts = resource_def.split('|')
        if len(parts) != 5:
            raise ValueError(
                f"Resource definition must have 5 parts separated by '|': {resource_def}\n"
                f"Format: 'name|uri|description|params|return_type'"
            )

        name, uri, description, params, return_type = [part.strip() for part in parts]

        if not name:
            raise ValueError("Resource name cannot be empty")
        if not uri:
            raise ValueError("Resource URI cannot be empty")
        if not description:
            raise ValueError("Resource description cannot be empty")

        return {
            "name": name,
            "uri": uri,
            "description": description,
            "params": params if params else "",
            "return_type": return_type if return_type else "Dict[str, Any]",
        }