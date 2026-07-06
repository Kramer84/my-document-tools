import ast
import subprocess
import sys
from pathlib import Path
from typing import List

import typer
from typing_extensions import Annotated


class DocstringStripper(ast.NodeTransformer):
    def _strip_docstring(self, node):
        self.generic_visit(node)
        if (
            hasattr(node, "body")
            and isinstance(node.body, list)
            and (len(node.body) > 0)
        ):
            first_stmt = node.body[0]
            if (
                isinstance(first_stmt, ast.Expr)
                and isinstance(first_stmt.value, ast.Constant)
                and isinstance(first_stmt.value.value, str)
            ):
                node.body.pop(0)
                if len(node.body) == 0:
                    node.body.append(ast.Pass())
        return node

    def visit_Module(self, node):
        return self._strip_docstring(node)

    def visit_ClassDef(self, node):
        return self._strip_docstring(node)

    def visit_FunctionDef(self, node):
        return self._strip_docstring(node)

    def visit_AsyncFunctionDef(self, node):
        return self._strip_docstring(node)


def clean_code(source_code: str, keep_docstrings: bool = False) -> str:
    tree = ast.parse(source_code)
    if not keep_docstrings:
        stripper = DocstringStripper()
        tree = stripper.visit(tree)
        ast.fix_missing_locations(tree)
    return ast.unparse(tree)


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
