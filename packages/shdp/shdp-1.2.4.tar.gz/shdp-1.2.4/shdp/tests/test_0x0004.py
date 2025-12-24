"""Tests for the 0x0004 protocol message (FullFyveResponse).

This test suite verifies the encoding and decoding of the FullFyveResponse message,
which is used to transmit Fyve files with their contents between server and client.
"""

import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from shdp.protocol.client.versions.v1.r0x0004 import FullFyveResponse as ClientFullFyveResponse
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.c0x0004 import FullFyveResponse
from shdp.protocol.versions import Version


class Test0x0004(unittest.TestCase):
    def test_fyve_file_response_empty(self):
        """Test encoding and decoding of FullFyveResponse with empty file.

        This test:
        1. Creates a temporary empty Fyve file
        2. Creates a FullFyveResponse with the file
        3. Encodes it using LSB frame encoding
        4. Decodes it using MSB frame decoding
        5. Verifies the decoded filename and empty content
        """
        with NamedTemporaryFile(suffix=".fyve", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Encode fyve response
            encoder = FrameEncoder(Version.V1.value)
            frame = encoder.encode(FullFyveResponse(str(temp_path)))

            # Decode response
            decoder = BitDecoder(frame.unwrap())
            frame_decoder = FrameDecoder(decoder)
            data = frame_decoder.decode().unwrap()
            decoder = frame_decoder.get_decoder()

            # Decode fyve data
            decoded_data = ClientFullFyveResponse(decoder)
            decoded_data_result = decoded_data.decode(data)

            if decoded_data_result.is_ok():
                self.assertEqual(decoded_data.filename, temp_path.name)
                self.assertEqual(decoded_data.content, "")
            else:
                self.fail(decoded_data_result.unwrap_err())

        finally:
            temp_path.unlink()

    def test_fyve_file_response_with_content(self):
        """Test encoding and decoding of FullFyveResponse with file content.

        This test:
        1. Creates a temporary Fyve file with test content
        2. Creates a FullFyveResponse with the file
        3. Encodes it using LSB frame encoding
        4. Decodes it using MSB frame decoding
        5. Verifies the decoded filename and content match the original
        """
        test_content = "component Button {style: primary; text: 'Click me';}"

        with NamedTemporaryFile(suffix=".fyve", mode="w", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = Path(temp_file.name)

        try:
            # Encode fyve response
            encoder = FrameEncoder(Version.V1.value)
            frame = encoder.encode(FullFyveResponse(str(temp_path)))

            # Decode response
            decoder = BitDecoder(frame.unwrap())
            frame_decoder = FrameDecoder(decoder)
            data = frame_decoder.decode().unwrap()
            decoder = frame_decoder.get_decoder()

            # Decode fyve data
            decoded_data = ClientFullFyveResponse(decoder)
            decoded_data_result = decoded_data.decode(data)

            if decoded_data_result.is_ok():
                self.assertEqual(decoded_data.filename, temp_path.name)
                self.assertEqual(decoded_data.content, test_content)
            else:
                self.fail(decoded_data_result.unwrap_err())

        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
