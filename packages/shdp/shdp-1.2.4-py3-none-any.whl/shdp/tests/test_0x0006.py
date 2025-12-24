"""Tests for the 0x0006 protocol message (InteractionResponse).

This test suite verifies the encoding and decoding of the InteractionResponse message,
which is used to handle server responses to interaction requests.
"""

import unittest

from shdp.protocol.client.versions.v1.r0x0006 import (
    InteractionResponse as ClientInteractionResponse,
)
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.c0x0006 import InteractionResponse
from shdp.protocol.versions import Version


class Test0x0006(unittest.TestCase):
    def test_basic_interaction_response(self):
        """Test encoding and decoding of basic InteractionResponse.

        This test:
        1. Creates an InteractionResponse with just a request ID
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies the decoded request ID matches the original
        """
        request_id = 12345

        # Encode response
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(InteractionResponse(request_id, None))

        # Decode response
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode interaction data
        decoded_data = ClientInteractionResponse(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.request_id, request_id)
            self.assertIsNone(decoded_data.response)
        else:
            self.fail(decoded_data_result.unwrap_err())

    def test_dict_interaction_response(self):
        """Test encoding and decoding of InteractionResponse with dict data.

        This test:
        1. Creates an InteractionResponse with a request ID and dict response
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies all decoded fields match the original
        """
        request_id = 67890
        response_data = {
            "status": "success",
            "value": 42,
            "message": "Operation completed",
        }

        # Encode response
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(InteractionResponse(request_id, response_data))

        # Decode response
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode interaction data
        decoded_data = ClientInteractionResponse(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.request_id, request_id)
            self.assertEqual(decoded_data.response, response_data)
        else:
            self.fail(decoded_data_result.unwrap_err())

    def test_list_interaction_response(self):
        """Test encoding and decoding of InteractionResponse with list data.

        This test:
        1. Creates an InteractionResponse with a request ID and list response
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies all decoded fields match the original
        """
        request_id = 11111
        response_data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"},
        ]

        # Encode response
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(InteractionResponse(request_id, response_data))

        # Decode response
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode interaction data
        decoded_data = ClientInteractionResponse(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.request_id, request_id)
            self.assertEqual(decoded_data.response, response_data)
        else:
            self.fail(decoded_data_result.unwrap_err())


if __name__ == "__main__":
    unittest.main()
