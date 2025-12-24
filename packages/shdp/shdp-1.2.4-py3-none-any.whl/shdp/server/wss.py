import asyncio
import logging
import ssl
from pathlib import Path
from typing import Dict, Optional, Set

import websockets
from websockets.asyncio.server import Server, ServerConnection, serve

from shdp.lib import IShdpServer
from shdp.protocol.errors import Error, ErrorKind
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.managers.registry import EVENT_REGISTRY_MSB
from shdp.utils.bitvec import BitVec
from shdp.utils.result import Result


class ShdpWssServer(IShdpServer[ServerConnection, None]):
    """WebSocket Secure implementation of the SHDP server protocol.

    This class implements a WebSocket server that handles SHDP protocol connections.
    It manages client connections and provides methods for server operations.

    Attributes:
        _server (Optional[websockets.server.WebSocketServer]): The WebSocket server instance
        _clients (Dict[str, ServerConnection]): Dictionary of connected clients
    """

    _cert_path: Path
    _key_path: Path

    def __init__(self, cert_path: Path, key_path: Path):
        """Initialize a new SHDP WebSocket server instance."""
        self._server: Optional[Server] = None
        self._clients: Dict[str, ServerConnection] = {}
        self._cert_path = cert_path
        self._key_path = key_path
        self._active_connections: Set[ServerConnection] = set[ServerConnection]()

    @staticmethod
    async def listen(
        port: int = 15150,
        *,
        cert_path: Optional[Path] = None,
        key_path: Optional[Path] = None,
    ) -> Result[IShdpServer[ServerConnection, None], Error]:
        """Start listening for WebSocket connections on the specified port.

        Args:
            port: Port number to listen on, defaults to 15150
            cert_path: Path to the certificate file
            key_path: Path to the private key file

        Returns:
            Result[IShdpServer[WebSocketServerProtocol], Error]: Ok with server instance if successful,
                                          Err with error details if failed
        """
        if cert_path is None or key_path is None:
            return Result[IShdpServer[ServerConnection, None], Error].Err(
                Error.new(ErrorKind.EXPECTATION_FAILED, "cert_path or key_path is None")
            )

        try:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
            ssl_context.load_cert_chain(cert_path, key_path)

            ws_server = ShdpWsServer(cert_path, key_path)

            server = await serve(
                ws_server._accept,
                host="0.0.0.0",
                port=port,
                ssl=ssl_context,
                ping_interval=20,
                ping_timeout=20,
            )

            ws_server._server = server
            logging.info("SHDP WebSocket server listening on port %d", port)
            return Result[IShdpServer[ServerConnection, None], Error].Ok(ws_server)

        except Exception as e:
            return Result[IShdpServer[ServerConnection, None], Error].Err(
                Error.new(ErrorKind.USER_DEFINED, str(e))
            )

    async def stop(self) -> Result[None, Error]:
        """Close the server and all client connections.

        Returns:
            Result[None, Error]: Ok(None) if closed successfully, Err if failed
        """
        try:
            if self._server is None:
                return Result[None, Error].Err(
                    Error.new(ErrorKind.SERVICE_UNAVAILABLE, "Server not listening")
                )

            # Fermer toutes les connexions clients actives
            close_tasks = [client.close() for client in self._active_connections]
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)

            self._active_connections.clear()
            self._clients.clear()

            self._server.close()
            await self._server.wait_closed()
            self._server = None

            logging.info("SHDP WebSocket server closed")
            return Result[None, Error].Ok(None)

        except Exception as e:
            return Result[None, Error].Err(Error.new(ErrorKind.USER_DEFINED, str(e)))

    def get_clients(self) -> Result[Dict[str, ServerConnection], Error]:
        """Get a dictionary of all connected clients.

        Returns:
            Result[Dict[str, WebSocketServerProtocol], Error]: Ok with clients dict if successful,
                                                             Err if failed
        """
        return Result[Dict[str, ServerConnection], Error].Ok(self._clients)

    async def _accept(self, websocket: ServerConnection) -> None:
        """Handle incoming WebSocket connection.

        Args:
            websocket: The WebSocket connection to handle
        """
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self._clients[client_addr] = websocket
        self._active_connections.add(websocket)
        logging.info(f"Accepted connection from {client_addr}")

        try:
            async for message in websocket:
                if not message:
                    continue

                if not isinstance(message, bytes):
                    raise ValueError("Message is not bytes")

                decoder = BitDecoder(BitVec.from_bytes(message))
                frame_decoder = FrameDecoder(decoder)
                data = frame_decoder.decode().unwrap()
                decoder = frame_decoder.get_decoder()

                factories = EVENT_REGISTRY_MSB.get_event((data.version, data.event))

                if factories is None:
                    await websocket.send(
                        await self._answer_error(
                            data.version,
                            Error.new(ErrorKind.NOT_FOUND, "Event not found"),
                        )
                    )
                    continue

                for factory in factories:
                    event = factory(decoder)
                    event.decode(data)

                    responses = event.get_responses()
                    if responses.is_ok():
                        for response in responses.unwrap():
                            encoder = FrameEncoder(data.version)
                            frame = encoder.encode(response)
                            await websocket.send(frame.unwrap().to_bytes())
                    else:
                        await websocket.send(
                            await self._answer_error(
                                data.version, responses.unwrap_err()
                            )
                        )

        except websockets.exceptions.ConnectionClosed:
            logging.debug("[SHDP:WS::S] Connection closed by client %s", client_addr)
        except Exception as e:
            logging.error("Error handling connection from %s: %s", client_addr, e)
        finally:
            if client_addr in self._clients:
                del self._clients[client_addr]
            self._active_connections.discard(websocket)

    async def _answer_error(self, version: int, error: Error) -> bytes:
        """Generate error response frame.

        Args:
            version: Protocol version
            error: Error to send

        Returns:
            bytes: Encoded error frame
        """
        encoder = FrameEncoder(version)
        return encoder.encode(error.to_error_response()).unwrap().to_bytes()


# Alias for backwards compatibility
ShdpWsServer = ShdpWssServer  # type: ignore
"""Deprecated alias for ShdpWssServer.

This alias is maintained for backwards compatibility but should not be used in new code.
Use ShdpWssServer instead.
"""
