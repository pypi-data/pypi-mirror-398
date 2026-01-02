"""Sloppy JSON - A forgiving JSON parser for LLM outputs."""

from .exceptions import SloppyJSONDecodeError, SloppyJSONError
from .options import RecoveryOptions
from .parser import parse

__all__ = [
    "RecoveryOptions",
    "SloppyJSONDecodeError",
    "SloppyJSONError",
    "parse",
]

__version__ = "0.2.0"
