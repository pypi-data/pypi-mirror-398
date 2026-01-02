"""Exception classes for sloppy_json."""

from dataclasses import dataclass


class SloppyJSONError(Exception):
    """Base exception for sloppy_json errors."""

    pass


@dataclass
class ErrorInfo:
    """Information about a parsing error."""

    message: str
    position: int
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.message} at line {self.line}, column {self.column}"


class SloppyJSONDecodeError(SloppyJSONError):
    """Exception raised when JSON decoding fails."""

    def __init__(self, message: str, position: int = 0, line: int = 1, column: int = 1):
        self.message = message
        self.position = position
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column} (position {position})")

    def to_error_info(self) -> ErrorInfo:
        return ErrorInfo(
            message=self.message,
            position=self.position,
            line=self.line,
            column=self.column,
        )
