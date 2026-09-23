import io
import subprocess
import sys
import tokenize
from pathlib import Path
from typing import List

import typer
from typing_extensions import Annotated


def strip_comments_and_docstrings(source_code: str, keep_docstrings: bool = False) -> str:
    """Strips comments and optionally docstrings using token re-emission

    rather than coordinate-dependent untokenize.
    """
    io_obj = io.StringIO(source_code)
    out_tokens = []

    try:
        token_gen = tokenize.generate_tokens(io_obj.readline)
        prev_toktype = tokenize.INDENT
        first_token = True

        for tok in token_gen:
            tok_type, tok_val, _, _, _ = tok

            # Drop comments
            if tok_type == tokenize.COMMENT:
                continue

            # Identify docstrings: standalone STRING tokens following INDENT, NEWLINE, or at BOF
            if not keep_docstrings and tok_type == tokenize.STRING:
                if first_token or prev_toktype in (tokenize.INDENT, tokenize.NEWLINE, tokenize.NL):
                    continue

            out_tokens.append((tok_type, tok_val))
            if tok_type not in (tokenize.NL, tokenize.COMMENT):
                prev_toktype = tok_type
            first_token = False

        result = tokenize.untokenize(out_tokens)
        return result
    except tokenize.TokenError:
        return source_code


def format_with_ruff(source_code: str) -> str:
    # 1. Sort imports
    check_proc = subprocess.run(
        ["ruff", "check", "--select", "I", "--fix", "-"],
        input=source_code,
        text=True,
        capture_output=True,
    )
    if check_proc.returncode != 0:
        raise RuntimeError(f"Ruff sort failed: {check_proc.stderr}")

    sorted_code = check_proc.stdout

    # 2. Format code and remove excess blank lines
    fmt_proc = subprocess.run(
        ["ruff", "format", "-"],
        input=sorted_code,
        text=True,
        capture_output=True,
    )
    if fmt_proc.returncode != 0:
        raise RuntimeError(f"Ruff format failed: {fmt_proc.stderr}")

    return fmt_proc.stdout


def clean_python(
    files: Annotated[
        List[Path],
        typer.Argument(
            help="Python file(s) or folder(s) to process",
            exists=True,
            resolve_path=True,
        ),
    ],
    in_place: Annotated[
        bool, typer.Option("-i", "--in-place", help="Modify files in place.")
    ] = False,
    backup: Annotated[
        bool,
        typer.Option(
            "--backup", help="Create a .bak backup file if modifying in place."
        ),
    ] = False,
    keep_docstrings: Annotated[
        bool,
        typer.Option(
            "--keep-docstrings", help="Preserve docstrings (only removes # comments)."
        ),
    ] = False,
):
    target_files: List[Path] = []
    for path in files:
        if path.is_file() and path.suffix == ".py":
            target_files.append(path)
        elif path.is_dir():
            target_files.extend(path.rglob("*.py"))

    for file_path in target_files:
        try:
            source = file_path.read_text(encoding="utf-8")
            cleaned = strip_comments_and_docstrings(source, keep_docstrings=keep_docstrings)
            formatted = format_with_ruff(cleaned)

            if in_place:
                if backup:
                    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                    backup_path.write_text(source, encoding="utf-8")
                file_path.write_text(formatted, encoding="utf-8")
                typer.secho(f"Successfully cleaned: {file_path.name}", fg=typer.colors.GREEN)
            else:
                if len(target_files) > 1:
                    typer.secho(f"# --- {file_path.name} ---", fg=typer.colors.BLUE)
                typer.echo(formatted)

        except Exception as e:
            typer.secho(f"Skipping {file_path.name} due to error: {e}", fg=typer.colors.RED, err=True)


if __name__ == "__main__":
    typer.run(clean_python)
