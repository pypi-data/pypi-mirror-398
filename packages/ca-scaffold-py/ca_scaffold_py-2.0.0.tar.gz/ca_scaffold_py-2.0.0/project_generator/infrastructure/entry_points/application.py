from fastapi import FastAPI
from project_generator.applications.settings.container import container
from project_generator.infrastructure.entry_points.api_routes import router

def create_application() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    
    container.wire(modules=[".api_routes"])

    app = FastAPI(
        title="MCP Project Generator API",
        description="An API to generate MCP projects from a dynamic scaffold."
    )

    app.include_router(router)

    return app
