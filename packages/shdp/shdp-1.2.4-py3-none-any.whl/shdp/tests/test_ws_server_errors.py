"""Tests for WebSocket server error handling.

This test suite verifies the error handling behavior of the WebSocket server implementation,
focusing on error cases and edge conditions.
"""

import pytest
import websockets

from shdp.protocol.errors import ErrorKind
from shdp.server.ws import ShdpWsServer


@pytest.mark.asyncio
async def test_stop_server_not_listening():
    """Test stopping a server that isn't listening.

    Should return SERVICE_UNAVAILABLE error.
    """
    server = ShdpWsServer()

    result = await server.stop()
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.SERVICE_UNAVAILABLE
    assert error.message == "Server not listening"


@pytest.mark.asyncio
async def test_server_stop_error():
    """Test error handling during server shutdown.

    Should return USER_DEFINED error when an exception occurs during shutdown.
    """

    class BrokenWebSocket:
        async def close(self):
            raise websockets.exceptions.ConnectionClosed(
                rcvd=None, sent=None, code=1006, reason="Test error"
            )

    # Create a server with a broken client connection
    server = ShdpWsServer()
    server._server = True  # Simulate server running
    server._active_connections.add(BrokenWebSocket())

    result = await server.stop()
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.USER_DEFINED


@pytest.mark.asyncio
async def test_server_get_clients_success():
    """Test getting clients list from server.

    Should return empty dictionary when no clients are connected.
    """
    server = ShdpWsServer()

    result = server.get_clients()
    assert result.is_ok()
    assert len(result.unwrap()) == 0


if __name__ == "__main__":
    pytest.main([__file__])
