"""
HTML content parser and decoder for SHDP protocol version 0x0001.
This module handles HTML tag structures and their attributes using MSB
    (Most Significant Bit) encoding.
"""

import logging
from dataclasses import dataclass
from typing import Literal, Union

from shdp.protocol.client.bits.utils import Operation

from shdp.utils.bitvec import Msb, ReversedR
from shdp.utils.result import Result
from ....errors import Error, ErrorKind
from ....managers.bits.decoder import BitDecoder
from ....managers.event import EventDecoder, EventEncoder, Frame
from ....managers.registry import EVENT_REGISTRY_MSB
from ...bits.utils import FyveImpl, OperatingCode, OperationCode


class HtmlContent:
    """Represents either text content or a child HTML tag.

    A variant type that can hold either plain text or a nested HTML tag.

    Example:
        >>> text = HtmlContent.Text("Hello")
        >>> div = HtmlTag("div")
        >>> child = HtmlContent.Child(div)
    """

    _content: Union[str, "HtmlTag"]
    _variant: Literal["Text", "Child"]

    def __init__(self, content: Union[str, "HtmlTag"]) -> None:
        """Initialize content with either text or an HTML tag.

        Args:
            content: Either a string for text content or an HtmlTag instance

        Raises:
            ValueError: If content is neither str nor HtmlTag
        """
        if isinstance(content, str):
            self._variant = "Text"
            self._content = content
        elif isinstance(content, HtmlTag):
            self._variant = "Child"
            self._content = content
        else:
            raise ValueError(f"Invalid content type: {type(content)}")

    @classmethod
    def Text(cls, text: str) -> "HtmlContent":  # pylint: disable=invalid-name
        """Create text content.

        Example:
            >>> content = HtmlContent.Text("Hello World")
            >>> content.get_text()
            'Hello World'
        """
        return cls(text)

    @classmethod
    def Child(cls, tag: "HtmlTag") -> "HtmlContent":  # pylint: disable=invalid-name
        """Create child tag content.

        Example:
            >>> div = HtmlTag("div")
            >>> content = HtmlContent.Child(div)
            >>> content.get_child().get_name()
            'div'
        """
        return cls(tag)

    def get_text(self) -> str:
        """Get the text content if this is a Text variant.

        Returns:
            The text content if this is a Text variant, empty string otherwise

        Example:
            >>> content = HtmlContent.Text("Hello")
            >>> content.get_text()
            'Hello'
            >>> content = HtmlContent.Child(HtmlTag("div"))
            >>> content.get_text()
            ''
        """
        if self._variant == "Text":
            return self._content if isinstance(self._content, str) else ""
        else:
            return ""

    def get_child(self) -> "HtmlTag":
        """Get the child tag if this is a Child variant.

        Returns:
            The child HtmlTag if this is a Child variant, empty tag otherwise

        Example:
            >>> div = HtmlTag("div")
            >>> content = HtmlContent.Child(div)
            >>> content.get_child().get_name()
            'div'
            >>> content = HtmlContent.Text("Hello")
            >>> content.get_child().get_name()
            ''
        """
        if self._variant == "Child":
            return self._content if isinstance(self._content, HtmlTag) else HtmlTag("")
        else:
            return HtmlTag("")

    def __str__(self) -> str:
        if self._variant == "Text":
            return self.get_text()
        else:
            return str(self.get_child())


@dataclass
class HtmlTag:
    """Represents an HTML tag with attributes and content.

    Example:
        >>> tag = HtmlTag("div")
        >>> tag.add_attribute("class", "container")
        >>> tag.add_data(HtmlContent.Text("Hello"))
    """

    def __init__(self, name: str) -> None:
        """Initialize an HTML tag with given name.

        Example:
            >>> tag = HtmlTag("span")
            >>> tag.get_name()
            'span'
        """
        self.name: str = name
        self.attributes: dict[str, str] = {}
        self.data: list[HtmlContent] = []

    def add_attribute(self, name: str, value: str) -> None:
        """Add or update an attribute to the HTML tag.

        Args:
            name: Attribute name
            value: Attribute value

        Example:
            >>> tag = HtmlTag("div")
            >>> tag.add_attribute("class", "container")
            >>> tag.add_attribute("id", "main")
        """
        self.attributes[name] = value

    def add_data(self, data: HtmlContent) -> None:
        """Add content (text or child tag) to this tag.

        Args:
            data: HtmlContent instance (either Text or Child)

        Example:
            >>> tag = HtmlTag("div")
            >>> tag.add_data(HtmlContent.Text("Hello"))
            >>> child = HtmlTag("span")
            >>> tag.add_data(HtmlContent.Child(child))
        """
        self.data.append(data)

    def get_name(self) -> str:
        """Get the name of this HTML tag.

        Returns:
            The tag name (e.g., "div", "span", etc.)

        Example:
            >>> tag = HtmlTag("div")
            >>> tag.get_name()
            'div'
        """
        return self.name

    def __str__(self) -> str:
        result: str = f"<{self.name}"

        for key, value in self.attributes.items():
            result += f' {key}="{value}"'

        result += ">"

        for data in self.data:
            result += str(data)

        result += f"</{self.name}>"

        return result


