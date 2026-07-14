import ast
import io
import subprocess
import sys
import tokenize
from pathlib import Path
from typing import List

import typer
from typing_extensions import Annotated


def clean_code(source_code: str, keep_docstrings: bool = False) -> str:
    """
    Cleans the source code by removing comments and optionally docstrings,
    using tokenization to preserve string formatting (like multiline templates).
    """
    # 1. Identify the exact start and end coordinates of docstrings using AST
    docstring_ranges = []
    if not keep_docstrings:
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        expr = node.body[0]
                        # Capture (start_line, start_col, end_line, end_col)
                        docstring_ranges.append(
                            (expr.lineno, expr.col_offset, expr.end_lineno, expr.end_col_offset)
                        )
        except SyntaxError:
            # If the code has syntax errors, skip docstring removal and let Ruff/Python catch it later
            pass

    # 2. Tokenize the source, filtering out comments and docstrings
    tokens = []
    try:
        io_obj = io.StringIO(source_code)
        for tok in tokenize.generate_tokens(io_obj.readline):
            # Strip all # comments
            if tok.type == tokenize.COMMENT:
                continue
            
            # Strip docstrings if they fall within the AST coordinates we found
            if not keep_docstrings and tok.type == tokenize.STRING:
                is_docstring = False
                for (start_line, start_col, end_line, end_col) in docstring_ranges:
                    if (start_line, start_col) <= tok.start and tok.end <= (end_line, end_col):
                        is_docstring = True
                        break
                if is_docstring:
                    continue
                    
            tokens.append(tok)
            
        # Reconstruct the string. Untokenize faithfully preserves your multiline strings!
        cleaned_source = tokenize.untokenize(tokens)
    except tokenize.TokenError:
        # Fallback to original source if tokenization unexpectedly fails
        cleaned_source = source_code

    return cleaned_source


def format_with_ruff(source_code: str) -> str:
    try:
        process_check = subprocess.run(
            ["ruff", "check", "--select", "I", "--fix", "-"],
            input=source_code,
            text=True,
            capture_output=True,
            check=True,
        )
        sorted_code = process_check.stdout
        process_format = subprocess.run(
            ["ruff", "format", "-"],
            input=sorted_code,
            text=True,
            capture_output=True,
            check=True,
        )
        formatted_code = process_format.stdout
        if '\nif __name__ == "__main__":' in formatted_code:
            formatted_code = formatted_code.replace(
                '\nif __name__ == "__main__":', '\n\nif __name__ == "__main__":'
            )
        return formatted_code.rstrip() + "\n"
    except subprocess.CalledProcessError as e:
        typer.secho(
            f"Ruff formatting failed: {e.stderr}", fg=typer.colors.YELLOW, err=True
        )
        return source_code


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
            cleaned_source = clean_code(source, keep_docstrings)
            formatted_source = format_with_ruff(cleaned_source)
            if in_place:
                if backup:
                    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                    backup_path.write_text(source, encoding="utf-8")
                file_path.write_text(formatted_source, encoding="utf-8")
                typer.secho(
                    f"Successfully cleaned: {file_path.name}", fg=typer.colors.GREEN
                )
            else:
                if len(target_files) > 1:
                    typer.secho(f"# --- {file_path.name} ---", fg=typer.colors.BLUE)
                typer.echo(formatted_source)
        except SyntaxError as e:
            typer.secho(
                f"Syntax Error in {file_path.name}: Cannot parse invalid Python code. ({e})",
                fg=typer.colors.RED,
                err=True,
            )
        except Exception as e:
            typer.secho(
                f"Error processing {file_path.name}: {e}", fg=typer.colors.RED, err=True
            )


if __name__ == "__main__":
    typer.run(clean_python)