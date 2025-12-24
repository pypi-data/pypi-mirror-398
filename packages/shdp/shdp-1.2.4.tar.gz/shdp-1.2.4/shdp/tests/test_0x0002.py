"""Tests for the 0x0002 protocol message (ErrorResponse).

This test suite verifies the encoding and decoding of the ErrorResponse message,
which is used to transmit errors between server and client.
"""

import logging
import unittest

from shdp.protocol.client.versions.v1.r0x0002 import ErrorResponse as ClientErrorResponse
from shdp.protocol.errors import Error, ErrorKind
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.c0x0002 import ErrorResponse
from shdp.protocol.versions import Version


class Test0x0002(unittest.TestCase):
    def test_error_response(self):
        """Test encoding and decoding of ErrorResponse message.

        This test:
        1. Creates an ErrorResponse with an error code and message
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies the decoded error code and message match the original
        """
        # Create test error
        test_error = Error(404, ErrorKind.NOT_FOUND, "Resource not found")

        # Encode error response
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(ErrorResponse(test_error))

        logging.debug(f"Encoded frame: {frame.unwrap().to_hex()}")

        # Decode response
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode error data
        decoded_data = ClientErrorResponse(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.code, test_error.code)
            self.assertEqual(decoded_data.message, test_error.message)
        else:
            self.fail(decoded_data_result.unwrap_err())


if __name__ == "__main__":
    unittest.main()
