"""Tests for ABF file I/O."""

import pytest
from pyioneer.io import load_abf, ABFReader


def test_abf_reader_initialization():
    """Test ABFReader initialization (requires actual ABF file)."""
    # This test would require a real ABF file
    # For now, we just test that the class exists
    assert ABFReader is not None


def test_load_abf_function():
    """Test load_abf convenience function."""
    # This test would require a real ABF file
    # For now, we just test that the function exists
    assert load_abf is not None


# Note: Full I/O tests would require actual ABF files
# These can be added when test data is available

