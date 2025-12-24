"""Tests for WebSocket server initialization and management.

This test suite verifies the WebSocket server's ability to start up, handle connections,
and properly manage shutdown scenarios.
"""

import asyncio
import logging
import socket

import pytest

from shdp.protocol.errors import ErrorKind
from shdp.server.ws import ShdpWsServer


def find_free_port():
    """Trouve un port disponible sur le système."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port


@pytest.mark.asyncio
async def test_server_opening():
    """Test successful WebSocket server startup and shutdown."""
    logging.basicConfig(level=logging.DEBUG)

    test_port = find_free_port()
    server_result = await ShdpWsServer.listen(port=test_port)
    assert (
        server_result.is_ok()
    ), f"Server failed to start: {server_result.unwrap_err()}"
    server = server_result.unwrap()

    try:
        assert server._server is not None, "Invalid server internal state"

        clients_result = server.get_clients()
        assert clients_result.is_ok(), "Failed to get client list"
        assert len(clients_result.unwrap()) == 0, "New server should have no clients"

        await asyncio.sleep(0.1)

    finally:
        close_result = await server.stop()
        assert (
            close_result.is_ok()
        ), f"Server failed to close: {close_result.unwrap_err()}"


@pytest.mark.asyncio
async def test_server_invalid_port():
    """Test server behavior when starting on invalid port."""
    invalid_port = -1
    server_result = await ShdpWsServer.listen(port=invalid_port)

    assert server_result.is_err(), "Server should fail to start on invalid port"
    error = server_result.unwrap_err()
    assert error.kind == ErrorKind.USER_DEFINED, "Incorrect error type returned"


@pytest.mark.asyncio
async def test_server_double_close():
    """Test server behavior when attempting to close twice."""
    test_port = find_free_port()
    server_result = await ShdpWsServer.listen(port=test_port)
    assert server_result.is_ok()
    server = server_result.unwrap()

    close_result = await server.stop()
    assert close_result.is_ok()

    close_result = await server.stop()
    assert close_result.is_err()
    assert close_result.unwrap_err().kind == ErrorKind.SERVICE_UNAVAILABLE


if __name__ == "__main__":
    pytest.main([__file__])
