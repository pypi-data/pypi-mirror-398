"""Sloppy JSON - A forgiving JSON parser for LLM outputs."""

from .detector import detect_required_options
from .exceptions import SloppyJSONDecodeError, SloppyJSONError
from .options import RecoveryOptions
from .parser import parse, parse_lenient, parse_permissive, parse_strict

__all__ = [
    "RecoveryOptions",
    "SloppyJSONDecodeError",
    "SloppyJSONError",
    "detect_required_options",
    "parse",
    "parse_lenient",
    "parse_permissive",
    "parse_strict",
]

__version__ = "0.1.0"
