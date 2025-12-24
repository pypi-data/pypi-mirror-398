"""Protocol argument handling module.

This module provides typed argument representation and conversion utilities for
the SHDP protocol. It defines the Arg class which encapsulates protocol arguments
with their types and values, enabling type-safe argument handling and conversion
between different formats.

The module supports multiple argument types:
    - TEXT: String values
    - INT: Integer values (including hexadecimal notation)
    - BOOL: Boolean values
    - VEC_TEXT: Lists of strings
    - OPT_TEXT: Optional string values
    - OPT_VALUE: Optional complex values (dictionaries or lists)

All conversion methods return Result types for explicit error handling, ensuring
type safety and preventing runtime errors from invalid conversions.

Example usage:

    >>> from shdp.protocol.args import Arg
    >>> from shdp.utils.result import Result
    >>>
    >>> # Create typed arguments
    >>> text_arg = Arg(Arg.TEXT, "Hello")
    >>> int_arg = Arg(Arg.INT, 42)
    >>> bool_arg = Arg(Arg.BOOL, True)
    >>>
    >>> # Convert arguments to strings
    >>> result = text_arg.to_string()
    >>> if result.is_ok():
    ...     print(result.unwrap())  # "Hello"
    >>>
    >>> # Create argument from string with automatic type detection
    >>> arg = Arg.from_str("42")  # Creates Arg(INT, 42)
    >>> arg = Arg.from_str("true")  # Creates Arg(BOOL, True)
    >>> arg = Arg.from_str("0xFF")  # Creates Arg(INT, 255)
"""

import json
from dataclasses import dataclass
from typing import Any, Union

from shdp.lib import Result
from .errors import Error, ErrorKind


