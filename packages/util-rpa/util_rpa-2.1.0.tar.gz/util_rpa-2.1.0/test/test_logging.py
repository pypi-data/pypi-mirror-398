"""Tests for logging utilities."""
from util_rpa.logging_utils import init_logging


def test_logging_creation():
    """Test logging initialization."""
    logger = init_logging()
    assert logger is not None
