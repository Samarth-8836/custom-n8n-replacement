"""
Main entry point for the Pipeline n8n Alternative server.

Run this file to start the API server:
    python main.py
"""

import uvicorn


def main():
    """
    Start the FastAPI server using uvicorn.
    """
    uvicorn.run(
        "src.api.app:app",  # Use import string for reload support
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info",
    )


if __name__ == "__main__":
    main()
