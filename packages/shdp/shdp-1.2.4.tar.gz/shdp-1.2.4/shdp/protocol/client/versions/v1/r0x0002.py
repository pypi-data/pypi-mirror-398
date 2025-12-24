"""
Error response decoder for SHDP protocol version 0x0002.
This module handles error responses from the server, including error codes and messages.
"""

import logging

from shdp.utils.bitvec import Msb, ReversedR
from shdp.utils.result import Result
from ....errors import Error
from ....managers.bits.decoder import BitDecoder
from ....managers.event import EventDecoder, EventEncoder, Frame
from ....managers.registry import EVENT_REGISTRY_MSB


class ErrorResponse(EventDecoder[Msb]):
    """Decoder for error responses in SHDP protocol version 0x0002.

    This class handles the decoding of error responses from the server.
    Each error response contains:
    - A 16-bit error code
    - An 8-bit padding
    - A variable-length UTF-8 encoded error message

    Attributes:
        decoder (BitDecoder[Msb]): Bit decoder for MSB-first reading
        code (int): 16-bit error code from server
        message (str): Human-readable error message

    Example:
        >>> decoder = BitDecoder(error_data)
        >>> response = ErrorResponse(decoder)
        >>> response.decode(frame)
        >>> print(f"Error {response.code}: {response.message}")
    """

    def __init__(self, decoder: BitDecoder[Msb]) -> None:
        """Initialize error response decoder.

        Args:
            decoder: BitDecoder configured for MSB-first reading

        Example:
            >>> decoder = BitDecoder(error_bytes)
            >>> response = ErrorResponse(decoder)
        """
        logging.debug("[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0002\x1b[0m received")

        self.decoder: BitDecoder[Msb] = decoder
        self.code: int = 0
        self.message: str = ""

    def decode(self, frame: Frame[Msb]) -> Result[None, Error]:
        """Decode error response from binary frame data.

        Frame structure:
        - First 16 bits: Error code
        - Next 8 bits: Padding (skipped)
        - Remaining bits: UTF-8 encoded error message

        Args:
            frame: Binary frame containing error data

        Example:
            >>> response = ErrorResponse(decoder)
            >>> response.decode(frame)
            >>> if response.code == 404:
            ...     print("Resource not found:", response.message)
        """
        # Read 16-bit error code
        self.code = self.decoder.read_data(16).unwrap().to_int().unwrap()
        # Skip 8-bit padding
        self.decoder.position += 8

        # Read remaining bytes as UTF-8 message
        data: list[int] = []
        for _ in range((frame.data_size - 24) // 8):
            data.append(self.decoder.read_data(8).unwrap().to_byte_list()[0])

        self.message = "".join(chr(d) for d in data)

        return Result.reveal()

    def get_responses(self) -> Result[list[EventEncoder[ReversedR]], Error]:
        """Get list of possible response events.

        Returns:
            Empty list as error responses don't generate additional events

        Example:
            >>> response = ErrorResponse(decoder)
            >>> response.get_responses()
            []
        """
        return Result.Ok([])


#
# REGISTRY
#

EVENT_REGISTRY_MSB.add_event((1, 0x0002), ErrorResponse)
