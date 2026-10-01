import ast
import io
import subprocess
import tokenize
from pathlib import Path
from typing import List

import typer
from typing_extensions import Annotated


def strip_comments_and_docstrings(source_code: str, keep_docstrings: bool = False) -> str:
    """Strips comments and optionally docstrings using token re-emission."""
    io_obj = io.StringIO(source_code)
    out_tokens = []

    try:
        token_gen = tokenize.generate_tokens(io_obj.readline)
        prev_toktype = tokenize.INDENT
        first_token = True

        for tok in token_gen:
            tok_type, tok_val, _, _, _ = tok

            if tok_type == tokenize.COMMENT:
                continue

            if not keep_docstrings and tok_type == tokenize.STRING:
                if first_token or prev_toktype in (tokenize.INDENT, tokenize.NEWLINE, tokenize.NL):
                    continue

            out_tokens.append((tok_type, tok_val))
            if tok_type not in (tokenize.NL, tokenize.COMMENT):
                prev_toktype = tok_type
            first_token = False

        return tokenize.untokenize(out_tokens)
    except tokenize.TokenError:
        return source_code


def format_with_ruff(source_code: str) -> str:
    # 1. Sort imports (--exit-zero ensures warnings don't abort execution)
    check_proc = subprocess.run(
        ["ruff", "check", "--select", "I", "--fix", "--exit-zero", "-"],
        input=source_code,
        text=True,
        capture_output=True,
    )
    # Only fall back to unorganized code if stdout was completely empty
    sorted_code = check_proc.stdout if check_proc.stdout.strip() else source_code

    # 2. Format code
    fmt_proc = subprocess.run(
        ["ruff", "format", "-"],
        input=sorted_code,
        text=True,
        capture_output=True,
    )
    if fmt_proc.returncode != 0:
        raise RuntimeError(f"Ruff format rejected code:\n{fmt_proc.stderr}")

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
    exclude: Annotated[
        List[str],
        typer.Option(
            "-e",
            "--exclude",
            help="File or directory names/patterns to skip.",
        ),
    ] = [
        ".venv",
        "venv",
        ".git",
        "__pycache__",
        "*.egg-info",
        "build",
        "dist",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "site-packages",
    ],
):
    target_files: List[Path] = []
    cwd = Path.cwd()

    def is_excluded(path: Path) -> bool:
        for part in path.parts:
            for pattern in exclude:
                if part == pattern or path.match(pattern) or Path(part).match(pattern):
                    return True
        return False

    for path in files:
        if is_excluded(path):
            continue

        if path.is_file() and path.suffix == ".py":
            target_files.append(path)
        elif path.is_dir():
            for p in path.rglob("*.py"):
                if not is_excluded(p):
                    target_files.append(p)

    for file_path in target_files:
        try:
            rel_path = file_path.relative_to(cwd)
        except ValueError:
            rel_path = file_path

        try:
            source = file_path.read_text(encoding="utf-8")
            if not source.strip():
                continue

            cleaned = strip_comments_and_docstrings(source, keep_docstrings=keep_docstrings)
            formatted = format_with_ruff(cleaned)

            # --- HARD SAFETY CHECKS ---
            if not formatted.strip() and source.strip():
                raise RuntimeError("Sanity check failed: output is empty while source was not.")

            # Validate that output is strictly valid Python
            try:
                ast.parse(formatted)
            except SyntaxError as e:
                raise RuntimeError(f"Sanity check failed: output contains invalid syntax ({e}).")

            if in_place:
                if backup:
                    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                    backup_path.write_text(source, encoding="utf-8")

                # Atomic write via temp file
                tmp_file = file_path.with_suffix(file_path.suffix + ".tmp")
                tmp_file.write_text(formatted, encoding="utf-8")
                tmp_file.replace(file_path)

                typer.secho(f"Successfully cleaned: {rel_path}", fg=typer.colors.GREEN)
            else:
                if len(target_files) > 1:
                    typer.secho(f"# --- {rel_path} ---", fg=typer.colors.BLUE)
                typer.echo(formatted)

        except Exception as e:
            typer.secho(f"Skipping {rel_path} due to error: {e}", fg=typer.colors.RED, err=True)


if __name__ == "__main__":
    typer.run(clean_python)
