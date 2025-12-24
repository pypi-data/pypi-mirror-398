"""
Component needs response decoder for SHDP protocol version 0x0003.
This module handles component needs responses from the server, including:
- Component name and optional title
- List of required files
- UTF-8 encoded data with null byte separators
"""

import logging

from shdp.utils.bitvec import Msb, ReversedR
from shdp.utils.result import Result
from ....errors import Error
from ....managers.bits.decoder import BitDecoder
from ....managers.event import EventDecoder, EventEncoder, Frame
from ....managers.registry import EVENT_REGISTRY_MSB


class ComponentNeedsResponse(EventDecoder[Msb]):
    """Decoder for component needs responses in SHDP protocol version 0x0003.

    This class handles the decoding of component requirements from the server.
    The response contains:
    - Component name and optional title (separated by 0x01)
    - List of required files (separated by null bytes)

    Attributes:
        decoder (BitDecoder[Msb]): Bit decoder for MSB-first reading
        component_name (str): Name of the requested component
        title (str): Optional title for the component
        files (list[str]): List of required files for the component

    Example:
        >>> decoder = BitDecoder(response_data)
        >>> response = ComponentNeedsResponse(decoder)
        >>> response.decode(frame)
        >>> print(f"Component: {response.component_name}")
        >>> print(f"Title: {response.title}")
        >>> print("Required files:", response.files)
    """

    def __init__(self, decoder: BitDecoder[Msb]) -> None:
        """Initialize component needs response decoder.

        Args:
            decoder: BitDecoder configured for MSB-first reading

        Example:
            >>> decoder = BitDecoder(response_bytes)
            >>> response = ComponentNeedsResponse(decoder)
        """
        logging.debug("[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0003\x1b[0m received")

        self.decoder: BitDecoder[Msb] = decoder
        self.component_name: str = ""
        self.title: str = ""
        self.files: list[str] = []

    def decode(self, frame: Frame[Msb]) -> Result[None, Error]:
        """Decode component needs response from binary frame data.

        Frame structure:
        - Component info (null byte terminated):
          - Component name and title separated by 0x01
        - List of required files (each null byte terminated)

        Args:
            frame: Binary frame containing component data

        Example:
            >>> response = ComponentNeedsResponse(decoder)
            >>> response.decode(frame)
            >>> print(f"Loading {response.component_name}...")
            >>> for file in response.files:
            ...     print(f"Required: {file}")
        """
        # Read all bytes and decode as UTF-8
        data_bytes: list[int] = []
        for _ in range(frame.data_size // 8):
            data_bytes.append(self.decoder.read_data(8).unwrap().to_byte_list()[0])

        data: str = bytes(data_bytes).decode("utf-8")
        parts: list[str] = data.split("\0")
        component_names: list[str] = parts[0].split("\x01")
        parts.pop(0)

        self.component_name = component_names[0]

        if component_names[1]:
            self.title = component_names[1]

        for part in parts:
            self.files.append(part)

        return Result.reveal()

    def get_responses(self) -> Result[list[EventEncoder[ReversedR]], Error]:
        """Get list of possible response events.

        Returns:
            Empty list as component needs responses don't generate additional events

        Example:
            >>> response = ComponentNeedsResponse(decoder)
            >>> response.get_responses()
            []
        """
        return Result.Ok([])


#
# REGISTRY
#

EVENT_REGISTRY_MSB.add_event((1, 0x0003), ComponentNeedsResponse)
