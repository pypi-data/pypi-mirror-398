"""Tests for full client-server interaction flow.

This test suite verifies the complete flow of:
1. Client connecting to server
2. Client sending interaction requests
3. Server processing requests and sending responses
4. Client handling responses
"""

import logging
import socket
from pathlib import Path
from typing import cast

import pytest

from shdp.client.wss import ShdpWsClient
from shdp.lib import Error, Result
from shdp.protocol.args import Arg
from shdp.protocol.client.versions.v1.c0x0000 import (
    ComponentNeedsRequest as ClientComponentNeedsRequest,
)
from shdp.protocol.client.versions.v1.c0x0005 import InteractionRequest as ClientRequest
from shdp.protocol.managers.event import EventDecoder
from shdp.protocol.managers.registry import EVENT_REGISTRY_MSB
from shdp.protocol.server.versions.v1.r0x0000 import ComponentNeedsRequest
from shdp.protocol.server.versions.v1.r0x0005 import InteractionRequest
from shdp.protocol.versions import Version
from shdp.server.wss import ShdpWsServer


def component_needs_request_listen(decoder: EventDecoder) -> list[Arg]:
    """Gestionnaire d'événements pour les requêtes de composants."""
    decoder = cast(ComponentNeedsRequest, decoder)

    args: list[Arg] = []

    args.append(Arg(Arg.OPT_TEXT, "TestComponent"))
    args.append(Arg(Arg.VEC_TEXT, ["test.html", "test.css", "test.js"]))

    return args


def interaction_request_listen(decoder: EventDecoder) -> list[Arg]:
    """Gestionnaire d'événements pour les requêtes d'interaction."""
    decoder = cast(InteractionRequest, decoder)

    args: list[Arg] = []

    response_data = {
        "status": "success",
        "request_id": decoder.request_id,
        "function": decoder.function_name,
        "component": decoder.parent_name,
        "processed_params": decoder.params,
    }

    args.append(Arg(Arg.OPT_VALUE, response_data))

    return args


# Enregistrer les gestionnaires d'événements
EVENT_REGISTRY_MSB.add_listener(
    (Version.V1.value, 0x0000), lambda decoder: component_needs_request_listen(decoder)
)
EVENT_REGISTRY_MSB.add_listener(
    (Version.V1.value, 0x0005), lambda decoder: interaction_request_listen(decoder)
)


def find_free_port():
    """Trouve un port disponible sur le système."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port


@pytest.mark.asyncio
async def test_client_full_front_interaction():
    """Test complete client-server interaction flow."""
    logging.basicConfig(level=logging.DEBUG)

    # Démarrer le serveur
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
        # Créer une instance du client pour les commandes
        client_result: Result[ShdpWsClient, Error] = await ShdpWsClient.connect(
            ("localhost", test_port)
        )
        assert client_result.is_ok(), client_result.unwrap_err()
        client = client_result.unwrap()

        try:
            # Test d'interaction basique
            request = ClientRequest(
                request_id=12345,
                function_name="getData",
                parent_name="TestComponent",
                object_id=1,
                params={"type": "user_info"},
                token=None,
            )

            # Envoyer la requête
            result = await client.send(request)
            assert result.is_ok(), result.unwrap_err().message

            # Test d'interaction authentifiée
            auth_request = ClientRequest(
                request_id=67890,
                function_name="updateProfile",
                parent_name="UserProfile",
                object_id=None,
                params={"name": "Test User"},
                token="test_auth_token",
            )

            # Envoyer la requête authentifiée
            result = await client.send(auth_request)
            assert result.is_ok(), result.unwrap_err().message

        finally:
            await client.disconnect()

    finally:
        # Nettoyage final
        await server.stop()


@pytest.mark.asyncio
async def test_client_component_request():
    """Test component request flow."""
    logging.basicConfig(level=logging.DEBUG)

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
        # Créer une instance du client pour les commandes
        client_result: Result[ShdpWsClient, Error] = await ShdpWsClient.connect(
            ("localhost", test_port)
        )
        assert client_result.is_ok(), client_result.unwrap_err()
        client = client_result.unwrap()

        try:
            # Demander un composant
            request = ClientComponentNeedsRequest("TestComponent")
            logging.info(f"Sending request: {request}")

            # Envoyer la requête
            result = await client.send(request)
            logging.info(f"Request result: {result}")
            assert result.is_ok(), result.unwrap_err().message

        finally:
            await client.disconnect()

    finally:
        # Nettoyage final
        await server.stop()


if __name__ == "__main__":
    pytest.main([__file__])
