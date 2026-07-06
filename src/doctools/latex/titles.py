import difflib
import re
from pathlib import Path

import typer
from typing_extensions import Annotated

MINOR_WORDS = {
    "and",
    "as",
    "at",
    "but",
    "by",
    "for",
    "if",
    "in",
    "nor",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "a",
    "an",
}


def to_title_case(title_text: str) -> str:
    words = title_text.split()
    transformed_words = []
    for i, word in enumerate(words):
        if not word:
            continue
        clean_word = re.sub("[^a-zA-Z]", "", word).lower()
        if i == 0 or i == len(words) - 1 or clean_word not in MINOR_WORDS:
            if word.startswith("\\") or word.startswith("$"):
                transformed_words.append(word)
            else:
                transformed_words.append(word[0].upper() + word[1:].lower())
        else:
            transformed_words.append(word.lower())
    return " ".join(transformed_words)


def process_content(content: str) -> str:
    pattern = re.compile("(\\\\(?:sub)*section\\*?\\{)")
    new_content = ""
    last_idx = 0
    for match in pattern.finditer(content):
        start_match = match.start()
        if start_match < last_idx:
            continue
        start_title = match.end()
        brace_count = 1
        end_idx = start_title
        while end_idx < len(content) and brace_count > 0:
            if content[end_idx] == "{":
                brace_count += 1
            elif content[end_idx] == "}":
                brace_count -= 1
            end_idx += 1
        if brace_count == 0:
            new_content += content[last_idx:start_match]
            prefix = match.group(1)
            title_text = content[start_title : end_idx - 1]
            transformed_title = to_title_case(title_text)
            new_content += f"{prefix}{transformed_title}}}"
            last_idx = end_idx
        else:
            pass
    new_content += content[last_idx:]
    return new_content


def process_file(file_path: Path, encoding: str, dry_run: bool):
    content = file_path.read_text(encoding=encoding)
    new_content = process_content(content)
    if new_content != content:
        original_lines = content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        typer.echo(f"\n--- Changes in: {file_path.name} ---")
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile="Before",
            tofile="After",
            lineterm="",
            n=0,
        )
        has_changes = False
        for line in diff:
            if line.startswith("+") and (not line.startswith("+++")):
                typer.secho(line, fg=typer.colors.GREEN)
                has_changes = True
            elif line.startswith("-") and (not line.startswith("---")):
                typer.secho(line, fg=typer.colors.RED)
                has_changes = True
        if has_changes and (not dry_run):
            file_path.write_text(new_content, encoding=encoding)


def normalize_titles(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a specific .tex file or a directory containing .tex files",
            exists=True,
            resolve_path=True,
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Print the diffs without writing changes to the files."
        ),
    ] = False,
    encoding: Annotated[
        str, typer.Option(help="File encoding to use when reading/writing.")
    ] = "utf-8",
    exclude: Annotated[
        str, typer.Option(help="Filename to exclude from processing.")
    ] = "normalize_titles_latex.py",
):
    if path.is_file() and path.suffix == ".tex":
        process_file(path, encoding, dry_run)
    elif path.is_dir():
        typer.echo(f"Scanning directory: {path}")
        for p in path.rglob("*.tex"):
            if p.name != exclude:
                process_file(p, encoding, dry_run)
    else:
        typer.echo(
            f"Error: Path '{path}' is not a valid .tex file or directory.", err=True
        )
        raise typer.Exit(code=1)
