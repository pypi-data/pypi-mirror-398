"""Interaction request decoder for SHDP protocol version 1 (event 0x0005).

This module provides decoding functionality for interaction requests in the
SHDP protocol. It implements the InteractionRequest class which handles
the decoding of client interaction requests and generates responses.

The decoder processes requests by:
    1. Decoding the 64-bit request ID
    2. Decoding UTF-8 string data containing:
       - Function name
       - Parent/table name
       - Optional authentication token
       - Optional object ID
       - Optional JSON parameters
    3. Querying registered listeners for interaction handlers
    4. Generating InteractionResponse objects with results

The module automatically registers the decoder with EVENT_REGISTRY_MSB for
event ID (1, 0x0005), enabling automatic request handling in the protocol.

Example usage:

    >>> from shdp.protocol.server.versions.v1.r0x0005 import InteractionRequest
    >>> from shdp.protocol.managers.bits.decoder import BitDecoder
    >>> from shdp.utils.result import Result
    >>>
    >>> # Decode an interaction request
    >>> decoder = BitDecoder[Msb](request_data)
    >>> request = InteractionRequest(decoder)
    >>> result = request.decode(frame)
    >>> if result.is_ok():
    ...     responses = request.get_responses()
"""

import json
import logging
from typing import Any, Optional, cast

from shdp.utils.bitvec import Lsb, Msb, ReversedR
from shdp.utils.result import Result
from ....errors import Error, ErrorKind
from ....managers.bits.decoder import BitDecoder
from ....managers.event import EventDecoder, EventEncoder, Frame
from ....managers.registry import EVENT_REGISTRY_MSB
from .c0x0006 import InteractionResponse


class InteractionRequest(EventDecoder[Msb]):
    """Interaction request decoder for SHDP protocol.

    This class decodes client interaction requests (event 0x0005) that contain
    function calls with parameters. It extracts the request ID, function name,
    parent/table name, optional authentication token, optional object ID, and
    optional JSON parameters.

    The decoder processes requests by:
        1. Reading the 64-bit request ID
        2. Decoding UTF-8 string data split by null bytes
        3. Validating required fields (function name and parent name)
        4. Parsing optional fields (token, object ID, parameters)
        5. Querying registered listeners to generate responses

    Attributes:
        decoder (BitDecoder[Msb]): Bit decoder for reading request data
        request_id (int): Unique identifier for the request (64-bit)
        parent_name (str): Name of the parent/table containing the function
        function_name (str): Name of the function to call
        object_id (Optional[int]): Optional object identifier
        params (Optional[dict[str, Any]]): Optional JSON parameters for the function
        token (Optional[str]): Optional authentication token

    Example:
        >>> from shdp.protocol.managers.bits.decoder import BitDecoder
        >>> decoder = BitDecoder[Msb](request_data)
        >>> request = InteractionRequest(decoder)
        >>> result = request.decode(frame)
        >>> if result.is_ok():
        ...     print(f"Function: {request.function_name}")
        ...     print(f"Parent: {request.parent_name}")
        ...     responses = request.get_responses()
    """

    def __init__(self, decoder: BitDecoder[Msb]):
        logging.debug(
            "[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;125m0x0005\x1b[0m received"
        )

        self.decoder = decoder
        self.request_id = 0
        self.parent_name = ""
        self.function_name = ""
        self.object_id: Optional[int] = None
        self.params: Optional[dict[str, Any]] = None
        self.token: Optional[str] = None

    def decode(self, frame: Frame) -> Result[None, Error]:
        self.request_id = self.decoder.read_data(64).unwrap().to_int().unwrap()
        byte_length = (frame.data_size - 64) // 8
        data_bytes = []

        for _ in range(byte_length):
            byte = self.decoder.read_data(8).unwrap().to_byte_list()[0]
            data_bytes.append(byte)

        string = bytes(data_bytes).decode("utf-8")
        parts = string.split("\x00")

        self.function_name = parts[0]
        self.parent_name = parts[1]

        if self.parent_name == "":
            return Result.Err(Error.new(ErrorKind.BAD_REQUEST, "Parent name is empty"))

        if self.function_name == "":
            return Result.Err(
                Error.new(ErrorKind.BAD_REQUEST, "Function name is empty")
            )

        self.token = parts[2] if parts[2] != "" else None
        self.object_id = int(parts[3]) if parts[3] != "" else None
        self.params = json.loads(parts[4]) if parts[4] != "" else None

        logging.debug(
            "[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;125m0x0005\x1b[0m: "
            "function_name: %s, table: %s, object_id: %s, params: %s, token: %s",
            self.function_name,
            self.parent_name,
            self.object_id,
            self.params,
            self.token,
        )

        return Result.Ok(None)

    def get_responses(self) -> Result[list[EventEncoder[ReversedR]], Error]:
        listeners = EVENT_REGISTRY_MSB.get_listeners((1, 0x0005))

        if listeners is None:
            return Result.Ok([])

        all_arg_responses = [listener(self) for listener in listeners]
        responses: list[EventEncoder[Lsb]] = []

        for arg_response in all_arg_responses:
            if arg_response.is_ok():
                args_list = arg_response.unwrap()
            else:
                return Result.Err(arg_response.unwrap_err())

            result_response = args_list[0].to_opt_value()

            if result_response.is_ok():
                response = result_response.unwrap()
            else:
                return Result.Err(result_response.unwrap_err())

            responses.append(InteractionResponse(self.request_id, response))

        return Result.Ok(cast(list[EventEncoder[ReversedR]], responses))


#
# REGISTRY
#

EVENT_REGISTRY_MSB.add_event((1, 0x0005), InteractionRequest)
