"""
Interaction request encoder for SHDP protocol version 0x0005.
This module handles client-side interaction requests, including function
    calls and parameter passing.
"""

import json
import logging

from shdp.utils.bitvec import Lsb
from shdp.utils.result import Result
from ....errors import Error
from ....managers.bits.encoder import BitEncoder
from ....managers.event import EventEncoder


class InteractionRequest(EventEncoder[Lsb]):
    """Encoder for client interaction requests in SHDP protocol.

    Handles encoding of function calls with parameters and authentication tokens.
    Data is encoded using LSB (Least Significant Bit) encoding.

    Attributes:
        encoder (BitEncoder[Lsb]): Bit encoder for LSB encoding
        request_id (int): Unique identifier for this request
        function_name (str): Name of the function to call
        parent_name (str): Name of the parent component
        object_id (int | None): Optional object identifier
        params (dict | list | None): Optional parameters for the function
        token (str | None): Optional authentication token

    Example:
        >>> request = InteractionRequest(1, "click", "Button", 42,
        ...                             {"x": 100, "y": 200}, "auth_token")
        >>> request.encode()
        >>> encoder = request.get_encoder()
    """

    def __init__(
        self,
        request_id: int,
        function_name: str,
        parent_name: str,
        object_id: int | None,
        params: dict | list | None,
        token: str | None,
    ):
        """Initialize an interaction request.

        Args:
            request_id: Unique identifier for this request
            function_name: Name of the function to call
            parent_name: Name of the parent component
            object_id: Optional object identifier
            params: Optional parameters for the function
            token: Optional authentication token

        Example:
            >>> request = InteractionRequest(1, "setValue", "Input", 123,
            ...                             {"value": "Hello"}, None)
        """
        logging.debug(
            "[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0005\x1b[0m created (%d:%s->"
            "%s=%s(%s, %s))",
            request_id,
            function_name,
            parent_name,
            object_id,
            params,
            token,
        )

        self.encoder = BitEncoder()
        self.request_id = request_id
        self.function_name = function_name
        self.parent_name = parent_name
        self.object_id = object_id
        self.params = params
        self.token = token

    def encode(self) -> Result[None, Error]:
        """Encode the interaction request into binary format."""
        Result.hide()

        self.encoder.add_data(self.request_id, 64)
        self.encoder.add_bytes(self.function_name.encode("utf-8"))
        self.encoder.add_data(0, 8)  # Null terminator
        self.encoder.add_bytes(self.parent_name.encode("utf-8"))
        self.encoder.add_data(0, 8)  # Null terminator

        if self.token is not None:
            self.encoder.add_bytes(self.token.encode("utf-8"))

        self.encoder.add_data(0, 8)  # Null terminator

        if self.object_id is not None:
            self.encoder.add_bytes(str(self.object_id).encode("utf-8"))

        self.encoder.add_data(0, 8)  # Null terminator

        if self.params is not None:
            self.encoder.add_bytes(json.dumps(self.params).encode("utf-8"))

        return Result.reveal()

    def get_encoder(self) -> BitEncoder[Lsb]:
        """Get the bit encoder containing the encoded request.

        Returns:
            BitEncoder configured for LSB encoding

        Example:
            >>> request = InteractionRequest(1, "click", "Button", None, None, None)
            >>> request.encode()
            >>> encoder = request.get_encoder()
        """
        return self.encoder

    def get_event(self) -> int:
        """Get the event identifier for interaction requests.

        Returns:
            0x0005: The event ID for interaction requests

        Example:
            >>> request = InteractionRequest(1, "click", "Button", None, None, None)
            >>> request.get_event()
            0x0005
        """
        return 0x0005
