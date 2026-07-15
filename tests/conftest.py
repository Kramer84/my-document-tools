from pathlib import Path

import pytest
from typer.testing import CliRunner

from doctools.cli import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_workspace(tmp_path):

    return tmp_path
