"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    temp = Path(tempfile.mkdtemp(prefix="pyautokit_test_"))
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def clean_temp_dir():
    """Create a clean temporary directory for each test."""
    temp = Path(tempfile.mkdtemp(prefix="pyautokit_clean_"))
    yield temp
    shutil.rmtree(temp, ignore_errors=True)
