import logging
import os
from contextlib import asynccontextmanager
from functools import partial
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from src.applications.settings.container import Container
from src.applications.settings.settings import Config
from src.infrastructure.entry_points.mcp.routes import set_routes
from src.infrastructure.entry_points.mcp import (prompts,
                                                 resources,
                                                 tools)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI, fast_mcp: FastMCP):
    """
    Context manager to manage IoC and lifespan of the application.
    """
    tools.bind_tools(fast_mcp)
    resources.bind_resources(fast_mcp)
    prompts.bind_prompts(fast_mcp)
    async with fast_mcp.session_manager.run():
        yield


def create_application():
    """Create and configure FastAPI application with MCP server.

    Returns:
        FastAPI: Configured application instance with MCP integration.
    """
    container = Container()
    container.config.from_pydantic(Config())
    container.wire(modules=[tools, resources, prompts])
    fast_mcp = FastMCP("customer", stateless_http=True)
    logger.info("MCP server starting...")
    prefix = container.config.url_prefix()
    origins = os.getenv(
        "ALLOW_ORIGINS",
        "https://informacion-int-dev.apps.ambientesbc.com/"
    ).split(",")
    methods = os.getenv("ALLOW_METHODS", "POST,GET,OPTIONS").split(",")
    headers = os.getenv("ALLOW_HEADERS", "*").split(",")
    app = FastAPI(
        lifespan=partial(lifespan, fast_mcp=fast_mcp),
    )
    app.add_middleware(CORSMiddleware,
                       allow_origins=origins,
                       allow_credentials=True,
                       allow_methods=methods,
                       allow_headers=headers,
                       max_age=600)
    app.include_router(set_routes(prefix))
    app.mount(prefix, app=fast_mcp.streamable_http_app())
    return app
