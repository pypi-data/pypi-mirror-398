"""Tests for the 0x0005 protocol message (InteractionRequest).

This test suite verifies the encoding and decoding of the InteractionRequest message,
which is used to handle client-side interaction requests and server-side responses.
"""

import unittest

from shdp.protocol.client.versions.v1.c0x0005 import InteractionRequest
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.r0x0005 import InteractionRequest as ServerInteractionRequest
from shdp.protocol.versions import Version


class Test0x0005(unittest.TestCase):
    def test_basic_interaction_request(self):
        """Test encoding and decoding of basic InteractionRequest.

        This test:
        1. Creates an InteractionRequest with minimal parameters
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies all decoded fields match the original
        """
        request_id = 12345
        function_name = "click"
        parent_name = "Button"

        # Encode request
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(
            InteractionRequest(
                request_id=request_id,
                function_name=function_name,
                parent_name=parent_name,
                object_id=None,
                params=None,
                token=None,
            )
        )

        # Decode request
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode interaction data
        decoded_data = ServerInteractionRequest(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.request_id, request_id)
            self.assertEqual(decoded_data.function_name, function_name)
            self.assertEqual(decoded_data.parent_name, parent_name)
            self.assertIsNone(decoded_data.object_id)
            self.assertIsNone(decoded_data.params)
            self.assertIsNone(decoded_data.token)
        else:
            self.fail(decoded_data_result.unwrap_err())

    def test_full_interaction_request(self):
        """Test encoding and decoding of InteractionRequest with all fields.

        This test:
        1. Creates an InteractionRequest with all optional parameters
        2. Encodes it using LSB frame encoding
        3. Decodes it using MSB frame decoding
        4. Verifies all decoded fields match the original
        """
        request_id = 67890
        function_name = "setValue"
        parent_name = "Input"
        object_id = 42
        params = {"value": "Hello, World!", "type": "text"}
        token = "auth_token_123"

        # Encode request
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(
            InteractionRequest(
                request_id=request_id,
                function_name=function_name,
                parent_name=parent_name,
                object_id=object_id,
                params=params,
                token=token,
            )
        )

        # Decode request
        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Decode interaction data
        decoded_data = ServerInteractionRequest(decoder)
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.request_id, request_id)
            self.assertEqual(decoded_data.function_name, function_name)
            self.assertEqual(decoded_data.parent_name, parent_name)
            self.assertEqual(decoded_data.token, token)
            self.assertEqual(decoded_data.object_id, object_id)
            self.assertEqual(decoded_data.params, params)
        else:
            self.fail(decoded_data_result.unwrap_err())

    def test_invalid_interaction_request(self):
        """Test handling of invalid InteractionRequest.

        This test verifies that appropriate errors are returned for:
        1. Empty parent name
        2. Empty function name
        """
        # Test empty parent name
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(
            InteractionRequest(
                request_id=1,
                function_name="test",
                parent_name="",  # Invalid empty parent name
                object_id=None,
                params=None,
                token=None,
            )
        )

        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        decoded_data = ServerInteractionRequest(decoder)
        result = decoded_data.decode(data)
        self.assertTrue(result.is_err())
        self.assertEqual(result.unwrap_err().message, "Parent name is empty")

        # Test empty function name
        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(
            InteractionRequest(
                request_id=1,
                function_name="",  # Invalid empty function name
                parent_name="test",
                object_id=None,
                params=None,
                token=None,
            )
        )

        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        decoded_data = ServerInteractionRequest(decoder)
        result = decoded_data.decode(data)
        self.assertTrue(result.is_err())
        self.assertEqual(result.unwrap_err().message, "Function name is empty")


if __name__ == "__main__":
    unittest.main()
