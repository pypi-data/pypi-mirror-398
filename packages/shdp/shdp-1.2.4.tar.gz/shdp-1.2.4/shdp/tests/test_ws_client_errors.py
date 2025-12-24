"""Tests for WebSocket client error handling.

This test suite verifies the error handling behavior of the WebSocket client implementation,
focusing on error cases and edge conditions.
"""

import pytest
import websockets

from shdp.client.ws import ShdpWsClient
from shdp.protocol.errors import ErrorKind
from shdp.protocol.managers.event import EventEncoder
from shdp.utils.bitvec import Lsb


class MockEventEncoder(EventEncoder[Lsb]):
    """Mock event encoder for testing."""

    def encode(self):
        return None

    def get_encoder(self):
        return None

    def get_event(self) -> int:
        return 0x0000


@pytest.mark.asyncio
async def test_send_without_connection():
    """Test sending event when client is not connected.

    Should return SERVICE_UNAVAILABLE error.
    """
    client = ShdpWsClient()
    event = MockEventEncoder()

    result = await client.send(event)
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.SERVICE_UNAVAILABLE
    assert error.message == "Client not connected"


@pytest.mark.asyncio
async def test_disconnect_without_connection():
    """Test disconnecting when client is not connected.

    Should return SERVICE_UNAVAILABLE error.
    """
    client = ShdpWsClient()

    result = await client.disconnect()
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.SERVICE_UNAVAILABLE
    assert error.message == "Client not connected"


@pytest.mark.asyncio
async def test_get_address_without_connection():
    """Test getting address when client is not connected.

    Should return SERVICE_UNAVAILABLE error.
    """
    client = ShdpWsClient()

    result = client.get_address()
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.SERVICE_UNAVAILABLE
    assert error.message == "Client not connected"


@pytest.mark.asyncio
async def test_accept_without_connection():
    """Test accepting connection when client is not connected.

    Should return SERVICE_UNAVAILABLE error.
    """
    client = ShdpWsClient()

    result = await client._accept()
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.SERVICE_UNAVAILABLE
    assert error.message == "No connection to accept"


@pytest.mark.asyncio
async def test_connect_invalid_host():
    """Test connecting to invalid host.

    Should return USER_DEFINED error.
    """
    result = await ShdpWsClient.connect(("invalid_host_name", 8000))
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.USER_DEFINED


@pytest.mark.asyncio
async def test_connect_invalid_port():
    """Test connecting to invalid port.

    Should return USER_DEFINED error.
    """
    result = await ShdpWsClient.connect(("localhost", -1))
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.USER_DEFINED


@pytest.mark.asyncio
async def test_disconnect_websocket_error():
    """Test error handling when websocket.close() fails.

    Should return USER_DEFINED error.
    """
    client = ShdpWsClient()

    class BrokenWebSocket:
        async def close(self):
            raise websockets.exceptions.ConnectionClosed(
                rcvd=None, sent=None, code=1006, reason="Test error"
            )

    client._websocket = BrokenWebSocket()
    client._address = ("localhost", 8000)  # Simulate connected state

    result = await client.disconnect()
    assert result.is_err()
    error = result.unwrap_err()
    assert error.kind == ErrorKind.USER_DEFINED


if __name__ == "__main__":
    pytest.main([__file__])
