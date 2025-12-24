"""Entry point for running the API server."""

import uvicorn


def main() -> None:
    """Run the API server."""
    uvicorn.run(
        "basic_memory_hooks.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
