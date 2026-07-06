import re
from pathlib import Path
from typing import Dict, List, Tuple

import typer
from typing_extensions import Annotated


def search_strings(
    strings_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the text file containing strings (one per line).",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    folder: Annotated[
        Path,
        typer.Argument(
            help="Path to the folder/directory to search inside.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ],
    file_pattern: Annotated[
        str,
        typer.Option(
            help="Glob pattern to filter which files to search (e.g., '*.py', '*.tex')."
        ),
    ] = "*",
    encoding: Annotated[
        str, typer.Option(help="File encoding to use when reading.")
    ] = "utf-8",
    errors: Annotated[
        str, typer.Option(help="Error handling scheme for decoding errors.")
    ] = "ignore",
):
    try:
        raw_lines = strings_file.read_text(encoding=encoding).splitlines()
        search_strings_list = [line.strip() for line in raw_lines if line.strip()]
    except Exception as e:
        typer.echo(f"Error reading file '{strings_file}': {e}", err=True)
        raise typer.Exit(code=1)
    if not search_strings_list:
        typer.echo("The search strings file is empty. Nothing to search for.")
        return
    typer.echo(
        f"Searching for {len(search_strings_list)} strings across '{file_pattern}' files in '{folder}'...\n"
    )
    results: Dict[str, List[Tuple[Path, int]]] = {
        string: [] for string in search_strings_list
    }
    escaped_strings = [re.escape(s) for s in search_strings_list]
    fast_check_pattern = re.compile("|".join(escaped_strings))
    for file_path in folder.rglob(file_pattern):
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding=encoding, errors=errors) as f:
                    for line_num, line in enumerate(f, start=1):
                        if fast_check_pattern.search(line):
                            for string in search_strings_list:
                                if string in line:
                                    results[string].append((file_path, line_num))
            except Exception:
                continue
    for string, matches in results.items():
        typer.secho(f"=== Results for: '{string}' ===", fg=typer.colors.CYAN)
        if matches:
            typer.secho(f"Found {len(matches)} match(es):", fg=typer.colors.GREEN)
            for file_path, line_num in matches:
                typer.echo(f"  - {file_path} (Line {line_num})")
        else:
            typer.echo("  No matches found.")
        typer.echo("-" * 40)
