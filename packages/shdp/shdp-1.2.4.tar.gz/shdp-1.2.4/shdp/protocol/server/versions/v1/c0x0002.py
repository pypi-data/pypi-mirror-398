"""Error response encoder for SHDP protocol version 1 (event 0x0002).

This module provides encoding functionality for error responses in the SHDP
protocol. It implements the ErrorResponse class which handles the encoding
of error information for transmission, including:

    - 16-bit error code (identifies the specific error)
    - 8-bit padding (for alignment)
    - UTF-8 encoded error message (descriptive text)

The encoder uses LSB-first bit ordering and processes error objects by:
    1. Encoding the 16-bit error code
    2. Adding 8 bits of padding (zero)
    3. Encoding the error message as UTF-8 bytes

This response type is used throughout the protocol to communicate error
conditions from the server to the client in a standardized format.

Example usage:

    >>> from shdp.protocol.server.versions.v1.c0x0002 import ErrorResponse
    >>> from shdp.protocol.errors import Error, ErrorKind
    >>> from shdp.utils.result import Result
    >>>
    >>> # Create an error response
    >>> error = Error(404, ErrorKind.NOT_FOUND, "Page not found")
    >>> response = ErrorResponse(error)
    >>> result = response.encode()
    >>> if result.is_ok():
    ...     encoder = response.get_encoder()
    ...     event_id = response.get_event()  # Returns 0x0002
"""

import logging

from shdp.lib import Result
from shdp.utils.bitvec import Lsb
from ....errors import Error
from ....managers.bits.encoder import BitEncoder
from ....managers.event import EventEncoder


class ErrorResponse(EventEncoder[Lsb]):
    """Error response encoder for SHDP protocol.

    Handles encoding of error responses including:
    - 16-bit error code
    - UTF-8 encoded error message
    - 8-bit padding

    Attributes:
        encoder (BitEncoder): Bit encoder for the response
        error (Error): Error details to encode

    Example:
        >>> error = Error(404, ErrorKind.NOT_FOUND, "Page not found")
        >>> response = ErrorResponse(error)
        >>> response.encode()
    """

    def __init__(self, error: Error):
        logging.debug(
            "[\x1b[38;5;227mSHDP\x1b[0m] \x1b[38;5;160m0x0002\x1b[0m created "
            "(\x1b[38;5;160m%d\x1b[0m): [%s] %s",
            error.code,
            error.kind,
            error.message,
        )
        self.encoder = BitEncoder[Lsb]()
        self.error = error

    def encode(self) -> Result[None, Error]:
        Result.hide()

        self.encoder.add_data(self.error.code, 16)
        self.encoder.add_data(0, 8)
        self.encoder.add_bytes(self.error.message.encode("utf-8"))

        return Result.reveal()

    def get_encoder(self) -> BitEncoder[Lsb]:
        return self.encoder

    def get_event(self) -> int:
        return 0x0002
