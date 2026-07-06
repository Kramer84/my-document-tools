import difflib
import re
from pathlib import Path
from typing import List, Optional, Tuple

import typer
from typing_extensions import Annotated

PREFIX_MAP = {"section": "sec", "subsection": "ssec", "subsubsection": "sssec"}


def normalize_title(title_text: str) -> str:
    text = title_text.replace("$", "")
    text = text.replace("\\", "")
    text = text.replace("&", "and")
    text = text.replace("/", "_")
    text = re.sub("[^\\w\\s-]", "", text)
    text = re.sub("[\\s_]+", "_", text)
    return text.lower().strip("_")


def parse_sections_and_labels(
    file_path: Path, encoding: str
) -> Tuple[List[str], List[Tuple[int, str, str, Optional[str]]]]:
    lines = file_path.read_text(encoding=encoding).splitlines(keepends=True)
    sec_pattern = re.compile("\\\\((?:sub)*section)\\*?\\{([^}]+)\\}")
    label_pattern = re.compile("^\\s*\\\\label\\{([^}]+)\\}\\s*$")
    results = []
    for i, line in enumerate(lines):
        match = sec_pattern.search(line)
        if match:
            sec_type = match.group(1)
            title = match.group(2)
            existing_label = None
            if i + 1 < len(lines):
                label_match = label_pattern.match(lines[i + 1])
                if label_match:
                    existing_label = label_match.group(1)
            results.append((i, sec_type, title, existing_label))
    return (lines, results)


def normalize_labels(
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
    ] = "normalize_latex_labels.py",
):
    file_list: List[Path] = []
    if path.is_file() and path.suffix == ".tex":
        file_list.append(path)
    elif path.is_dir():
        for p in path.rglob("*.tex"):
            if p.name != exclude:
                file_list.append(p)
    else:
        typer.echo(
            f"Error: Path '{path}' does not point to a valid .tex file or directory.",
            err=True,
        )
        raise typer.Exit(code=1)
    global_label_map = {}
    file_structures = {}
    for file_path in file_list:
        lines, structures = parse_sections_and_labels(file_path, encoding)
        file_structures[file_path] = (lines, structures)
        for _, sec_type, title, existing_label in structures:
            prefix = PREFIX_MAP.get(sec_type, "sec")
            normalized = normalize_title(title)
            new_label = f"{prefix}:{normalized}"
            if existing_label:
                global_label_map[existing_label] = new_label
    for file_path in file_list:
        lines, structures = file_structures[file_path]
        new_lines = list(lines)
        for idx, sec_type, title, existing_label in reversed(structures):
            prefix = PREFIX_MAP.get(sec_type, "sec")
            normalized = normalize_title(title)
            new_label = f"{prefix}:{normalized}"
            if existing_label:
                new_lines[idx + 1] = f"\\label{{{new_label}}}\n"
            else:
                new_lines.insert(idx + 1, f"\\label{{{new_label}}}\n")
        content = "".join(new_lines)
        for old_label, new_label in global_label_map.items():
            ref_pattern = re.compile(f"(?<=\\{{){re.escape(old_label)}(?=\\}})")
            content = ref_pattern.sub(new_label, content)
        final_lines = content.splitlines(keepends=True)
        if lines != final_lines:
            typer.echo(f"\n--- Label Changes in: {file_path.name} ---")
            diff = difflib.unified_diff(
                lines, final_lines, fromfile="Before", tofile="After", lineterm="", n=1
            )
            has_printed = False
            for line in diff:
                if line.startswith("+") and (not line.startswith("+++")):
                    typer.secho(line, fg=typer.colors.GREEN, nl=False)
                    has_printed = True
                elif line.startswith("-") and (not line.startswith("---")):
                    typer.secho(line, fg=typer.colors.RED, nl=False)
                    has_printed = True
            if has_printed and (not dry_run):
                file_path.write_text("".join(final_lines), encoding=encoding)
