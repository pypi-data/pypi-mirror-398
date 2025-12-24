import os
import re
from project_generator.domain.models.project_models import ProjectInventory

class ProjectAnalyzerAdapter:
    def analyze(self, path: str) -> ProjectInventory:
        root_path = os.path.abspath(path)
        mcp_server_file = os.path.join(root_path, "src/infrastructure/entry_points/mcp/tools.py")
        agent_procode_file = os.path.join(root_path, "infrastructure/entry_points/a2a/a2a_server.py")
        
        project_type = "unknown"
        is_valid = False

        if os.path.exists(os.path.join(root_path, "pyproject.toml")):
            if os.path.exists(mcp_server_file):
                project_type = "mcp_server"
                is_valid = True
            elif os.path.exists(agent_procode_file):
                project_type = "agent_procode"
                is_valid = True

        inventory = ProjectInventory(
            is_valid=is_valid,
            project_path=root_path,
            project_type=project_type,
            existing_resource_uris=[]
        )

        if project_type == "mcp_server":
            tool_pattern = r'@mcp\.tool\(\)\s*async\s*def\s*(\w+)'
            prompt_pattern = r'@mcp\.prompt\("([^"]+)"\)'
            resource_pattern = r'@mcp\.resource\("([^"]+)"\)\s*async\s*def\s*(\w+)'

            inventory.existing_tools = self._find_components(os.path.join(root_path, "src/infrastructure/entry_points/mcp/tools.py"), tool_pattern, group_index=1)
            inventory.existing_prompts = self._find_components(os.path.join(root_path, "src/infrastructure/entry_points/mcp/prompts.py"), prompt_pattern, group_index=1)
            resource_matches = self._find_components_multiple_groups(os.path.join(root_path, "src/infrastructure/entry_points/mcp/resources.py"), resource_pattern)
            inventory.existing_resources = [match[1] for match in resource_matches]
            inventory.existing_resource_uris = [match[0] for match in resource_matches]

        elif project_type == "agent_procode":
            env_path = os.path.join(root_path, "application/settings/.env")
            inventory.existing_mcp_connections = self._find_mcp_connections(env_path)

        return inventory

    def _find_components(self, file_path: str, pattern: str, group_index: int = 1) -> list[str]:
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            matches = re.findall(pattern, content)
            return [match[group_index - 1] if isinstance(match, tuple) else match for match in matches]
        except IOError:
            return []

    def _find_components_multiple_groups(self, file_path: str, pattern: str) -> list[tuple]:
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return re.findall(pattern, content)
        except IOError:
            return []

    def _find_mcp_connections(self, env_path: str) -> list[str]:
        if not os.path.exists(env_path):
            return []
        connections = []
        try:
            with open(env_path, 'r') as f:
                content = f.read()
            matches = re.findall(r'MCP_CONNECTION_\d+_NAME=(.+)', content)
            return [m.strip().strip('"').strip("'") for m in matches]
        except IOError:
            return []