@dataclass
class Arg:
    """Class representing a typed argument with its associated value.

    Attributes:
        type (int): The argument type
        value (Any): The argument value

    Examples:
        >>> text_arg = Arg(Arg.TEXT, "Hello")
        >>> int_arg = Arg(Arg.INT, 42)
        >>> bool_arg = Arg(Arg.BOOL, True)
        >>> vec_arg = Arg(Arg.VEC_TEXT, ["a", "b", "c"])
        >>> opt_text_arg = Arg(Arg.OPT_TEXT, "optional")
        >>> opt_value_arg = Arg(Arg.OPT_VALUE, {"key": "value"})
    """

    type: int
    value: Any

    # Supported argument types
    TEXT = 1  # For strings
    INT = 2  # For integers
    BOOL = 3  # For booleans
    VEC_TEXT = 4  # For string lists
    OPT_TEXT = 5  # For optional strings
    OPT_VALUE = 6  # For optional complex values (dict/list)

    def __init__(self, arg_type: int, value: Any = None):
        """Initialize a new argument with its type and value.

        Args:
            arg_type (int): The argument type
            value (Any, optional): The argument value. Defaults to None.

        Examples:
            >>> text_arg = Arg(Arg.TEXT, "Hello")
            >>> int_arg = Arg(Arg.INT, 42)
        """
        self.type = arg_type
        self.value = value

    @classmethod
    def from_str(cls, s: str) -> "Arg":
        """Create an argument from a string by automatically determining its type.

        Args:
            s (str): The string to convert

        Returns:
            Arg: A new Arg instance

        Examples:
            >>> Arg.from_str("42")        # Arg(INT, 42)
            >>> Arg.from_str("0xFF")      # Arg(INT, 255)
            >>> Arg.from_str("true")      # Arg(BOOL, True)
            >>> Arg.from_str("hello")     # Arg(TEXT, "hello")
        """
        if s.startswith("0x"):
            return cls(cls.INT, int(s, 16))

        try:
            if int(s):
                return cls(cls.INT, int(s))
        except ValueError:
            pass

        if s == "true":
            return cls(cls.BOOL, True)
        if s == "false":
            return cls(cls.BOOL, False)

        return cls(cls.TEXT, s)

    def to_string(self) -> Result[str, Error]:
        """Convert the argument to a string.

        Returns:
            str: String representation of the argument

        Examples:
            >>> Arg(Arg.TEXT, "hello").to_string()           # "hello"
            >>> Arg(Arg.INT, 42).to_string()                 # "42"
            >>> Arg(Arg.BOOL, True).to_string()              # "true"
            >>> Arg(Arg.VEC_TEXT, ["a","b"]).to_string()     # "a,b"
            >>> Arg(Arg.OPT_VALUE, {"x":1}).to_string()      # '{"x":1}'
        """
        type_converters = {
            self.TEXT: lambda: self.value,
            self.INT: lambda: str(self.value),
            self.BOOL: lambda: "true" if self.value else "false",
            self.VEC_TEXT: lambda: ",".join(self.value),
            self.OPT_TEXT: lambda: self.value or "",
            self.OPT_VALUE: lambda: json.dumps(self.value),
        }

        if self.type in type_converters:
            return Result.Ok(type_converters[self.type]())

        return Result.Err(
            Error(0, ErrorKind.BAD_REQUEST, f"Invalid argument type: {self.type}")
        )

    def to_int(self) -> Result[int, Error]:
        """Convert the argument to an integer if its type is INT.

        Returns:
            int: The integer value

        Raises:
            ValueError: If the type is not INT

        Example:
            >>> Arg(Arg.INT, 42).to_int()  # 42
        """
        if self.type == self.INT:
            return Result.Ok(self.value)

        return Result.Err(
            Error(0, ErrorKind.BAD_REQUEST, f"Invalid argument type: {self.type}")
        )

    def to_bool(self) -> Result[bool, Error]:
        """Convert the argument to a boolean if its type is BOOL.

        Returns:
            bool: The boolean value

        Raises:
            ValueError: If the type is not BOOL

        Example:
            >>> Arg(Arg.BOOL, True).to_bool()  # True
        """
        if self.type == self.BOOL:
            return Result.Ok(self.value)

        return Result.Err(
            Error(0, ErrorKind.BAD_REQUEST, f"Invalid argument type: {self.type}")
        )

    def to_vec_text(self) -> Result[list[str], Error]:
        """Convert the argument to a list of strings if its type is VEC_TEXT.

        Returns:
            list[str]: The list of strings

        Raises:
            ValueError: If the type is not VEC_TEXT

        Example:
            >>> Arg(Arg.VEC_TEXT, ["a", "b"]).to_vec_text()  # ["a", "b"]
        """
        if self.type == self.VEC_TEXT:
            return Result.Ok(self.value)

        return Result.Err(
            Error(0, ErrorKind.BAD_REQUEST, f"Invalid argument type: {self.type}")
        )

    def to_opt_text(self) -> Result[str, Error]:
        """Convert the argument to an optional string if its type is OPT_TEXT.

        Returns:
            str | None: The string or None

        Raises:
            ValueError: If the type is not OPT_TEXT

        Examples:
            >>> Arg(Arg.OPT_TEXT, "hello").to_opt_text()  # "hello"
            >>> Arg(Arg.OPT_TEXT, None).to_opt_text()     # None
        """
        if self.type == self.OPT_TEXT:
            return Result.Ok(self.value)

        return Result.Err(
            Error(0, ErrorKind.BAD_REQUEST, f"Invalid argument type: {self.type}")
        )

    def to_opt_value(self) -> Result[Union[dict, list], Error]:
        """Convert the argument to an optional complex value if its type is OPT_VALUE.

        Returns:
            Union[dict, list, None]: The complex value or None

        Raises:
            ValueError: If the type is not OPT_VALUE

        Examples:
            >>> Arg(Arg.OPT_VALUE, {"x": 1}).to_opt_value()  # {"x": 1}
            >>> Arg(Arg.OPT_VALUE, [1, 2]).to_opt_value()    # [1, 2]
            >>> Arg(Arg.OPT_VALUE, None).to_opt_value()      # None
        """
        if self.type == self.OPT_VALUE:
            return Result.Ok(self.value)

        return Result.Err(
            Error(0, ErrorKind.BAD_REQUEST, f"Invalid argument type: {self.type}")
        )
