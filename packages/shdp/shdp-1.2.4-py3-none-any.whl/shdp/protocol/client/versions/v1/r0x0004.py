"""
Full fyve response decoder for SHDP protocol version 0x0004.
This module handles decoding of fyve-encoded file contents with filenames.
"""

import logging

from shdp.utils.bitvec import Msb, ReversedR
from shdp.utils.result import Result
from ....errors import Error, ErrorKind
from ....managers.bits.decoder import BitDecoder
from ....managers.event import EventDecoder, EventEncoder, Frame
from ....managers.registry import EVENT_REGISTRY_MSB
from ...bits.utils import FyveImpl, OperatingCode


class FullFyveResponse(EventDecoder[Msb]):
    """Decoder for fyve-encoded file responses in SHDP protocol.

    Handles decoding of files with their names and contents using 5-bit (fyve) encoding.

    Attributes:
        decoder (BitDecoder[Msb]): Bit decoder for MSB-first reading
        filename (str): Name of the decoded file
        content (str): Decoded file content

    Example:
        >>> decoder = BitDecoder(file_data)
        >>> response = FullFyveResponse(decoder)
        >>> response.decode(frame)
        >>> print(f"File: {response.filename}")
        >>> print(f"Content: {response.content}")
    """

    def __init__(self, decoder: BitDecoder[Msb]) -> None:
        """Initialize fyve response decoder.

        Args:
            decoder: BitDecoder configured for MSB-first reading

        Example:
            >>> decoder = BitDecoder(file_bytes)
            >>> response = FullFyveResponse(decoder)
        """
        logging.debug("[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0004\x1b[0m received")

        self.decoder: BitDecoder[Msb] = decoder
        self.filename: str = ""
        self.content: str = ""

    def decode(self, frame: Frame[Msb]) -> Result[None, Error]:
        """Decode file response from binary frame data.

        Format:
        - Null-terminated filename (UTF-8)
        - Fyve-encoded content until end of frame

        Args:
            frame: Binary frame containing file data

        Example:
            >>> response = FullFyveResponse(decoder)
            >>> response.decode(frame)
            >>> print(f"Loaded {response.filename}")
        """
        data_bytes: list[int] = []
        while True:
            byte = self.decoder.read_data(8).unwrap().to_byte_list()[0]
            if byte == 0:
                break
            data_bytes.append(byte)

        self.filename = bytes(data_bytes).decode("utf-8")

        content: str = ""
        while True:
            if self.decoder.position >= frame.data_size + 56:
                break

            op = FyveImpl.get_op(self.decoder).unwrap()

            if op.kind == OperatingCode.CHARACTER:
                content += op.get_char().unwrap()
            else:
                return Result.Err(
                    Error.new(ErrorKind.USER_DEFINED, "Unsupported operation")
                )

        self.content = content

        return Result.reveal()

    def get_responses(self) -> Result[list[EventEncoder[ReversedR]], Error]:
        """Get list of possible response events.

        Returns:
            Empty list as file responses don't generate additional events

        Example:
            >>> response = FullFyveResponse(decoder)
            >>> response.get_responses()
            []
        """
        return Result.Ok([])


#
# REGISTRY
#

EVENT_REGISTRY_MSB.add_event((1, 0x0004), FullFyveResponse)
