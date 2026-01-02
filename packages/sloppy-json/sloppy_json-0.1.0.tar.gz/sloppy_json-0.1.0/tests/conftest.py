"""Pytest configuration and shared fixtures."""

import pytest

from sloppy_json import RecoveryOptions


@pytest.fixture
def strict_options() -> RecoveryOptions:
    """Return strict parsing options."""
    return RecoveryOptions.strict()


@pytest.fixture
def lenient_options() -> RecoveryOptions:
    """Return lenient parsing options."""
    return RecoveryOptions.lenient()


@pytest.fixture
def permissive_options() -> RecoveryOptions:
    """Return permissive parsing options."""
    return RecoveryOptions.permissive()
