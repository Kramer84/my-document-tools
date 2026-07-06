import shutil
from pathlib import Path
from typing import List

import typer
from typing_extensions import Annotated

TARGET_DIRECTORIES = [
    "__pycache__",
    "build",
    "dist",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".coverage",
]
TARGET_FILES = ["*.pyc", "*.pyo", "*.pyd", ".coverage"]


def sweep_python_project(
    project_root: Annotated[
        Path,
        typer.Argument(
            help="Root directory of the Python project to clean.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = Path("."),
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="List files/directories that would be deleted without actually deleting them.",
        ),
    ] = False,
    force: Annotated[
        bool, typer.Option("-f", "--force", help="Bypass the confirmation prompt.")
    ] = False,
):
    targets_to_delete: List[Path] = []
    for pattern in TARGET_DIRECTORIES:
        for matched_dir in project_root.rglob(pattern):
            if matched_dir.is_dir():
                targets_to_delete.append(matched_dir)
    for pattern in TARGET_FILES:
        for matched_file in project_root.rglob(pattern):
            if matched_file.is_file():
                targets_to_delete.append(matched_file)
    if not targets_to_delete:
        typer.secho(
            f"✨ '{project_root.name}' is already clean. No fluff found.",
            fg=typer.colors.GREEN,
        )
        return
    typer.secho(
        f"Found {len(targets_to_delete)} artifact(s) to remove in '{project_root.name}':\n",
        fg=typer.colors.CYAN,
    )
    for target in sorted(targets_to_delete):
        typer.echo(f"  - {target.relative_to(project_root)}")
    typer.echo("")
    if dry_run:
        typer.secho("Dry run complete. No files were deleted.", fg=typer.colors.YELLOW)
        return
    if not force:
        confirm = typer.confirm("Are you sure you want to delete these items?")
        if not confirm:
            typer.secho("Operation aborted.", fg=typer.colors.RED)
            raise typer.Exit()
    deleted_count = 0
    for target in targets_to_delete:
        if target.exists():
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                deleted_count += 1
            except Exception as e:
                typer.secho(
                    f"Failed to delete {target.name}: {e}",
                    fg=typer.colors.RED,
                    err=True,
                )
    typer.secho(
        f"\n🗑️  Successfully removed {deleted_count} artifact(s).",
        fg=typer.colors.GREEN,
        bold=True,
    )
