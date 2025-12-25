"""Example demonstrating different import options for the Veris AI SDK.

This file shows how to import and use the SDK with minimal dependencies.
"""

# Option 1: Default imports (only base dependencies required)
# This works with just: pip install veris-ai
import os
from typing import Any

from veris_ai import JaegerClient, SearchQuery, veris


# Example using the mock decorator (requires only base deps)
@veris.mock()
async def process_data(input_data: dict) -> dict:
    """Process some data."""
    return {"processed": True, "data": input_data}


# Example using Jaeger client (requires only base deps)
def query_traces() -> Any:  # noqa: ANN401
    """Query traces from Jaeger."""
    client = JaegerClient(base_url="http://localhost:16686")
    query = SearchQuery(service="my-service", limit=10)
    return client.search(query)


# Option 2: Using optional features (requires extra dependencies)
# This requires: pip install veris-ai[instrument]
try:
    from veris_ai import instrument

    # Set up tracing (only works if [instrument] deps are installed)
    instrument(service_name="my-service")
except ImportError as e:
    print(f"Tracing not available: {e}")
    print("Install with: pip install veris-ai[instrument]")


# Option 3: Direct submodule imports for maximum control
# Import only what you need
from veris_ai.tool_mock import veris as mock_tool  # noqa: E402


# Use the directly imported modules
@mock_tool.stub(return_value={"status": "ok"})
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01"}


# Option 4: FastAPI integration (requires [fastapi] extra)
if os.getenv("USE_FASTAPI") == "true":
    try:
        from fastapi import FastAPI

        app = FastAPI()

        # This method only imports FastAPI deps when called
        veris.set_fastapi_mcp(
            fastapi=app,
            name="My API Server",
        )
        # Mount the MCP server with HTTP transport (recommended)
        # Note: User must call this separately after set_fastapi_mcp
        veris.fastapi_mcp.mount_http()
    except ImportError:
        print("FastAPI integration requires: pip install veris-ai[fastapi]")