class HtmlFileResponse(EventDecoder[Msb]):
    """Decoder for HTML file responses in SHDP protocol.

    Parses binary data into an HTML structure with nested tags,
    attributes, and text content.

    Example:
        >>> decoder = BitDecoder(binary_data)
        >>> response = HtmlFileResponse(decoder)
        >>> response.decode(frame)
    """

    def __init__(self, decoder: BitDecoder[Msb]) -> None:
        logging.debug("[\x1b[38;5;187mSHDP\x1b[0m] \x1b[38;5;21m0x0001\x1b[0m received")

        self.decoder: BitDecoder[Msb] = decoder
        self.name: str = ""
        self.parent: HtmlTag = HtmlTag("")

    def _read_utf8_chain(self, length: int) -> str:
        """Read a UTF-8 encoded string of given length.

        Args:
            length: Number of bytes to read

        Returns:
            Decoded UTF-8 string
        """
        data: list[int] = []
        for _ in range(length):
            data.append(self.decoder.read_data(8).unwrap().to_byte_list()[0])

        logging.debug("data: %d :: %s", len(data), data)

        return bytes(data).decode("utf-8")

    def decode(self, frame: Frame[Msb]) -> Result[None, Error]:
        """Decode binary frame data into HTML structure.

        Processes operation codes to build HTML tag hierarchy:
        - START_OF_TAG: Begin new tag
        - START_OF_ATTRIBUTES: Process tag attributes
        - START_OF_DATA: Handle tag content
        - END_OF_DATA: Close current tag

        Args:
            frame: Binary frame containing HTML data

        Example:
            >>> decoder = BitDecoder(binary_data)
            >>> response = HtmlFileResponse(decoder)
            >>> response.decode(frame)
            >>> print(response.parent.get_name())  # Root tag name
        """
        data: list[int] = []
        temp_data: int = 0

        Result.hide()

        while True:
            temp_data = self.decoder.read_data(8).unwrap().to_byte_list()[0]

            if temp_data == 0:
                break

            data.append(temp_data)

        self.name = bytes(data).decode("utf-8")

        is_in_tag = False
        is_in_attributes: bool = False
        entered_in_attributes: bool = False
        entered_in_data: bool = False
        is_in_data: bool = False
        text: str = ""
        attribute_name: str = ""
        tag_name: str = ""
        tags_controlled: list[HtmlTag] = []

        tags_controlled.append(self.parent)

        while True:
            if self.decoder.position >= frame.data_size + 56:
                break

            op_code: Operation = FyveImpl.get_op(self.decoder).unwrap()

            if op_code.kind == OperatingCode.SYSTEM:
                if op_code.code == OperationCode.START_OF_TAG:
                    is_in_tag = True
                    is_in_attributes = False
                    is_in_data = False
                elif op_code.code == OperationCode.START_OF_ATTRIBUTES:
                    is_in_tag = False
                    is_in_attributes = True
                    is_in_data = False
                elif op_code.code == OperationCode.START_OF_DATA:
                    is_in_tag = False
                    is_in_attributes = False
                    is_in_data = True
                elif op_code.code == OperationCode.END_OF_DATA:
                    is_in_tag = False
                    is_in_attributes = False
                    is_in_data = False
                elif op_code.code == OperationCode.UTF8_CHAIN:
                    text_len = self.decoder.read_data(15).unwrap().to_int().unwrap()
                    text = self._read_utf8_chain(text_len)
                elif op_code.code == OperationCode.UNKNOWN:
                    return Result.Err(
                        Error.new(
                            ErrorKind.USER_DEFINED,
                            f"Unknown operation code: {op_code.code}::{op_code.kind}::{op_code.values}",
                        )
                    )
                else:
                    return Result.Err(
                        Error.new(
                            ErrorKind.USER_DEFINED,
                            f"Unknown operation code: {op_code.code}::{op_code.kind}::{op_code.values}",
                        )
                    )

                if is_in_tag:
                    text = ""

                if is_in_attributes and text != "":
                    tag: HtmlTag = tags_controlled[0]
                    tag.add_attribute(attribute_name, text)
                    attribute_name = ""
                    text = ""
                elif is_in_attributes and text == "" and not entered_in_attributes:
                    tag = HtmlTag(tag_name)
                    tag_name = ""
                    tags_controlled[0].data.append(HtmlContent.Child(tag))
                    tags_controlled.insert(0, tag)
                    entered_in_attributes = True

                if is_in_data and text != "":
                    tags_controlled[0].data.append(HtmlContent.Text(text))
                    entered_in_data = True

                if is_in_data and not entered_in_attributes and not entered_in_data:
                    tag = HtmlTag(tag_name)
                    tag_name = ""
                    tags_controlled.insert(0, tag)
                elif not is_in_data:
                    entered_in_data = False

                if is_in_data and entered_in_attributes:
                    entered_in_attributes = False

                if not is_in_tag and not is_in_attributes and not is_in_data:
                    tag_name = ""
                    attribute_name = ""
                    is_in_tag = True

                    if len(tags_controlled) >= 2:
                        last_tag: HtmlTag = tags_controlled[0]
                        tags_controlled[1].add_data(HtmlContent.Child(last_tag))

                    if len(tags_controlled) != 0:
                        tags_controlled.pop(0)

            if op_code.kind == OperatingCode.CHARACTER:
                char: str = op_code.get_char().unwrap()

                if is_in_tag:
                    tag_name += char

                if is_in_attributes:
                    attribute_name += char

        self.parent = tags_controlled[0]

        return Result.reveal()

    def get_responses(self) -> Result[list[EventEncoder[ReversedR]], Error]:
        """Get list of possible response events.

        Returns:
            Empty list as this decoder doesn't generate response events

        Example:
            >>> response = HtmlFileResponse(decoder)
            >>> response.get_responses()
            []
        """
        return Result.Ok([])


#
# REGISTRY
#

EVENT_REGISTRY_MSB.add_event((1, 0x0001), HtmlFileResponse)
