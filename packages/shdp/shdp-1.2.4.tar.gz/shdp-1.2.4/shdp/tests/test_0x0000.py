"""Tests for the 0x0000 protocol message (ComponentNeedsRequest).

This test suite verifies the encoding and decoding of the ComponentNeedsRequest message,
which is used to request specific components from the server.
"""

import logging
import unittest

from shdp.protocol.client.versions.v1.c0x0000 import ComponentNeedsRequest
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.r0x0000 import (
    ComponentNeedsRequest as ServerComponentNeedsRequest,
)
from shdp.protocol.versions import Version


class Test0x0000(unittest.TestCase):
    def test_component_needs_request(self):
        """Test encoding and decoding of ComponentNeedsRequest message.

        This test:
        1. Creates a ComponentNeedsRequest with a test component name
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies the decoded component name matches the original
        """
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(ComponentNeedsRequest("test"))

        logging.debug(f"Encoded frame: {frame.unwrap().to_hex()}")

        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        decoded_data = ServerComponentNeedsRequest(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.requested_component_name, "test")
        else:
            self.fail(decoded_data_result.unwrap_err())


if __name__ == "__main__":
    unittest.main()
