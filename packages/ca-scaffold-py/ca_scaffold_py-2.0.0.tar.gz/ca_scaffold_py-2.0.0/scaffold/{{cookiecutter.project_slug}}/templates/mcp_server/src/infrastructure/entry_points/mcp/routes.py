from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

def bind_routes(mcp: FastMCP):
    """
    TODO: If you want to use dependency injection, test with class to inject
    the use case, otherwise you can use the function directly:
    i.e. bind_routes(mcp, prompt_usecase=Provide[Container.prompt_usecase])

    Bind routes to the FastMCP instance.
    """

    @mcp.custom_route(name="health_check", path="/v1/api/health", methods=["GET"])
    async def health_check(_request: Request) -> Response:
        """
        Health check endpoint to verify the server is running.
        
        Returns:
            JSON response indicating the server is healthy.
        """

        response_data = {"status": "ok"}
        return JSONResponse(response_data)

    @mcp.custom_route(name="readiness_check", path="/v1/health/readiness", methods=["GET"])
    async def readiness_check(_request: Request) -> Response:
        return JSONResponse({"status": "ready"})
    
    @mcp.custom_route(name="liveness_check", path="/v1/health/liveliness", methods=["GET"])
    async def liveness_check(_request: Request) -> Response:
        return JSONResponse({"status": "alive"})
    
    @mcp.custom_route(name="startup_check", path="/v1/health/startup", methods=["GET"])
    async def startup_check(_request: Request) -> Response:
        return JSONResponse({"status": "started"})