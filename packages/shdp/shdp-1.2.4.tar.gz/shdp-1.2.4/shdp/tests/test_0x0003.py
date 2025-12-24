"""Tests for the 0x0003 protocol message (ComponentNeedsResponse).

This test suite verifies the encoding and decoding of the ComponentNeedsResponse message,
which is used to transmit component requirements between server and client.
"""

import logging
import unittest

from shdp.protocol.client.versions.v1.r0x0003 import (
    ComponentNeedsResponse as ClientComponentNeedsResponse,
)
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.c0x0003 import ComponentNeedsResponse
from shdp.protocol.versions import Version


class Test0x0003(unittest.TestCase):
    def test_component_needs_response_basic(self):
        """Test encoding and decoding of basic ComponentNeedsResponse message.

        This test:
        1. Creates a ComponentNeedsResponse with just a component name
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies the decoded component name matches the original
        """
        component_name = "test-component"

        # Encode component needs response
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(ComponentNeedsResponse(component_name, None, []))

        # Decode response
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode component data
        decoded_data = ClientComponentNeedsResponse(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.component_name, component_name)
            self.assertEqual(decoded_data.title, "")
            self.assertEqual(decoded_data.files, [])
        else:
            self.fail(decoded_data_result.unwrap_err())

    def test_component_needs_response_full(self):
        """Test encoding and decoding of ComponentNeedsResponse with all fields.

        This test:
        1. Creates a ComponentNeedsResponse with name, title and required files
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies all decoded fields match the original
        """
        component_name = "test-component"
        title = "Test Component"
        files = ["style.css", "script.js"]

        # Encode component needs response
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(ComponentNeedsResponse(component_name, title, files))

        logging.debug(f"Encoded frame: {frame.unwrap().to_hex()}")

        # Decode response
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode component data
        decoded_data = ClientComponentNeedsResponse(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.component_name, component_name)
            self.assertEqual(decoded_data.title, title)
            self.assertEqual(decoded_data.files, files)
        else:
            self.fail(decoded_data_result.unwrap_err())


if __name__ == "__main__":
    unittest.main()
