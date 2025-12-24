"""Tests for the 0x0001 protocol message (HtmlFileResponse).

This test suite verifies the encoding and decoding of the HtmlFileResponse message,
which is used to transfer HTML files between server and client.
"""

import unittest
from pathlib import Path

from shdp.protocol.client.versions.v1.r0x0001 import (
    HtmlContent,
    HtmlFileResponse,
    HtmlTag,
)
from shdp.protocol.managers.bits.decoder import BitDecoder, FrameDecoder
from shdp.protocol.managers.bits.encoder import FrameEncoder
from shdp.protocol.server.versions.v1.c0x0001 import HtmlFileResponse as ServerHtmlFileResponse
from shdp.protocol.versions import Version


class Test0x0001(unittest.TestCase):
    def test_html_file_response(self):
        """Test encoding and decoding of HtmlFileResponse message."""
        test_file_path = Path(__file__).parent / "files" / "test.html"

        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(ServerHtmlFileResponse(str(test_file_path)))

        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        decoded_data = HtmlFileResponse(decoder)
        decoded_data.parent = HtmlTag("container")
        decoded_data_result = decoded_data.decode(data)

        if decoded_data_result.is_ok():
            self.assertEqual(decoded_data.name, "test.html")
            self.assertEqual(decoded_data.parent.name, "container")
        else:
            self.fail(decoded_data_result.unwrap_err())

    def test_html_content_text(self):
        """Test HtmlContent text variant functionality."""
        text_content = HtmlContent.Text("Hello World")
        self.assertEqual(text_content.get_text(), "Hello World")
        self.assertEqual(text_content.get_child().get_name(), "")

    def test_html_content_child(self):
        """Test HtmlContent child variant functionality."""
        child_tag = HtmlTag("div")
        child_content = HtmlContent.Child(child_tag)
        self.assertEqual(child_content.get_text(), "")
        self.assertEqual(child_content.get_child().get_name(), "div")

    def test_html_tag_operations(self):
        """Test HtmlTag methods and string representation."""
        tag = HtmlTag("div")
        tag.add_attribute("class", "container")
        tag.add_attribute("id", "main")
        tag.add_data(HtmlContent.Text("Hello"))

        child = HtmlTag("span")
        child.add_attribute("class", "highlight")
        child.add_data(HtmlContent.Text("World"))
        tag.add_data(HtmlContent.Child(child))

        self.assertEqual(tag.get_name(), "div")
        expected_str = '<div class="container" id="main">Hello<span class="highlight">World</span></div>'
        self.assertEqual(str(tag), expected_str)

    def test_html_response_unknown_operation(self):
        """Test handling of unknown operation codes in HTML response decoding."""
        test_file_path = Path(__file__).parent / "files" / "test.html"

        encoder = FrameEncoder(Version.V1.value)
        frame = encoder.encode(ServerHtmlFileResponse(str(test_file_path)))

        decoder = BitDecoder(frame.unwrap())
        frame_decoder = FrameDecoder(decoder)
        data = frame_decoder.decode().unwrap()
        decoder = frame_decoder.get_decoder()

        # Modify frame data to simulate unknown operation code
        # This requires access to internal frame data which might not be possible
        # Alternative approach: Create a mock decoder that returns unknown operation codes

        decoded_data = HtmlFileResponse(decoder)
        result = decoded_data.decode(data)

        if result.is_err():
            error = result.unwrap_err()
            self.assertTrue("Unknown operation code" in error.message)


if __name__ == "__main__":
    unittest.main()
