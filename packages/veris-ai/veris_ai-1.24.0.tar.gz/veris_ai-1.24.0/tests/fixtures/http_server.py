import multiprocessing
import socket
import time
from typing import AsyncGenerator, Generator

import httpx
import pytest
import uvicorn
from fastapi_mcp import FastApiMCP  # type: ignore[import-untyped]
from mcp import InitializeResult
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import EmptyResult

from veris_ai import veris

from .simple_app import make_simple_fastapi_app

HOST = "127.0.0.1"
SERVER_NAME = "Test MCP Server"


@pytest.fixture
def server_port() -> int:
    with socket.socket() as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


@pytest.fixture
def server_url(server_port: int) -> str:
    return f"http://{HOST}:{server_port}"


def run_server(server_port: int) -> None:
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

    # Give server time to start
    while not server.started:
        time.sleep(0.5)


@pytest.fixture()
def server(server_port: int, simulation_env: bool) -> Generator[None, None, None]:
    proc = multiprocessing.Process(
        target=run_server,
        kwargs={"server_port": server_port},
        daemon=True,
    )
    proc.start()

    # Wait for server to be running
    max_attempts = 20
    attempt = 0
    while attempt < max_attempts:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, server_port))
                break
        except ConnectionRefusedError:
            time.sleep(0.1)
            attempt += 1
    else:
        msg = f"Server failed to start after {max_attempts} attempts"
        raise RuntimeError(msg)
    yield

    # Signal the server to stop - added graceful shutdown before kill
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


@pytest.fixture()
async def http_client(server: None, server_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=server_url) as client:
        yield client


@pytest.mark.anyio
async def test_http_basic_connection(server: None, server_url: str) -> None:
    async with (
        streamablehttp_client(server_url + "/mcp") as (read_stream, write_stream, _),
        ClientSession(read_stream, write_stream) as session,
    ):
        # Test initialization
        result = await session.initialize()
        assert isinstance(result, InitializeResult)
        assert result.serverInfo.name == SERVER_NAME

        # Test ping
        ping_result = await session.send_ping()
        assert isinstance(ping_result, EmptyResult)
