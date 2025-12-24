from typing import List, Dict
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection

from infrastructure.driven_adapters.logging.logger_config import LoggerConfig


class MCPClient:
    def __init__(self, mcp_connections: List[Dict[str, str]]):
        self.logger = LoggerConfig().get_logger(self.__class__.__name__)
        """ Initialize MCP client for multiple servers """
        
        server_connections = {}
        if not mcp_connections:
            self.logger.warning("No MCP connections provided in configuration.")
        else:
            self.logger.info(f"Initializing MCPClient with {len(mcp_connections)} connection(s)...")
            for conn in mcp_connections:
                name = conn.get("name")
                endpoint = conn.get("endpoint")
                
                if not name or not endpoint:
                    self.logger.warning(f"Omitiendo conexión MCP inválida (falta nombre o endpoint): {conn}")
                    continue
                
                connection_config: StreamableHttpConnection = {
                    "url": endpoint,
                    "transport": "streamable_http",
                }
                server_connections[name] = connection_config
                self.logger.info(f"MCP Connection configured: '{name}' -> {endpoint}")

        self.mcp_client = MultiServerMCPClient(server_connections)

    async def get_tools(self):
        """ Get tools from ALL configured MCP servers """
        try:
            self.logger.info("Fetching tools from all configured MCP servers...")
            tools = await self.mcp_client.get_tools()
            self.logger.info(f"Successfully fetched {len(tools)} tools.")
        except Exception as e:
            self.logger.warning(f"Error getting tools from MCP servers: {e}")
            tools = []
        return tools