"""Component needs response encoder for SHDP protocol version 1 (event 0x0003).

This module provides encoding functionality for component requirement responses
in the SHDP protocol. It implements the ComponentNeedsResponse class which
handles the encoding of component dependency information, including:

    - Component name (required identifier)
    - Optional title (display name for the component)
    - List of required files (dependencies like CSS, JS, etc.)

The encoder uses LSB-first bit ordering and processes component data by:
    1. Encoding the component name as UTF-8 bytes
    2. Optionally encoding the title (if provided) with a flag byte
    3. Encoding each required file path with a separator byte

This response type is used to communicate component dependencies from the
server to the client, allowing the client to request necessary resources
before rendering the component.

Example usage:

    >>> from shdp.protocol.server.versions.v1.c0x0003 import (
    ...     ComponentNeedsResponse
    ... )
    >>> from shdp.utils.result import Result
    >>>
    >>> # Create a component needs response
    >>> files = ["style.css", "script.js", "data.json"]
    >>> response = ComponentNeedsResponse(
    ...     "MyComponent", "My Component Title", files
    ... )
    >>> result = response.encode()
    >>> if result.is_ok():
    ...     encoder = response.get_encoder()
    ...     event_id = response.get_event()  # Returns 0x0003
"""

import logging

from shdp.lib import Result
from shdp.utils.bitvec import Lsb
from ....errors import Error
from ....managers.bits.encoder import BitEncoder
from ....managers.event import EventEncoder


class ComponentNeedsResponse(EventEncoder[Lsb]):
    """Component needs response encoder for SHDP protocol.

    Handles encoding of component requirements, including:
    - Component name
    - Optional title
    - List of required files

    Attributes:
        encoder (BitEncoder): Bit encoder for the response
        component_name (str): Name of the component
        title (str | None): Optional component title
        files (list[str]): List of required file paths

    Example:
        >>> files = ["style.css", "script.js"]
        >>> response = ComponentNeedsResponse("MyComponent", "My Title", files)
        >>> response.encode()
    """

    def __init__(self, component_name: str, title: str | None, files: list[str]):
        """Initialize component needs response.

        Args:
            component_name: Name of the component
            title: Optional title for the component
            files: List of required file paths
        """
        logging.debug(
            "[\x1b[38;5;227mSHDP\x1b[0m] \x1b[38;5;192m0x0003\x1b[0m created (%s)",
            component_name,
        )

        self.encoder = BitEncoder[Lsb]()
        self.component_name = component_name
        self.title = "" if title is None else title
        self.files = files

    def encode(self) -> Result[None, Error]:
        Result.hide()

        self.encoder.add_bytes(self.component_name.encode("utf-8"))

        if self.title is not None:
            self.encoder.add_data(1, 8)
            self.encoder.add_bytes(self.title.encode("utf-8"))

        if len(self.files) > 0:
            for file in self.files:
                self.encoder.add_data(0, 8)
                self.encoder.add_bytes(file.encode("utf-8"))

        return Result.reveal()

    def get_encoder(self) -> BitEncoder[Lsb]:
        return self.encoder

    def get_event(self) -> int:
        return 0x0003
