"""Full Fyve file response encoder for SHDP protocol version 1 (event 0x0004).

This module provides encoding functionality for Fyve files in the SHDP protocol.
It implements the FullFyveResponse class which handles the complete encoding
process for Fyve file transmission, including:

    - File name extraction and encoding (UTF-8)
    - Content reading and whitespace normalization
    - Character encoding using CHARS mapping for optimization
    - Null byte separation between filename and content

The encoder uses LSB-first bit ordering and processes Fyve files by:
    1. Extracting the filename from the file path (cross-platform)
    2. Encoding the filename as UTF-8 bytes
    3. Adding a null byte separator
    4. Reading the file content and removing whitespace (tabs, newlines, returns)
    5. Encoding each character using the CHARS mapping table

Fyve files are component definition files that use optimized character encoding
for efficient transmission over the protocol.

Example usage:

    >>> from shdp.protocol.server.versions.v1.c0x0004 import FullFyveResponse
    >>> from shdp.utils.result import Result
    >>>
    >>> # Create and encode a Fyve file response
    >>> response = FullFyveResponse("components/button.fyve")
    >>> result = response.encode()
    >>> if result.is_ok():
    ...     encoder = response.get_encoder()
    ...     event_id = response.get_event()  # Returns 0x0004
"""

import logging
import os
import re

from shdp.utils.bitvec import Lsb
from shdp.utils.result import Result
from ....errors import Error
from ....managers.bits.encoder import BitEncoder
from ....managers.event import EventEncoder
from ...bits.utils import CHARS


class FullFyveResponse(EventEncoder[Lsb]):
    """Fyve file response encoder for SHDP protocol.

    Handles encoding of Fyve files, including:
    - File name encoding
    - Content encoding using CHARS mapping
    - Null byte separation

    Attributes:
        encoder (BitEncoder): Bit encoder for the response
        path (str): Path to the Fyve file

    Example:
        >>> response = FullFyveResponse("components/button.fyve")
        >>> response.encode()
        >>> encoder = response.get_encoder()
    """

    def __init__(self, path: str) -> None:
        """Initialize a full Fyve file response.

        Args:
            path: Path to the Fyve file to be sent

        Example:
            >>> response = FullFyveResponse("components/button.fyve")
        """
        logging.debug(
            "[\x1b[38;5;227mSHDP\x1b[0m] \x1b[38;5;192m0x0004\x1b[0m created (%s)",
            path,
        )

        self.encoder = BitEncoder[Lsb]()
        self.path: str = path

    def encode(self) -> Result[None, Error]:
        """Encode the Fyve file content into binary format.

        Reads the file content and encodes both the filename and content
        using the CHARS encoding table.

        Returns:
            Result[None, Error]: Ok(None) if encoding succeeds,
                               Err(error) if any operation fails

        Example:
            >>> response = FullFyveResponse("button.fyve")
            >>> result = response.encode()
            >>> if result.is_ok():
            ...     print("File encoded successfully")
        """
        file_name: str = (
            "/".join(self.path.split("/")[-2:])
            if os.name == "posix"
            else "\\".join(self.path.split("\\")[-2:])
        )

        Result.hide()

        self.encoder.add_bytes(file_name.encode("utf-8"))
        self.encoder.add_data(0, 8)

        with open(self.path, "rb") as file:
            content: str = file.read().decode("utf-8")
            content = re.sub(r"[\t\n\r]", "", content)

        for char in content:
            self.encoder.add_vec(CHARS[char])

        return Result.reveal()

    def get_encoder(self) -> BitEncoder[Lsb]:
        """Get the bit encoder containing the encoded file data.

        Returns:
            BitEncoder[Lsb]: The encoder containing the encoded filename and content

        Example:
            >>> response = FullFyveResponse("button.fyve")
            >>> response.encode()
            >>> encoder = response.get_encoder()
        """
        return self.encoder

    def get_event(self) -> int:
        """Get the event identifier for full Fyve file responses.

        Returns:
            int: The event ID (0x0004)

        Example:
            >>> response = FullFyveResponse("button.fyve")
            >>> response.get_event()
            0x0004
        """
        return 0x0004
