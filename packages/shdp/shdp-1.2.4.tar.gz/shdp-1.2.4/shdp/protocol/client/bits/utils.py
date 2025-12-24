"""
Utilities for handling SHDP protocol bit operations and character encoding.

This module provides:
- Character mapping for special encoding (CHARS dict)
- Operating and Operation codes for the protocol
- Bit operations for handling 5-bit sequences (fyves)

Example usage:
    # Reading an operation from a bit stream
    decoder = BitDecoder()
    operation = FyveImpl.get_op(decoder)

    # Getting a character from encoded values
    if operation.kind == OperatingCode.CHARACTER:
        char = operation.get_char()  # Returns decoded character
"""

from enum import Enum
from shdp.utils.result import Result
from shdp.utils.bitvec import Msb
from ...errors import Error, ErrorKind
from ...managers.bits.decoder import BitDecoder


CHARS: dict[int, str] = {
    1: " ",
    2: "t",
    3: "a",
    4: "e",
    5: "i",
    6: "n",
    7: "o",
    8: "r",
    9: "s",
    10: "d",
    11: "l",
    12: "-",
    13: '"',
    14: "c",
    15: "p",
    16: "f",
    17: ">",
    18: "=",
    19: ".",
    20: "v",
    21: "<",
    22: "u",
    23: "m",
    24: ";",
    25: "g",
    26: ":",
    27: "/",
    28: "h",
    29: "y",
    30: "x",
    993: "b",
    994: "k",
    995: ")",
    996: "(",
    997: "w",
    998: "E",
    999: "#",
    1000: "}",
    1001: "{",
    1002: "0",
    1003: "N",
    1004: "A",
    1005: "2",
    1006: "R",
    1007: "1",
    1008: "T",
    1009: "D",
    1010: "O",
    1011: "I",
    1012: "S",
    1013: "_",
    1014: "P",
    1015: "L",
    1016: "6",
    1017: "4",
    1018: ",",
    1019: "z",
    1020: "M",
    1021: "C",
    1022: "B",
    32737: "G",
    32738: "%",
    32739: "j",
    32740: "3",
    32741: "U",
    32742: "8",
    32743: "*",
    32744: "5",
    32745: "9",
    32746: "+",
    32747: "F",
    32748: "|",
    32749: "W",
    32750: "V",
    32751: "@",
    32752: "q",
    32753: "'",
    32754: "Q",
    32755: "H",
    32756: "!",
    32757: "]",
    32758: "[",
    32759: "7",
    32760: "Z",
    32761: "Y",
    32762: "X",
    32763: "J",
    32764: "^",
    32765: "K",
    32766: "?",
    1048545: "$",
    1048546: "\\",
    1048547: "~",
    1048548: "`",
    1048549: "&",
}


