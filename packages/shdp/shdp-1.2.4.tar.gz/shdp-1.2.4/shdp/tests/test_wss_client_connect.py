"""Tests for WebSocket client connection functionality.

This test suite verifies the WebSocket client's ability to connect to a server,
handle connection states, and properly manage disconnection scenarios.
"""

import asyncio
import logging
import socket
from pathlib import Path

import pytest

from shdp.client.wss import ShdpWsClient
from shdp.lib import Error, Result
from shdp.protocol.errors import ErrorKind
from shdp.server.wss import ShdpWsServer


def find_free_port():
    """Trouve un port disponible sur le système."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port


@pytest.mark.asyncio
async def test_client_connection():
    """Test successful WebSocket client connection to server."""
    logging.basicConfig(level=logging.DEBUG)

    test_port = find_free_port()
    keys_dir = Path(__file__).parent / "keys"
    server_result = await ShdpWsServer.listen(
        port=test_port,
        cert_path=keys_dir / "cert.pem",
        key_path=keys_dir / "key.pem",
    )
    assert (
        server_result.is_ok()
    ), f"Server failed to start: {server_result.unwrap_err()}"
    server = server_result.unwrap()

    try:

        # Attendre que la connexion soit établie
        await asyncio.sleep(10)

        # Créer une instance du client pour les tests
        client_result: Result[ShdpWsClient, Error] = await ShdpWsClient.connect(
            ("localhost", test_port)
        )
        assert client_result.is_ok(), client_result.unwrap_err()
        client = client_result.unwrap()

        try:
            addr_result = client.get_address()
            assert addr_result.is_ok(), "Failed to get client address"
            assert addr_result.unwrap() == (
                "localhost",
                test_port,
            ), "Client address mismatch"

            clients_result = server.get_clients()
            assert clients_result.is_ok(), "Failed to get server clients"
            assert (
                len(clients_result.unwrap()) == 1
            ), "Server should have exactly one client"

        finally:
            await client.disconnect()

    finally:
        # Nettoyage final
        await server.stop()


@pytest.mark.asyncio
async def test_client_invalid_connection():
    """Test client behavior when connecting to invalid address."""
    invalid_port = -1
    result = await ShdpWsClient.connect(("localhost", invalid_port))
    assert result.is_err(), "Client should fail to connect to invalid port"
    error = result.unwrap_err()
    assert error.kind == ErrorKind.USER_DEFINED, "Incorrect error type returned"


@pytest.mark.asyncio
async def test_client_double_disconnect():
    """Test client behavior when attempting to disconnect twice."""
    test_port = find_free_port()
    keys_dir = Path(__file__).parent / "keys"
    server_result = await ShdpWsServer.listen(
        port=test_port,
        cert_path=keys_dir / "cert.pem",
        key_path=keys_dir / "key.pem",
    )
    assert server_result.is_ok()
    server = server_result.unwrap()

    try:

        # Créer une instance du client pour les tests
        client_result: Result[ShdpWsClient, Error] = await ShdpWsClient.connect(
            ("localhost", test_port)
        )
        assert client_result.is_ok(), client_result.unwrap_err()
        client = client_result.unwrap()

        try:
            # Premier disconnect
            disconnect_result = await client.disconnect()
            assert disconnect_result.is_ok()

            # Second disconnect
            disconnect_result = await client.disconnect()
            assert disconnect_result.is_err()
            assert disconnect_result.unwrap_err().kind == ErrorKind.SERVICE_UNAVAILABLE

        finally:
            await client.disconnect()

    finally:
        # Nettoyage final
        await server.stop()


if __name__ == "__main__":
    pytest.main([__file__])
