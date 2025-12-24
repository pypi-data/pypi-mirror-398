import uvicorn
from project_generator.applications.app_service import app

def main():
    """Entry point to start the API server."""
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()