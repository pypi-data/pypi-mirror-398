"""Tests for full interaction request/response flow.

This test suite verifies the complete flow of:
1. Client sending an interaction request
2. Server processing the request
3. Server sending back the response
"""

import unittest

from shdp.protocol.client.versions.v1.c0x0005 import InteractionRequest
from shdp.protocol.client.versions.v1.r0x0006 import (
    InteractionResponse as ClientInteractionResponse,
)
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.c0x0006 import InteractionResponse
from shdp.protocol.server.versions.v1.r0x0005 import InteractionRequest as ServerInteractionRequest
from shdp.protocol.versions import Version


class TestInteractionFullTrack(unittest.TestCase):
    def test_basic_interaction_flow(self):
        """Test basic interaction request/response flow.

        This test simulates:
        1. Client sending a simple function call request
        2. Server processing the request
        3. Server sending back a success response
        """
        # Step 1: Client sends interaction request
        request_id = 12345
        function_name = "getValue"
        parent_name = "Counter"
        object_id = 42
        params = {"type": "current"}

        encoder = FrameEncoder(Version.V1.value)
        request_frame = encoder.encode(
            InteractionRequest(
                request_id=request_id,
                function_name=function_name,
                parent_name=parent_name,
                object_id=object_id,
                params=params,
                token=None,
            )
        )

        # Server receives and decodes request
        decoder = BitDecoder(request_frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        request_data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        server_request = ServerInteractionRequest(decoder)
        result = server_request.decode(request_data)
        self.assertTrue(result.is_ok())
        self.assertEqual(server_request.request_id, request_id)
        self.assertEqual(server_request.function_name, function_name)
        self.assertEqual(server_request.parent_name, parent_name)
        self.assertEqual(server_request.object_id, object_id)
        self.assertEqual(server_request.params, params)
        self.assertIsNone(server_request.token)

        # Step 2: Server sends response
        response_data = {
            "status": "success",
            "value": 100,
        }

        encoder = FrameEncoder(Version.V1.value)
        response_frame = encoder.encode(InteractionResponse(request_id, response_data))

        # Client receives and decodes response
        decoder = BitDecoder(response_frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        response_data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        client_response = ClientInteractionResponse(decoder)
        result = client_response.decode(response_data)
        self.assertTrue(result.is_ok())
        self.assertEqual(client_response.request_id, request_id)
        self.assertEqual(
            client_response.response,
            {"status": "success", "value": 100},
        )

    def test_authenticated_interaction_flow(self):
        """Test authenticated interaction request/response flow.

        This test simulates:
        1. Client sending an authenticated function call request
        2. Server processing the request with auth token
        3. Server sending back a success response
        """
        # Step 1: Client sends authenticated interaction request
        request_id = 67890
        function_name = "updateProfile"
        parent_name = "UserProfile"
        params = {"name": "John Doe", "email": "john@example.com"}
        token = "auth_token_123"

        encoder = FrameEncoder(Version.V1.value)
        request_frame = encoder.encode(
            InteractionRequest(
                request_id=request_id,
                function_name=function_name,
                parent_name=parent_name,
                object_id=None,
                params=params,
                token=token,
            )
        )

        # Server receives and decodes request
        decoder = BitDecoder(request_frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        request_data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        server_request = ServerInteractionRequest(decoder)
        result = server_request.decode(request_data)
        self.assertTrue(result.is_ok())
        self.assertEqual(server_request.request_id, request_id)
        self.assertEqual(server_request.function_name, function_name)
        self.assertEqual(server_request.parent_name, parent_name)
        self.assertIsNone(server_request.object_id)
        self.assertEqual(server_request.params, params)
        self.assertEqual(server_request.token, token)

        # Step 2: Server sends response
        response_data = {
            "status": "success",
            "message": "Profile updated successfully",
            "user": {"id": 1, "name": "John Doe", "email": "john@example.com"},
        }

        encoder = FrameEncoder(Version.V1.value)
        response_frame = encoder.encode(InteractionResponse(request_id, response_data))

        # Client receives and decodes response
        decoder = BitDecoder(response_frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        response_data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        client_response = ClientInteractionResponse(decoder)
        result = client_response.decode(response_data)
        self.assertTrue(result.is_ok())
        self.assertEqual(client_response.request_id, request_id)
        self.assertEqual(
            client_response.response,
            {
                "status": "success",
                "message": "Profile updated successfully",
                "user": {"id": 1, "name": "John Doe", "email": "john@example.com"},
            },
        )


if __name__ == "__main__":
    unittest.main()
