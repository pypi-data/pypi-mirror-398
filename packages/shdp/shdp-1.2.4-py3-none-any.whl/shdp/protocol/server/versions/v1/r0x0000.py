"""Component needs request decoder for SHDP protocol version 1 (event 0x0000).

This module provides decoding functionality for component loading requests
in the SHDP protocol. It implements the ComponentNeedsRequest class which
handles the decoding of component requests and generates appropriate responses.

The decoder processes requests by:
    1. Decoding the component name from UTF-8 bytes
    2. Querying registered listeners for component metadata
    3. Generating responses including:
       - ComponentNeedsResponse (component metadata)
       - HtmlFileResponse (for .html files)
       - FullFyveResponse (for .fyve files)

The module automatically registers the decoder with EVENT_REGISTRY_MSB for
event ID (1, 0x0000), enabling automatic request handling in the protocol.

Example usage:

    >>> from shdp.protocol.server.versions.v1.r0x0000 import (
    ...     ComponentNeedsRequest
    ... )
    >>> from shdp.protocol.managers.bits.decoder import BitDecoder
    >>> from shdp.utils.result import Result
    >>>
    >>> # Decode a component request
    >>> decoder = BitDecoder[Msb](request_data)
    >>> request = ComponentNeedsRequest(decoder)
    >>> result = request.decode(frame)
    >>> if result.is_ok():
    ...     responses = request.get_responses()
"""

import logging
import os
from pathlib import Path
from typing import cast

from shdp.utils.bitvec import BitVec, Lsb, Msb, ReversedR
from shdp.utils.result import Result
from ....errors import Error
from ....managers.bits.decoder import BitDecoder
from ....managers.event import EventDecoder, EventEncoder, Frame
from ....managers.registry import EVENT_REGISTRY_MSB
from .c0x0001 import HtmlFileResponse
from .c0x0003 import ComponentNeedsResponse
from .c0x0004 import FullFyveResponse


class ComponentNeedsRequest(EventDecoder[Msb]):
    """Component request decoder for SHDP protocol.

    Decodes requests for component loading, including:
    - Component name in UTF-8
    - Response generation for HTML and Fyve files
    - Title and file list handling

    Attributes:
        decoder (BitDecoder): Decoder for the request
        requested_component_name (str): Name of requested component

    Example:
        >>> decoder = BitDecoder(request_data)
        >>> request = ComponentNeedsRequest(decoder)
        >>> request.decode(frame)
        >>> print(request.requested_component_name)
    """

    def __init__(self, decoder: BitDecoder[Msb]):
        logging.debug("[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0000\x1b[0m received")

        self.decoder = decoder
        self.requested_component_name = ""

    def decode(self, frame: Frame[Msb]) -> Result[None, Error]:
        data_bytes = []

        for _ in range(frame.data_size // 8):
            temp_data = self.decoder.read_data(8)
            if temp_data.is_ok():
                data_bytes.append(BitVec(temp_data.unwrap()).to_byte_list()[0])
            else:
                return Result.Err(temp_data.unwrap_err())

        self.requested_component_name = "".join([chr(b) for b in data_bytes])

        return Result.Ok(None)

    def get_responses(self) -> Result[list[EventEncoder[ReversedR]], Error]:
        listeners = EVENT_REGISTRY_MSB.get_listeners((1, 0x0000))
        if listeners is None:
            return Result.Ok([])

        all_arg_responses = [listener(self) for listener in listeners]
        responses: list[EventEncoder[Lsb]] = []
        files_name = []

        for arg_response in all_arg_responses:
            if arg_response.is_ok():
                args_list = arg_response.unwrap()
            else:
                return Result.Err(arg_response.unwrap_err())

            result_title = args_list[0].to_opt_text()

            if result_title.is_ok():
                title = result_title.unwrap()
            else:
                return Result.Err(result_title.unwrap_err())

            result_files_path = args_list[1].to_vec_text()

            if result_files_path.is_ok():
                files_path = result_files_path.unwrap()
            else:
                return Result.Err(result_files_path.unwrap_err())

            for path in [os.sep.join(Path(path).parts[-2:]) for path in files_path]:
                files_name.append(path)

            for file_path in files_path:
                if file_path.endswith(".html"):
                    responses.append(HtmlFileResponse(file_path))
                else:
                    responses.append(FullFyveResponse(file_path))

            Result.reveal()

        responses.insert(
            0, ComponentNeedsResponse(self.requested_component_name, title, files_name)
        )

        return Result.Ok(cast(list[EventEncoder[ReversedR]], responses))


#
# REGISTRY
#

EVENT_REGISTRY_MSB.add_event((1, 0x0000), ComponentNeedsRequest)
