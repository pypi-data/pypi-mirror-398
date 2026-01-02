"""Pytest configuration and shared fixtures."""

import pytest

from sloppy_json import RecoveryOptions


@pytest.fixture
def strict_options() -> RecoveryOptions:
    """Return strict parsing options."""
    return RecoveryOptions(strict=True)
