"""Tests for full component request/response flow.

This test suite verifies the complete flow of:
1. Client requesting a component
2. Server responding with component needs
3. Server sending required files (HTML and Fyve)
"""

import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from shdp.protocol.client.versions.v1.c0x0000 import ComponentNeedsRequest
from shdp.protocol.client.versions.v1.r0x0001 import HtmlFileResponse as ClientHtmlResponse
from shdp.protocol.client.versions.v1.r0x0003 import (
    ComponentNeedsResponse as ClientComponentResponse,
)
from shdp.protocol.client.versions.v1.r0x0004 import FullFyveResponse as ClientFyveResponse
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.c0x0001 import HtmlFileResponse
from shdp.protocol.server.versions.v1.c0x0003 import ComponentNeedsResponse
from shdp.protocol.server.versions.v1.c0x0004 import FullFyveResponse
from shdp.protocol.server.versions.v1.r0x0000 import ComponentNeedsRequest as ServerComponentRequest
from shdp.protocol.versions import Version


class TestComponentFullTrack(unittest.TestCase):
    def test_component_request_flow(self):
        """Test complete component request and response flow.

        This test simulates:
        1. Client requesting a component
        2. Server decoding request and responding with needed files
        3. Server sending HTML template
        4. Server sending Fyve component file
        """
        # Create temporary test files
        html_content = "<div>Test Component</div>"
        fyve_content = "component TestComponent { style: primary }"

        with NamedTemporaryFile(suffix=".html", mode="w", delete=False) as html_file:
            html_file.write(html_content)
            html_path = Path(html_file.name)

        with NamedTemporaryFile(suffix=".fyve", mode="w", delete=False) as fyve_file:
            fyve_file.write(fyve_content)
            fyve_path = Path(fyve_file.name)

        try:
            # Step 1: Client sends component request
            encoder = FrameEncoder(Version.V1.value)
            request_frame = encoder.encode(ComponentNeedsRequest("TestComponent"))

            # Server receives and decodes request
            decoder = BitDecoder(request_frame.unwrap())
            frame_decoder = FrameDecoder(decoder)
            request_data = frame_decoder.decode().unwrap()
            decoder = frame_decoder.get_decoder()

            server_request = ServerComponentRequest(decoder)
            result = server_request.decode(request_data)
            self.assertTrue(result.is_ok())
            self.assertEqual(server_request.requested_component_name, "TestComponent")

            # Step 2: Server sends component needs response
            encoder = FrameEncoder(Version.V1.value)
            files = [html_path.name, fyve_path.name]
            needs_frame = encoder.encode(
                ComponentNeedsResponse("TestComponent", "Test Component", files)
            )

            # Client receives component needs
            decoder = BitDecoder(needs_frame.unwrap())
            frame_decoder = FrameDecoder(decoder)
            needs_data = frame_decoder.decode().unwrap()
            decoder = frame_decoder.get_decoder()

            client_needs = ClientComponentResponse(decoder)
            result = client_needs.decode(needs_data)
            self.assertTrue(result.is_ok())
            self.assertEqual(client_needs.component_name, "TestComponent")
            self.assertEqual(client_needs.title, "Test Component")
            self.assertEqual(client_needs.files, files)

            # Step 3: Server sends HTML file
            encoder = FrameEncoder(Version.V1.value)
            html_frame = encoder.encode(HtmlFileResponse(str(html_path)))

            # Client receives HTML file
            decoder = BitDecoder(html_frame.unwrap())
            frame_decoder = FrameDecoder(decoder)
            html_data = frame_decoder.decode().unwrap()
            decoder = frame_decoder.get_decoder()

            client_html = ClientHtmlResponse(decoder)
            result = client_html.decode(html_data)
            self.assertTrue(result.is_ok())
            self.assertEqual(client_html.name, html_path.name)

            # Step 4: Server sends Fyve file
            encoder = FrameEncoder(Version.V1.value)
            fyve_frame = encoder.encode(FullFyveResponse(str(fyve_path)))

            # Client receives Fyve file
            decoder = BitDecoder(fyve_frame.unwrap())
            frame_decoder = FrameDecoder(decoder)
            fyve_data = frame_decoder.decode().unwrap()
            decoder = frame_decoder.get_decoder()

            client_fyve = ClientFyveResponse(decoder)
            result = client_fyve.decode(fyve_data)
            self.assertTrue(result.is_ok())
            self.assertEqual(client_fyve.filename, fyve_path.name)
            self.assertEqual(client_fyve.content, fyve_content)

        finally:
            # Clean up temporary files
            html_path.unlink()
            fyve_path.unlink()


if __name__ == "__main__":
    unittest.main()