class OperatingCode(Enum):
    """Operating code for the SHDP protocol.

    Used to distinguish between system operations and character data.

    Examples:
        >>> op = OperatingCode.from_fyve(0x00)
        >>> op == OperatingCode.SYSTEM
        True

        >>> op = OperatingCode.from_fyve(0x1f)
        >>> op == OperatingCode.CHARACTER
        True
    """

    SYSTEM = 0x00
    CHARACTER = 0x1F

    @classmethod
    def from_fyve(cls, fyve: int) -> "OperatingCode":
        """Convert a 5-bit value (fyve) to an OperatingCode.

        Args:
            fyve: 5-bit integer value (0x00 or other)

        Returns:
            OperatingCode.SYSTEM for 0x00, OperatingCode.CHARACTER otherwise

        Example:
            >>> OperatingCode.from_fyve(0x00)
            OperatingCode.SYSTEM
            >>> OperatingCode.from_fyve(0x1f)
            OperatingCode.CHARACTER
        """
        if fyve == 0x00:
            return cls.SYSTEM

        return cls.CHARACTER

    def to_fyve(self) -> int:
        """Convert the OperatingCode to its 5-bit representation.

        Returns:
            Integer value (0x00 for SYSTEM, 0x1f for CHARACTER)

        Example:
            >>> OperatingCode.SYSTEM.to_fyve()
            0x00
            >>> OperatingCode.CHARACTER.to_fyve()
            0x1f
        """
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class OperationCode(Enum):
    """Operation codes for different SHDP protocol actions.

    Defines the specific operations that can be performed in SYSTEM mode:
    - UTF8_CHAIN: Handle UTF-8 encoded character sequences
    - START_OF_TAG: Begin a new XML/HTML tag
    - START_OF_ATTRIBUTE: Begin a tag attribute
    - START_OF_DATA: Begin data content
    - END_OF_DATA: End data content

    Examples:
        >>> op = OperationCode.from_fyve(0x10)
        >>> op == OperationCode.START_OF_TAG
        True
    """

    UTF8_CHAIN = 0x00
    START_OF_TAG = 0x10
    START_OF_ATTRIBUTES = 0x11
    START_OF_DATA = 0x18
    END_OF_DATA = 0x19
    UNKNOWN = 0xFF

    @classmethod
    def from_fyve(cls, fyve: int) -> "OperationCode":
        """Convert a 5-bit value to an OperationCode.

        Args:
            fyve: 5-bit integer value representing the operation

        Returns:
            Corresponding OperationCode or UNKNOWN if value not recognized

        Example:
            >>> OperationCode.from_fyve(0x10)
            OperationCode.START_OF_TAG
            >>> OperationCode.from_fyve(0x18)
            OperationCode.START_OF_DATA
        """
        if fyve == 0x00:
            return cls.UTF8_CHAIN
        if fyve == 0x10:
            return cls.START_OF_TAG
        if fyve == 0x11:
            return cls.START_OF_ATTRIBUTES
        if fyve == 0x18:
            return cls.START_OF_DATA
        if fyve == 0x19:
            return cls.END_OF_DATA
        return cls.UNKNOWN

    def to_fyve(self) -> int:
        """Convert the OperationCode to its 5-bit representation.

        Returns:
            Integer value corresponding to the operation code

        Example:
            >>> OperationCode.START_OF_TAG.to_fyve()
            0x10
            >>> OperationCode.END_OF_DATA.to_fyve()
            0x19
        """
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class Operation:
    """Represents a complete SHDP protocol operation.

    Handles both system operations and character data by decoding 5-bit sequences
        (fyves).

    Examples:
        # Decoding a character operation
        >>> decoder = BitDecoder()
        >>> op = Operation.from_fyve(0x1f, decoder)  # For multi-fyve character
        >>> char = op.get_char()  # Returns the decoded character

        # Decoding a system operation
        >>> op = Operation.from_fyve(0x00, decoder)
        >>> op.kind == OperatingCode.SYSTEM
        True
        >>> op.code == OperationCode.START_OF_TAG  # If next fyve was 0x10
        True
    """

    kind: OperatingCode
    code: OperationCode | None
    values: list[int] = []

    def __init__(
        self, kind: OperatingCode, code: OperationCode | None, values: list[int]
    ):
        """Initialize a new operation instance.

        Args:
            kind (OperatingCode): The type of operation being performed.
            code (OperationCode | None): The specific operation code. Can be None
                for certain operation types.
            values (list[int]): List of integer values associated with this operation.

        Examples:
            >>> # Create a basic operation
            >>> op = Operation(OperatingCode.READ, OperationCode.GET_STATUS, [1, 2, 3])

            >>> # Create an operation without a specific code
            >>> op = Operation(OperatingCode.WRITE, None, [255, 128])

            >>> # Create an operation with empty values
            >>> op = Operation(OperatingCode.QUERY, OperationCode.LIST_DEVICES, [])

        Note:
            The values list typically contains byte values (0-255) that will be used
            in the operation's execution.
        """
        self.kind = kind
        self.code = code
        self.values = values

    @staticmethod
    def from_fyve(fyve: int, decoder: BitDecoder[Msb]) -> Result["Operation", Error]:
        """Create an Operation from an initial fyve and subsequent bits.

        Args:
            fyve: Initial 5-bit value determining operation type
            decoder: Bit decoder for reading additional values

        Returns:
            Result[Operation, Error]: New Operation instance

        Example:
            >>> decoder = BitDecoder(bytes([0x1f, 0x03]))  # Character 'a'
            >>> op = Operation.from_fyve(0x1f, decoder)
            >>> op.kind == OperatingCode.CHARACTER
            True
            >>> op.get_char()
            Result.Ok('a')
        """
        Result.hide()

        op = OperatingCode.from_fyve(fyve)

        code: OperationCode | None = None

        values: list[int] = []
        values.append(fyve)

        if op == OperatingCode.SYSTEM:
            operator = decoder.read_data(5).unwrap().to_int().unwrap()

            code = OperationCode.from_fyve(operator)
            values.append(operator)
        else:
            op = OperatingCode.CHARACTER

            if fyve == 0x1F:
                next_fyve = decoder.read_data(5).unwrap().to_int().unwrap()
                values.append(next_fyve)

                while next_fyve == 0x1F:
                    next_fyve = decoder.read_data(5).unwrap().to_int().unwrap()
                    values.append(next_fyve)

        r: Result[None, Error] = Result.reveal()
        if r.is_err():
            return Result[Operation, Error].Err(r.unwrap_err())

        return Result.Ok(Operation(kind=op, code=code, values=values))

    def get_char(self, chars: dict[int, str] | None = None) -> Result[str, Error]:
        """Convert stored fyve values to a character using CHARS mapping.

        The method combines multiple 5-bit values into a single integer
        and looks up the corresponding character in the CHARS dictionary.

        Args:
            chars: Dictionary of character values to use for decoding.
                If None, uses default CHARS mapping.

        Returns:
            Result[str, Error]: Decoded character string

        Raises:
            Error: If the computed value isn't in CHARS dictionary

        Example:
            >>> op = Operation(kind=OperatingCode.CHARACTER,
            ...              code=None,
            ...              values=[0x1f, 0x03])
            >>> op.get_char()
            Result.Ok('a')
        """

        if chars is None:
            chars = CHARS

        values = self.values
        values.reverse()

        value = 0
        for i, v in enumerate[int](values):
            value |= v << (i * 5)

        if value in chars:
            return Result.Ok(chars[value])
        return Result.Err(
            Error(0, ErrorKind.BAD_REQUEST, f"Unknown character value: {value}")
        )


