import asyncio
import logging
from typing import Optional, Tuple

import websockets
from websockets.asyncio.client import ClientConnection, connect

from ..lib import IShdpClient
from ..protocol.errors import Error, ErrorKind
from ..protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from ..protocol.managers.bits.encoder import FrameEncoder
from ..protocol.managers.event import EventEncoder
from ..protocol.managers.registry import EVENT_REGISTRY_MSB
from ..protocol.versions import Version
from ..utils.bitvec import BitVec
from ..utils.result import Result


class ShdpWsClient(IShdpClient[ClientConnection]):
    """WebSocket implementation of the SHDP client protocol.

    This class implements a WebSocket client that handles SHDP protocol connections.
    It manages the connection to a server and provides methods for client operations.

    Attributes:
        _websocket (Optional[WebSocketClientProtocol]): The WebSocket connection
        _address (Optional[Tuple[str, int]]): The (host, port) of the connected server
    """

    def __init__(self) -> None:
        """Initialize a new SHDP WebSocket client instance."""
        self._websocket: Optional[ClientConnection] = None
        self._address: Optional[Tuple[str, int]] = None

    async def send(self, event: EventEncoder) -> Result[None, Error]:
        """Send an encoded event to the server.

        Args:
            event: The encoded event to send

        Returns:
            Result[None, Error]: Ok(None) if sent successfully, Err if failed
        """
        try:
            if self._websocket is None:
                return Result.Err(
                    Error.new(ErrorKind.SERVICE_UNAVAILABLE, "Client not connected")
                )

            frame = FrameEncoder(Version.V1.value).encode(event)
            await self._websocket.send(frame.unwrap().to_bytes())
            logging.debug(f"[SHDP:WS::C] Event sent: {event.get_event()}")
            return Result.Ok(None)

        except Exception as e:
            return Result.Err(Error.new(ErrorKind.USER_DEFINED, str(e)))

    @staticmethod
    async def connect(
        to: Tuple[str, int],
    ) -> Result[IShdpClient[ClientConnection], Error]:
        """Connect to a server at the specified address.

        Args:
            to: Tuple of (host, port) to connect to

        Returns:
            Result[ShdpWsClient, Error]: Ok with client instance if successful,
                                       Err with error details if failed
        """
        try:
            client = ShdpWsClient()
            uri = f"ws://{to[0]}:{to[1]}"

            client._websocket = await connect(uri, ping_interval=20, ping_timeout=20)
            client._address = to

            asyncio.create_task(client._accept())

            logging.info(f"Connected to SHDP WebSocket server at {to[0]}:{to[1]}")

            return Result.Ok(client)

        except Exception as e:
            return Result.Err(
                Error.new(
                    ErrorKind.USER_DEFINED,
                    str(e.with_traceback(None)),
                )
            )

    async def disconnect(self) -> Result[None, Error]:
        """Disconnect from the server.

        Returns:
            Result[None, Error]: Ok(None) if disconnected successfully, Err if failed
        """
        try:
            if self._websocket is None:
                return Result.Err(
                    Error.new(ErrorKind.SERVICE_UNAVAILABLE, "Client not connected")
                )

            await self._websocket.close()
            self._websocket = None
            self._address = None

            logging.info("Disconnected from SHDP WebSocket server")
            return Result.Ok(None)

        except Exception as e:
            return Result.Err(Error.new(ErrorKind.USER_DEFINED, str(e)))

    def get_address(self) -> Result[Tuple[str, int], Error]:
        """Get this client's server connection address.

        Returns:
            Result[Tuple[str, int], Error]: Ok with (host, port) if connected,
                                          Err if not connected
        """
        if self._address is None:
            return Result.Err(
                Error.new(ErrorKind.SERVICE_UNAVAILABLE, "Client not connected")
            )
        return Result.Ok(self._address)

    async def _accept(self) -> Result[None, Error]:
        """Accept and process incoming server connection.

        Returns:
            Result[None, Error]: Ok(None) if accepted successfully,
                               Err if failed or no connection exists
        """
        try:
            if self._websocket is None:
                return Result.Err(
                    Error.new(ErrorKind.SERVICE_UNAVAILABLE, "No connection to accept")
                )

            while True:
                try:
                    message = await self._websocket.recv()
                    if not message:
                        logging.debug("[SHDP:WS::C] Connection closed by server")
                        return Result.Err(
                            Error.new(
                                ErrorKind.NO_RESPONSE, "Connection closed by server"
                            )
                        )

                    if not isinstance(message, bytes):
                        raise ValueError("Message is not bytes")

                    decoder = BitDecoder(BitVec.from_bytes(message))
                    frame_decoder = FrameDecoder(decoder)
                    data = frame_decoder.decode().unwrap()
                    decoder = frame_decoder.get_decoder()

                    factories = EVENT_REGISTRY_MSB.get_event((data.version, data.event))
                    if factories is None:
                        return Result.Err(
                            Error.new(ErrorKind.NOT_FOUND, "Event not found")
                        )

                    for factory in factories:
                        event = factory(decoder)
                        event.decode(data)

                        responses = event.get_responses()
                        if responses.is_ok():
                            for response in responses.unwrap():
                                encoder = FrameEncoder(data.version)
                                frame = encoder.encode(response)
                                await self._websocket.send(frame.unwrap().to_bytes())
                        else:
                            return Result.Err(responses.unwrap_err())

                except websockets.exceptions.ConnectionClosed:
                    logging.debug("[SHDP:WS::C] WebSocket connection closed")
                    return Result.Ok(None)

            logging.info("Connection accepted")
            return Result.Ok(None)

        except Exception as e:
            return Result.Err(Error.new(ErrorKind.USER_DEFINED, str(e)))
