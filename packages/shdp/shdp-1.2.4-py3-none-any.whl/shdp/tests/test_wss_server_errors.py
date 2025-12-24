"""Tests for WebSocket server error handling.

This test suite verifies the error handling behavior of the WebSocket server implementation,
focusing on error cases and edge conditions.
"""

from pathlib import Path

import pytest
import websockets

from shdp.protocol.errors import ErrorKind
from shdp.server.wss import ShdpWsServer


@pytest.mark.asyncio
async def test_server_missing_certificates():
    """Test server initialization with missing certificate files.

    Should return EXPECTATION_FAILED error when cert_path or key_path is None.
    """
    server_result = await ShdpWsServer.listen(
        port=8000,
        cert_path=None,
        key_path=None,
    )

    assert server_result.is_err()
    error = server_result.unwrap_err()
    assert error.kind == ErrorKind.EXPECTATION_FAILED
    assert error.message == "cert_path or key_path is None"


@pytest.mark.asyncio
async def test_server_invalid_certificates():
    """Test server initialization with invalid certificate files.

    Should return USER_DEFINED error when certificate files are invalid.
    """
    invalid_path = Path("/nonexistent/path")
    server_result = await ShdpWsServer.listen(
        port=8000,
        cert_path=invalid_path / "cert.pem",
        key_path=invalid_path / "key.pem",
    )

    assert server_result.is_err()
    error = server_result.unwrap_err()
    assert error.kind == ErrorKind.USER_DEFINED


@pytest.mark.asyncio
async def test_stop_server_not_listening():
    """Test stopping a server that isn't listening.

    Should return SERVICE_UNAVAILABLE error.
    """
    server = ShdpWsServer(cert_path=Path("cert.pem"), key_path=Path("key.pem"))

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
    server = ShdpWsServer(cert_path=Path("cert.pem"), key_path=Path("key.pem"))
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
    server = ShdpWsServer(cert_path=Path("cert.pem"), key_path=Path("key.pem"))

    result = server.get_clients()
    assert result.is_ok()
    assert len(result.unwrap()) == 0


if __name__ == "__main__":
    pytest.main([__file__])
