import csv
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import typer
from typing_extensions import Annotated

CITE_REGEX_DEFAULT = (
    "\\\\[a-zA-Z]*cite[a-zA-Z*]*\\s*(?:\\[[^\\]]*\\]\\s*)*\\{([^}]+)\\}"
)


def remove_latex_comments(text: str) -> str:
    return re.sub("(?<!\\\\)%.*$", "", text, flags=re.MULTILINE)


def extract_citations(text: str, pattern: str = CITE_REGEX_DEFAULT) -> List[str]:
    text_clean = remove_latex_comments(text)
    regex = re.compile(pattern)
    citations = []
    for match in regex.finditer(text_clean):
        body = match.group(1)
        for key in body.split(","):
            k = key.strip()
            if k:
                citations.append(k)
    return citations


def analyze_citations(
    root_dir: Annotated[
        Path,
        typer.Argument(
            help="Root directory to scan recursively.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ],
    exts: Annotated[
        List[str],
        typer.Option(
            "--ext",
            help="File extensions to include. Can be used multiple times (e.g. --ext .tex --ext .txt).",
        ),
    ] = [".tex", ".txt"],
    pattern: Annotated[
        str, typer.Option(help="Regex pattern for citations.")
    ] = CITE_REGEX_DEFAULT,
    csv_path: Annotated[
        Optional[Path], typer.Option("--csv", help="Optional path to CSV output file.")
    ] = None,
    top: Annotated[int, typer.Option(help="Number of top citations to display.")] = 20,
    include_hidden: Annotated[
        bool,
        typer.Option(
            "--include-hidden",
            help="Include hidden files and directories (starting with '.').",
        ),
    ] = False,
):
    per_file_counts: Dict[str, Counter] = {}
    global_counts: Counter = Counter()
    target_files = []
    if exts:
        for ext in exts:
            target_files.extend(root_dir.rglob(f"*{ext}"))
    else:
        target_files = list(root_dir.rglob("*"))
    for path in target_files:
        if not path.is_file():
            continue
        if not include_hidden and any(
            (part.startswith(".") and part != "." for part in path.parts)
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            typer.secho(
                f"Warning: Could not read {path}: {e}", fg=typer.colors.YELLOW, err=True
            )
            continue
        citations = extract_citations(text, pattern=pattern)
        file_counter = Counter(citations)
        if file_counter:
            per_file_counts[str(path)] = file_counter
            global_counts.update(file_counter)
    if csv_path is not None:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["citation_key", "filename", "count"])
            for filename, counter in sorted(per_file_counts.items()):
                for key, count in counter.items():
                    writer.writerow([key, filename, count])
        typer.secho(f"CSV output saved to {csv_path}", fg=typer.colors.GREEN)
    if not global_counts:
        typer.secho(
            "No citations found! Check your regex or directory path.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    total_occurrences = sum(global_counts.values())
    unique_citations = len(global_counts)
    typer.secho("=" * 60, fg=typer.colors.CYAN)
    typer.secho(" CITATION ANALYSIS SUMMARY", fg=typer.colors.CYAN, bold=True)
    typer.secho("=" * 60, fg=typer.colors.CYAN)
    typer.echo(f"Total citation occurrences: {total_occurrences}")
    typer.echo(f"Unique citation keys:       {unique_citations}")
    typer.echo(f"Number of files with cites: {len(per_file_counts)}\n")
    typer.secho("-" * 60, fg=typer.colors.CYAN)
    typer.secho(
        f" TOP {min(top, unique_citations)} CITATIONS (GLOBAL)",
        fg=typer.colors.CYAN,
        bold=True,
    )
    typer.secho("-" * 60, fg=typer.colors.CYAN)
    for key, count in global_counts.most_common(top):
        freq = count / total_occurrences * 100 if total_occurrences else 0.0
        typer.echo(f"  {key:<35s} count: {count:<4d} ({freq:>5.2f}%)")
    typer.echo()
    typer.secho("-" * 60, fg=typer.colors.CYAN)
    typer.secho(" PER-FILE SUMMARY", fg=typer.colors.CYAN, bold=True)
    typer.secho("-" * 60, fg=typer.colors.CYAN)
    for filename, counter in sorted(per_file_counts.items()):
        file_total = sum(counter.values())
        unique_in_file = len(counter)
        typer.secho(f"  {filename}", fg=typer.colors.GREEN)
        typer.echo(f"    -> {file_total} total cites ({unique_in_file} unique keys)")
    typer.secho("=" * 60, fg=typer.colors.CYAN)


def extract_bib_field(body: str, field_name: str) -> Optional[str]:
    match = re.search(f"{field_name}\\s*=\\s*", body, re.IGNORECASE)
    if not match:
        return None
    start_idx = match.end()
    while start_idx < len(body) and body[start_idx].isspace():
        start_idx += 1
    if start_idx >= len(body):
        return None
    delim = body[start_idx]
    if delim == "{":
        value_chars = []
        brace_count = 0
        for idx in range(start_idx, len(body)):
            char = body[idx]
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            value_chars.append(char)
            if brace_count == 0:
                break
        return "".join(value_chars)[1:-1].strip()
    elif delim == '"':
        value_chars = []
        for idx in range(start_idx + 1, len(body)):
            char = body[idx]
            if char == '"' and body[idx - 1] != "\\":
                break
            value_chars.append(char)
        return "".join(value_chars).strip()
    else:
        end_idx = start_idx
        while end_idx < len(body) and body[end_idx] not in (",", "\n"):
            end_idx += 1
        return body[start_idx:end_idx].strip()


def parse_bib_file(bib_path: Path) -> Dict[str, Dict[str, str]]:
    if not bib_path.exists():
        typer.secho(
            f"Error: Bibliography file not found at '{bib_path}'",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    content = bib_path.read_text(encoding="utf-8", errors="ignore")
    entry_pattern = re.compile("@(\\w+)\\s*\\{\\s*([^,]+),([\\s\\S]*?)(?=\\n\\s*@|\\Z)")
    bib_entries = {}
    for match in entry_pattern.finditer(content):
        citation_key = match.group(2).strip()
        body = match.group(3)
        authors_raw = extract_bib_field(body, "author")
        if authors_raw:
            authors_clean = re.sub("\\s+", " ", authors_raw)
            bib_entries[citation_key] = {"authors": authors_clean, "body": body}
    return bib_entries


def load_analysis_csv(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        typer.secho(
            f"Error: CSV analysis file not found at '{csv_path}'. Run analyze-citations first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            reader.fieldnames = [field.strip() for field in reader.fieldnames if field]
        for row in reader:
            cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k}
            rows.append(cleaned_row)
    return rows


def find_citation_lines(tex_path: str, citation_key: str) -> List[Dict[str, str]]:
    occurrences = []
    target_file = Path(tex_path)
    if not target_file.exists():
        return occurrences
    pattern = re.compile("\\b" + re.escape(citation_key) + "\\b")
    with target_file.open("r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            if pattern.search(line):
                occurrences.append({"line_number": line_num, "text": line.strip()})
    return occurrences


def search_author_citations(target_author: str, bib_data: Dict, csv_data: List) -> Dict:
    results = {}
    target_lower = target_author.lower()
    matching_keys = {}
    for key, info in bib_data.items():
        if target_lower in info["authors"].lower():
            matching_keys[key] = info["authors"]
    if not matching_keys:
        return results
    for row in csv_data:
        key = row.get("citation_key")
        tex_file = row.get("filename")
        if key in matching_keys and tex_file:
            if key not in results:
                results[key] = {"authors": matching_keys[key], "locations": {}}
            lines_found = find_citation_lines(tex_file, key)
            if lines_found:
                results[key]["locations"][tex_file] = lines_found
    return results


def search_author(
    author_name: Annotated[
        str, typer.Argument(help="The name of the author to search for.")
    ],
    bib_file: Annotated[
        Path, typer.Option("--bib", help="Path to the .bib file.", resolve_path=True)
    ] = Path("Bibliography.bib"),
    csv_file: Annotated[
        Path,
        typer.Option("--csv", help="Path to the analysis CSV file.", resolve_path=True),
    ] = Path("bibliography_analysis.csv"),
):
    typer.echo(f"Parsing {bib_file.name} and cross-referencing with {csv_file.name}...")
    bib_data = parse_bib_file(bib_file)
    csv_data = load_analysis_csv(csv_file)
    results = search_author_citations(author_name, bib_data, csv_data)
    if not results:
        typer.secho(
            f"\nNo citations found matching author: '{author_name}'",
            fg=typer.colors.YELLOW,
        )
        return
    typer.secho(
        f"\nFound occurrences for author search: '{author_name}'",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo("=" * 80)
    for key, data in results.items():
        typer.secho(f"\n[Key]     : {key}", fg=typer.colors.CYAN)
        typer.echo(f"[Authors] : {data['authors']}")
        if not data["locations"]:
            typer.secho(
                "  ↳ Logged in CSV but no active match instances located in the .tex source files.",
                fg=typer.colors.YELLOW,
            )
            continue
        for file_path, lines in data["locations"].items():
            typer.secho(f"  ↳ File: {file_path}", fg=typer.colors.MAGENTA)
            for l in lines:
                typer.echo(f"      Line {l['line_number']}: {l['text']}")
    typer.echo("=" * 80)
