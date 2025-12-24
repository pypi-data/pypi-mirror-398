"""
Client implementation for SHDP protocol version 0x0000.
This module handles component request events using LSB (Least Significant Bit) encoding.
"""

import logging

from shdp.lib import Result
from shdp.utils.bitvec import Lsb
from ....errors import Error
from ....managers.bits.encoder import BitEncoder
from ....managers.event import EventEncoder


class ComponentNeedsRequest(EventEncoder[Lsb]):
    """Event encoder for requesting components in SHDP protocol.

    This class handles the encoding of component request events,
    where a client needs to request a specific component from the server.

    Attributes:
        component_name (str): Name of the component being requested
        encoder (BitEncoder): Bit encoder using LSB (Least Significant Bit) encoding

    Example:
        >>> request = ComponentNeedsRequest("MyComponent")
        >>> request.encode()
        >>> encoder = request.get_encoder()
        >>> event_id = request.get_event()  # Returns 0x0000
    """

    def __init__(self, component_name: str):
        """Initialize a new component request event.

        Args:
            component_name: Name of the component to request

        Example:
            >>> request = ComponentNeedsRequest("AuthModule")
        """
        logging.debug(
            "[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0000\x1b[0m created (%s)",
            component_name,
        )

        self.component_name = component_name
        self.encoder = BitEncoder[Lsb]()

    def encode(self) -> Result[None, Error]:
        """Encode the component name into the bit stream.

        Converts the component name to UTF-8 bytes and adds them to the encoder.

        Example:
            >>> request = ComponentNeedsRequest("Auth")
            >>> request.encode()
            # Encoder now contains UTF-8 encoded bytes for "Auth"
        """
        return self.encoder.add_bytes(bytes(self.component_name, "utf-8"))

    def get_encoder(self) -> BitEncoder[Lsb]:
        """Get the bit encoder containing the encoded component request.

        Returns:
            BitEncoder configured for LSB encoding with the encoded component name

        Example:
            >>> request = ComponentNeedsRequest("Auth")
            >>> request.encode()
            >>> encoder = request.get_encoder()
            # encoder contains the LSB-encoded component name
        """
        return self.encoder

    def get_event(self) -> int:
        """Get the event identifier for component requests.

        Returns:
            0x0000: The event ID for component request events

        Example:
            >>> request = ComponentNeedsRequest("Auth")
            >>> request.get_event()
            0x0000
        """
        return 0x0000
