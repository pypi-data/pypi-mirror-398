"""Interaction response encoder for SHDP protocol version 1 (event 0x0006).

This module provides encoding functionality for interaction responses in the
SHDP protocol. It implements the InteractionResponse class which handles
the encoding of responses to client interaction requests, including:

    - 64-bit request ID (links response to original request)
    - Optional JSON response data (structured response payload)

The encoder uses LSB-first bit ordering and processes interaction responses by:
    1. Encoding the 64-bit request ID
    2. Optionally encoding JSON response data as UTF-8 bytes (if provided)

This response type is used to send structured data back to the client in
response to interaction requests (event 0x0005), allowing bidirectional
communication between client and server.

Example usage:

    >>> from shdp.protocol.server.versions.v1.c0x0006 import InteractionResponse
    >>> from shdp.utils.result import Result
    >>>
    >>> # Create an interaction response
    >>> data = {"status": "success", "value": 42, "message": "Operation completed"}
    >>> response = InteractionResponse(request_id=123, response=data)
    >>> result = response.encode()
    >>> if result.is_ok():
    ...     encoder = response.get_encoder()
    ...     event_id = response.get_event()  # Returns 0x0006
"""

import json
import logging
from typing import Optional

from shdp.lib import Result
from shdp.utils.bitvec import Lsb
from ....errors import Error
from ....managers.bits.encoder import BitEncoder
from ....managers.event import EventEncoder


class InteractionResponse(EventEncoder[Lsb]):
    """Interaction response encoder for SHDP protocol.

    Handles encoding of interaction responses, including:
    - 64-bit request ID
    - Optional JSON response data

    Attributes:
        encoder (BitEncoder): Bit encoder for the response
        request_id (int): ID of the original request
        response (Optional[dict[str, Any]]): Optional response data

    Example:
        >>> data = {"status": "success", "value": 42}
        >>> response = InteractionResponse(123, data)
        >>> response.encode()
    """

    def __init__(self, request_id: int, response: Optional[dict | list]):
        logging.debug(
            "[\x1b[38;5;227mSHDP\x1b[0m] \x1b[38;5;163m0x0006\x1b[0m created (%d)",
            request_id,
        )

        self.encoder = BitEncoder[Lsb]()
        self.request_id = request_id
        self.response = response

    def encode(self) -> Result[None, Error]:
        self.encoder.add_data(self.request_id, 64)

        if self.response is not None:
            self.encoder.add_bytes(json.dumps(self.response).encode("utf-8"))

        return Result.Ok(None)

    def get_encoder(self) -> BitEncoder[Lsb]:
        return self.encoder

    def get_event(self) -> int:
        return 0x0006
