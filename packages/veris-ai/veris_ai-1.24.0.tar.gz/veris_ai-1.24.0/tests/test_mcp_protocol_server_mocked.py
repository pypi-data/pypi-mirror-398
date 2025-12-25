import json
import multiprocessing
import os
import socket
import time
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
import uvicorn
from mcp import ClientSession, ListToolsResult
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult

from veris_ai import veris
from tests.test_helpers import create_test_token

from .fixtures.simple_app import make_simple_fastapi_app

HOST = "127.0.0.1"
SERVER_NAME = "Test MCP Server"


def run_server_with_mock(server_port: int) -> None:  # noqa: C901
    """Run server with mocked veris API client methods."""
    os.environ["VERIS_API_URL"] = "http://test-endpoint"

    # Create a mock function for the API client
    def mock_post(endpoint, payload):
        # Log the request
        with Path("/tmp/veris_mock_payloads.log").open("a") as f:
            import json as json_module

            f.write(json_module.dumps(payload) + "\n")
            f.flush()

        try:
            # Try to extract item_id from the payload
            if payload and "tool_call" in payload and "parameters" in payload["tool_call"]:
                params = payload["tool_call"]["parameters"]
                # Handle both direct value and nested value structure
                if "item_id" in params:
                    if isinstance(params["item_id"], dict) and "value" in params["item_id"]:
                        # Convert string to int if needed
                        item_id = int(params["item_id"]["value"])
                    else:
                        item_id = int(params["item_id"])
                else:
                    item_id = 1  # Default
            else:
                item_id = 1  # Default

            return {
                "id": item_id,
                "name": f"Item {item_id}",
                "price": item_id * 10.0,
                "tags": [f"tag{item_id}"],
                "description": f"Item {item_id} description",
            }
        except Exception as e:
            # Return error response if something goes wrong
            return {"error": str(e)}

    # Patch the API client's post methods (both sync and async)
    from veris_ai.api_client import get_api_client

    async def mock_post_async(endpoint, payload):
        return mock_post(endpoint, payload)

    with (
        patch.object(get_api_client(), "post", side_effect=mock_post),
        patch.object(get_api_client(), "post_async", side_effect=mock_post_async),
    ):
        # Configure the server
        fastapi = make_simple_fastapi_app()
        veris.set_fastapi_mcp(
            fastapi=fastapi,
            name=SERVER_NAME,
            description="Test description",
        )
        assert veris.fastapi_mcp is not None
        veris.fastapi_mcp.mount_http()  # Use HTTP transport

        # Start the server
        server = uvicorn.Server(
            config=uvicorn.Config(app=fastapi, host=HOST, port=server_port, log_level="error"),
        )
        server.run()


@pytest.fixture
def server_port_mocked() -> int:
    with socket.socket() as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


@pytest.fixture
def server_url_mocked(server_port_mocked: int) -> str:
    return f"http://{HOST}:{server_port_mocked}"


@pytest.fixture()
def server_mocked(server_port_mocked: int, simulation_env: None) -> Generator[None, None, None]:
    # Clear the log file
    try:
        with Path("/tmp/veris_mock_payloads.log").open("w") as f:
            f.write("")
    except:
        pass

    proc = multiprocessing.Process(
        target=run_server_with_mock,
        kwargs={"server_port": server_port_mocked},
        daemon=True,
    )
    proc.start()

    # Wait for server to be running
    max_attempts = 20
    attempt = 0
    while attempt < max_attempts:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, server_port_mocked))
                break
        except ConnectionRefusedError:
            time.sleep(0.1)
            attempt += 1
    else:
        msg = f"Server failed to start after {max_attempts} attempts"
        raise RuntimeError(msg)
    yield

    # Signal the server to stop
    try:
        proc.terminate()
        proc.join(timeout=2)
    except (OSError, AttributeError):
        pass

    if proc.is_alive():
        proc.kill()
        proc.join(timeout=2)
        if proc.is_alive():
            msg = "server process failed to terminate"
            raise RuntimeError(msg)


@pytest.mark.asyncio
async def test_http_tool_call_mocked(server_mocked: None, server_url_mocked: str) -> None:
    """Test HTTP tool call with mocked HTTP endpoint."""
    session_id = "test-session-id"
    # Create a proper base64-encoded token
    token = create_test_token(session_id, "test-thread-id")

    async with (
        streamablehttp_client(
            server_url_mocked + "/mcp",
            headers={"Authorization": f"Bearer {token}"},
        ) as (read_stream, write_stream, _),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        tools_list_result = await session.list_tools()
        assert isinstance(tools_list_result, ListToolsResult)
        assert len(tools_list_result.tools) > 0

        tool_call_result = await session.call_tool("get_item", {"item_id": 1})
        assert isinstance(tool_call_result, CallToolResult)
        assert not tool_call_result.isError
        assert tool_call_result.content is not None
        assert len(tool_call_result.content) > 0

        # Read the captured payloads
        with Path("/tmp/veris_mock_payloads.log").open("r") as f:
            payloads = f.readlines()

        assert len(payloads) > 0, "No payloads were captured"

        # Parse and verify the payload
        payload_str = payloads[0].strip()
        payload = json.loads(payload_str)

        # Verify the session_id was passed correctly (should use thread_id as value)
        assert payload["session_id"] == "test-thread-id"
        assert payload["tool_call"]["function_name"] == "get_item"

        # Handle both direct value and nested value structure
        params = payload["tool_call"]["parameters"]
        if "item_id" in params:
            if isinstance(params["item_id"], dict) and "value" in params["item_id"]:
                assert int(params["item_id"]["value"]) == 1
            else:
                assert int(params["item_id"]) == 1

        print(f"SUCCESS: Verified session_id '{session_id}' was sent in payload")
        print(f"SUCCESS: Full captured payload: {json.dumps(payload, indent=2)}")
