"""Character ordering and encoding metadata module for protocol optimization.

This module provides utilities for analyzing character frequency in text files
and generating optimal encoding metadata for character compression. It uses
frequency analysis to assign shorter bit encodings to more common characters,
improving protocol efficiency.

The module implements a character ordering system that:
    - Analyzes character frequency in text files
    - Generates bit encoding metadata based on frequency
    - Handles forbidden characters and non-usable positions
    - Creates variable-length encodings optimized for common characters

Example usage:

    >>> from shdp.protocol.managers.ordering import Ordering
    >>> from collections import Counter
    >>>
    >>> ordering = Ordering()
    >>> counter = ordering.read("sample.txt")
    >>> char_order = ordering.get_char_order(counter)
    >>> # char_order contains optimized encoding metadata
"""

from collections import Counter
from dataclasses import dataclass
from typing import Final, Literal


ORDERING_NON_USABLE_CHARS = ["\r"]
MIN_BIT_ENCODING_SIZE: Final[Literal[5]] = 5
NON_USABLE_POSITIONS: Final[list[int]] = [0, 31]


@dataclass
class CharEncodingMetadata:
    """Metadata for character encoding in the protocol.

    This dataclass stores the encoding information for a single character,
    including the number of bits required and the encoded value.

    Attributes:
        bit_encoding_size: Number of bits required to encode this character
        bit_encoding_value: The binary value representing this character

    Example:
        >>> metadata = CharEncodingMetadata(bit_encoding_size=5, bit_encoding_value=1)
        >>> metadata.bit_encoding_size
        5
        >>> metadata.bit_encoding_value
        1
    """

    bit_encoding_size: int
    bit_encoding_value: int


class Ordering:
    """Character ordering analyzer for protocol optimization.

    This class analyzes character frequency in text files and generates
    optimal encoding metadata. It uses frequency analysis to assign shorter
    bit encodings to more common characters, improving protocol efficiency.

    The ordering algorithm:
        1. Reads and counts character frequency from files
        2. Sorts characters by frequency (most common first)
        3. Assigns variable-length bit encodings based on frequency
        4. Handles non-usable positions by increasing encoding size

    Example:
        >>> ordering = Ordering()
        >>> counter = ordering.read("data.txt")
        >>> char_order = ordering.get_char_order(counter)
        >>> # Most common characters have shorter encodings
    """

    def read(self, path: str, forbidden_chars: list[str] | None = None) -> Counter:
        """Read a file and count character frequency.

        Reads the file in chunks (1MB at a time) to handle large files
        efficiently. Characters are sanitized before counting to remove
        forbidden characters.

        Args:
            path: Path to the file to analyze
            forbidden_chars: Optional list of characters to exclude from
                counting. If None, uses ORDERING_NON_USABLE_CHARS.

        Returns:
            Counter[str]: A Counter object mapping characters to their
                frequency counts

        Example:
            >>> ordering = Ordering()
            >>> counter = ordering.read("sample.txt")
            >>> counter.most_common(5)  # Get 5 most common characters
        """
        counter = Counter[str]()
        with open(path, "r", encoding="utf-8") as f:
            for c in iter(lambda: f.read(1024 * 1024), ""):
                c = Ordering.sanitize(c, forbidden_chars)
                counter.update(c)
        return counter

    def sanitize(self, s: str, forbidden_chars: list[str] | None = None) -> str:
        """Remove forbidden characters from a string.

        Filters out characters that should not be used in the encoding
        scheme, such as carriage returns or other control characters.

        Args:
            s: The string to sanitize
            forbidden_chars: Optional list of characters to remove.
                If None, uses ORDERING_NON_USABLE_CHARS.

        Returns:
            str: The sanitized string with forbidden characters removed

        Example:
            >>> ordering = Ordering()
            >>> ordering.sanitize("hello\\rworld")
            'helloworld'
        """
        forbidden_chars = forbidden_chars or ORDERING_NON_USABLE_CHARS
        return "".join(c for c in s if c not in forbidden_chars)

    def get_char_order(self, counter: Counter[str]) -> dict[str, CharEncodingMetadata]:
        """Generate character encoding metadata based on frequency.

        Creates an optimized encoding scheme where more frequent characters
        receive shorter bit encodings. The algorithm:
            - Starts with MIN_BIT_ENCODING_SIZE bits
            - Skips non-usable positions (0, 31)
            - Increases encoding size when position limit is reached
            - Assigns binary values based on character frequency rank

        Args:
            counter: Counter object containing character frequency data,
                typically from the read() method

        Returns:
            dict[str, CharEncodingMetadata]: Dictionary mapping characters
                to their encoding metadata. Characters are ordered by
                frequency (most common first).

        Example:
            >>> ordering = Ordering()
            >>> counter = Counter("hello world")
            >>> char_order = ordering.get_char_order(counter)
            >>> # Most common character 'l' has shortest encoding
            >>> char_order['l'].bit_encoding_size
            5
        """
        char_order: dict[str, CharEncodingMetadata] = {}

        bit_encoding_size: int = MIN_BIT_ENCODING_SIZE
        current_position: int = 1

        for char, _count in counter.most_common():
            if current_position in NON_USABLE_POSITIONS:
                bit_encoding_size += MIN_BIT_ENCODING_SIZE
                current_position = 1
                continue

            current_position += 1

            bin_value = "1" * (bit_encoding_size - MIN_BIT_ENCODING_SIZE) + bin(
                current_position
            )[2:].zfill(MIN_BIT_ENCODING_SIZE)

            char_order[char] = CharEncodingMetadata(
                bit_encoding_size, int(bin_value, 2)
            )

        return char_order
