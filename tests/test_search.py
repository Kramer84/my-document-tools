import pytest
from typer.testing import CliRunner

from doctools.cli import app

runner = CliRunner()


def test_search_strings_integration(temp_workspace):
    strings_file = temp_workspace / "strings.txt"
    strings_file.write_text("TODO\nFIXME\n")

    target_dir = temp_workspace / "src"
    target_dir.mkdir()

    py_file = target_dir / "main.py"
    py_file.write_text(
        "def main():\n"
        "    # TODO: Refactor this\n"
        "    print('Hello')  # FIXME: Typo\n"
        "    pass\n"
    )

    tex_file = target_dir / "doc.tex"
    tex_file.write_text("% TODO: Write abstract\n")

    result = runner.invoke(
        app, ["search", str(strings_file), str(target_dir), "--file-pattern", "*.*"]
    )

    assert result.exit_code == 0

    assert "=== Results for: 'TODO' ===" in result.stdout
    assert "=== Results for: 'FIXME' ===" in result.stdout

    assert "main.py (Line 2)" in result.stdout
    assert "doc.tex (Line 1)" in result.stdout
    assert "main.py (Line 3)" in result.stdout


def test_search_strings_empty_file(temp_workspace):
    strings_file = temp_workspace / "empty.txt"
    strings_file.write_text("\n   \n")
    target_dir = temp_workspace / "src"
    target_dir.mkdir()

    result = runner.invoke(app, ["search", str(strings_file), str(target_dir)])

    assert result.exit_code == 0
    assert "The search strings file is empty. Nothing to search for." in result.stdout
