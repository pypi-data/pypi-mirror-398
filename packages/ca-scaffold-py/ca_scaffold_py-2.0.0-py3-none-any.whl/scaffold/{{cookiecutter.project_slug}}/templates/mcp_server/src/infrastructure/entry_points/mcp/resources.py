from dependency_injector.wiring import inject, Provide

from mcp.server.fastmcp import FastMCP

from typing import Any, List, Dict, Tuple, Set, Optional, Union, Callable, Protocol, TypedDict, Sequence, Mapping, Iterable, Generator

from src.applications.settings.container import Container
from src.domain.usecase.resource_usecase import ResourceUseCase
# ANCHOR_RESOURCES_IMPORT (no borrar)

@inject
def bind_resources(mcp: FastMCP,
                   resource_usecase: ResourceUseCase = Provide[Container.resource_usecase],
                   # ANCHOR_RESOURCES_PROVIDE (no borrar)
                   ):

    """
    Bind resources.
    """

    @mcp.resource("papers://folders")
    async def get_available_folders() -> list[str]:
        """
        List all available topic folders in the papers directory.
        
        This resource provides a simple list of all available topic folders.
        """
        return await resource_usecase.get_available_folders()


    @mcp.resource("papers://{topic}")
    async def get_topic_papers(topic: str) -> str:
        """
        Get detailed information about papers on a specific topic.
        
        Args:
            topic: The research topic to retrieve papers for
        """

        return await resource_usecase.get_topic_papers(topic)
    
    # ANCHOR_RESOURCES_BIND (no borrar)
