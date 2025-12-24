"""Core module defining the SHDP protocol interfaces.

This module provides the fundamental abstract base classes for implementing
the SHDP (Streamline Hyperlink Dynamic Protocol) protocol. It defines the contracts
that all SHDP server and client implementations must adhere to.

The module exposes two main interfaces:

    - IShdpServer: Interface for SHDP servers capable of handling multiple
      simultaneous client connections. Servers can listen on a specified port,
      accept connections, manage a collection of connected clients, and shut
      down gracefully.

    - IShdpClient: Interface for SHDP clients capable of connecting to a server
      and sending encoded events. Clients can establish connections, send data,
      retrieve their address, and disconnect.

These interfaces use generic types to allow flexibility in implementation while
maintaining type safety:

    - CT: Client Type - the type of client connection
    - RT: Return Type - the return type for connection acceptance

All methods return Result objects for explicit, type-safe error handling,
following a Rust-like pattern.

Example usage:

    >>> from shdp.lib import IShdpServer, IShdpClient
    >>> from shdp.utils.result import Result
    >>>
    >>> # Server implementation
    >>> class MyServer(IShdpServer[MyClient, MyResult]):
    ...     @staticmethod
    ...     async def listen(port=15150, *, cert_path=None, key_path=None):
    ...         # Listen implementation
    ...         return Result.Ok(server_instance)
    ...
    >>> # Client implementation
    >>> class MyClient(IShdpClient[MyClientType]):
    ...     @staticmethod
    ...     async def connect(to: tuple[str, int]):
    ...         # Connection implementation
    ...         return Result.Ok(client_instance)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, Optional, TypeVar

from .protocol.errors import Error
from .protocol.managers.event import EventEncoder
from .utils.result import Result

CT = TypeVar("CT")
RT = TypeVar("RT")


class IShdpServer(Generic[CT, RT], ABC):
    """Abstract base class for SHDP protocol servers.

    This class defines the interface for SHDP servers that can handle
    connections from multiple clients of type CT.

    Examples:
        >>> class MyServer(IShdpServer[MyClient]):
        ...     @staticmethod
        ...     def listen(port=15150):
        ...         # Implementation
        ...         return Result.Ok(client)
    """

    @staticmethod
    @abstractmethod
    async def listen(
        port: int = 15150,
        *,
        cert_path: Optional[Path] = None,
        key_path: Optional[Path] = None,
    ) -> "Result[IShdpServer[CT, RT], Error]":
        """Start listening for client connections on the specified port.

        Args:
            port: Port number to listen on, defaults to 15150
            cert_path: Path to the certificate file
            key_path: Path to the private key file

        Returns:
            Result containing the connected server if successful, Error if failed

        Example:
            >>> result = server.listen(8080)
            >>> if result.is_ok():
            ...     server = result.unwrap()
        """

    @abstractmethod
    async def _accept(self, connection: CT) -> RT:
        """Internal method to accept incoming connections.

        Returns:
            Result indicating success or failure of accepting connection
        """

    @abstractmethod
    async def stop(self) -> Result[None, Error]:
        """Stop the server and close all client connections.

        Returns:
            Result indicating success or failure of stopping server

        Example:
            >>> server.stop()
        """

    @abstractmethod
    def get_clients(self) -> Result[dict[str, CT], Error]:
        """Get a dictionary of all connected clients.

        Returns:
            Result containing dict mapping 'IP:PORT' strings to client objects

        Example:
            >>> clients = server.get_clients().unwrap()
            >>> for addr, client in clients.items():
            ...     print(f"Client at {addr}")
        """


class IShdpClient(Generic[CT], ABC):
    """Abstract base class for SHDP protocol clients.

    This class defines the interface for SHDP clients that can connect
    to servers and send events.

    Examples:
        >>> class MyClient(IShdpClient[MyClientType]):
        ...     @staticmethod
        ...     def connect(addr: tuple[str, int]):
        ...         # Implementation
        ...         return Result.Ok(client)
    """

    @abstractmethod
    async def send(self, event: EventEncoder) -> Result[None, Error]:
        """Send an encoded event to the server.

        Args:
            event: The encoded event to send

        Returns:
            Result indicating success or failure of sending

        Example:
            >>> event = MyEvent()
            >>> client.send(event)
        """

    @staticmethod
    @abstractmethod
    async def connect(to: tuple[str, int]) -> "Result[IShdpClient[CT], Error]":
        """Connect to a server at the specified address.

        Args:
            to: Tuple of (host, port) to connect to

        Returns:
            Result containing connected client if successful

        Example:
            >>> result = Client.connect(('localhost', 8080))
            >>> if result.is_ok():
            ...     client = result.unwrap()
        """

    @abstractmethod
    async def disconnect(self) -> Result[None, Error]:
        """Disconnect from the server.

        Returns:
            Result indicating success or failure of disconnecting

        Example:
            >>> client.disconnect()
        """

    @abstractmethod
    def get_address(self) -> Result[tuple[str, int], Error]:
        """Get this client's address.

        Returns:
            Result containing (host, port) tuple if successful

        Example:
            >>> addr = client.get_address().unwrap()
            >>> host, port = addr
        """

    @abstractmethod
    async def _accept(self) -> Result[None, Error]:
        """Internal method to accept the connection.

        Returns:
            Result indicating success or failure of accepting
        """
