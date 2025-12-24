"""
Interaction response decoder for SHDP protocol version 0x0006.
This module handles server responses to interaction requests, including JSON-formatted
    results.
"""

import json
import logging

from shdp.utils.bitvec import Msb, ReversedR
from shdp.utils.result import Result
from ....errors import Error
from ....managers.bits.decoder import BitDecoder, Frame
from ....managers.event import EventDecoder, EventEncoder
from ....managers.registry import EVENT_REGISTRY_MSB


class InteractionResponse(EventDecoder[Msb]):
    """Decoder for interaction responses in SHDP protocol.

    Handles decoding of server responses to interaction requests.
    Each response contains:
    - 64-bit request ID
    - JSON-encoded response data

    Attributes:
        decoder (BitDecoder[Msb]): Bit decoder for MSB-first reading
        request_id (int): ID of the original request
        response (dict | list | None): Decoded JSON response data

    Example:
        >>> decoder = BitDecoder(response_data)
        >>> response = InteractionResponse(decoder)
        >>> response.decode(frame)
        >>> print(f"Response to request {response.request_id}:", response.response)
    """

    def __init__(self, decoder: BitDecoder[Msb]) -> None:
        """Initialize interaction response decoder.

        Args:
            decoder: BitDecoder configured for MSB-first reading

        Example:
            >>> decoder = BitDecoder(response_bytes)
            >>> response = InteractionResponse(decoder)
        """
        logging.debug("[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0006\x1b[0m received")

        self.decoder: BitDecoder[Msb] = decoder
        self.request_id = 0
        self.response: dict | list | None = None

    def decode(self, frame: Frame[Msb]) -> Result[None, Error]:
        """Decode interaction response from binary frame data.

        Format:
        - 64-bit request ID
        - JSON-encoded response data

        Args:
            frame: Binary frame containing response data

        Example:
            >>> response = InteractionResponse(decoder)
            >>> response.decode(frame)
            >>> if isinstance(response.response, dict):
            ...     print("Status:", response.response.get("status"))
        """
        self.request_id = self.decoder.read_data(64).unwrap().to_int().unwrap()

        data_bytes: list[int] = []
        for _ in range((frame.data_size - 64) // 8):
            data_bytes.append(self.decoder.read_data(8).unwrap().to_byte_list()[0])

        data: str = bytes(data_bytes).decode("utf-8")

        if data != "":
            self.response = json.loads(data)
        else:
            self.response = None

        return Result.Ok(None)

    def get_responses(self) -> Result[list[EventEncoder[ReversedR]], Error]:
        """Get list of possible response events.

        Returns:
            Empty list as interaction responses don't generate additional events

        Example:
            >>> response = InteractionResponse(decoder)
            >>> response.get_responses()
            []
        """
        return Result.Ok([])


#
# REGISTRY
#

EVENT_REGISTRY_MSB.add_event((1, 0x0006), InteractionResponse)
