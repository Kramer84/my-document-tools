import pytest
from pathlib import Path
from typer.testing import CliRunner
from doctools.cli import app

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_workspace(tmp_path):
    """Provides an isolated temporary directory for file manipulation tests."""
    return tmp_path