class FyveImpl:
    """Implementation of 5-bit (fyve) operations for the SHDP protocol.

    Provides static methods for reading and processing fyve sequences.

    Examples:
        >>> decoder = BitDecoder()
        >>> fyve = FyveImpl.read_fyve(decoder)  # Reads next 5 bits
        >>> operation = FyveImpl.get_op(decoder)  # Gets complete operation
    """

    @staticmethod
    def get_op(decoder: BitDecoder[Msb]) -> Result["Operation", Error]:
        """Read and construct a complete Operation from the bit stream.

        Args:
            decoder: Bit decoder for reading 5-bit sequences

        Returns:
            Result[Operation, Error]: Constructed Operation instance

        Example:
            >>> decoder = BitDecoder(bytes([0x00, 0x10]))  # START_OF_TAG
            >>> op = FyveImpl.get_op(decoder)
            >>> op.kind == OperatingCode.SYSTEM
            True
            >>> op.code == OperationCode.START_OF_TAG
            True
        """
        op = FyveImpl.read_fyve(decoder)
        if op.is_err():
            return Result[Operation, Error].Err(op.unwrap_err())

        return Operation.from_fyve(op.unwrap(), decoder)

    @staticmethod
    def read_fyve(decoder: BitDecoder[Msb]) -> Result[int, Error]:
        """Read a single 5-bit value from the decoder.

        Args:
            decoder: Bit decoder for reading values

        Returns:
            Result[int, Error]: 5-bit integer value (0-31)

        Example:
            >>> decoder = BitDecoder(bytes([0x1f]))
            >>> FyveImpl.read_fyve(decoder)
            Result.Ok(31)  # 0x1f
        """
        return decoder.read_data(5).unwrap().to_int()
