import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence

import typer
from typing_extensions import Annotated


DEFAULT_EXCLUDES = [
    # User-requested externals
    "beartype*",
    "numpy*",
    "matplotlib*",
    "IPython*",
    "sklearn*",
    "torcheval*",
    "tqdm*",
    "pytransform3d*",
    "torch*",
    "trimesh*",
    # Common hubs that add clutter
    "typing*",
    "collections*",
]


class RankDir(str, Enum):
    """Available directions for the dependency graph layout."""
    TB = "TB"
    BT = "BT"
    LR = "LR"
    RL = "RL"


def build_excludes(
    package: str,
    subpath: Optional[str],
    exclude_private: bool,
    extra_excludes: Sequence[str],
) -> List[str]:
    """Assemble -x patterns, being careful with private targets.

    If focusing a private subpackage (name starts with `_`), don't exclude it.
    """
    patterns: List[str] = list(DEFAULT_EXCLUDES)
    patterns.extend(extra_excludes)

    is_private_target = bool(subpath and subpath.lstrip(".").startswith("_"))
    if exclude_private and not is_private_target:
        # Hide private top-level subpackages and any deeper private segments
        patterns.extend([f"{package}._*", f"{package}.*._*"])
    return patterns


def generate_pydeps(
    src: Annotated[
        Path,
        typer.Option(
            "--src",
            help="Root directory that contains the package (e.g., ./src).",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="Output SVG file path.",
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    package: Annotated[
        str,
        typer.Option(
            "--package",
            help="Top-level package name to analyze.",
        ),
    ] = "otaf",
    subpath: Annotated[
        Optional[str],
        typer.Option(
            "--subpath",
            help="Optional subpackage to focus on (e.g., _assembly_modeling).",
        ),
    ] = None,
    depth: Annotated[
        int,
        typer.Option(
            "--depth",
            help="Maximum module depth to display (--max-module-depth in pydeps).",
        ),
    ] = 2,
    rankdir: Annotated[
        RankDir,
        typer.Option(
            "--rankdir",
            help="Graph layout direction (TB, BT, LR, RL).",
        ),
    ] = RankDir.LR,
    exclude_private: Annotated[
        bool,
        typer.Option(
            "--exclude-private",
            help="Hide private segments (._*); auto-disabled when focusing a private subpackage.",
        ),
    ] = False,
    noise_level: Annotated[
        int,
        typer.Option(
            "--noise-level",
            help="Degree threshold for pruning nodes with high connectivity (0 disables).",
        ),
    ] = 0,
    include_missing: Annotated[
        bool,
        typer.Option(
            "--include-missing",
            help="Include modules not found on sys.path (workaround for rare cycles).",
        ),
    ] = False,
    cluster: Annotated[
        bool,
        typer.Option(
            "--cluster/--no-cluster",
            help="Draw external dependencies as clusters. Use --no-cluster to disable.",
        ),
    ] = True,
    use_only: Annotated[
        bool,
        typer.Option(
            "--only/--no-only",
            help="Pass --only to scope the graph exclusively to the package/subpackage.",
        ),
    ] = True,
    extra_exclude: Annotated[
        List[str],
        typer.Option(
            "--extra-exclude",
            help="Additional -x glob patterns to exclude (can be used multiple times).",
        ),
    ] = [],
) -> None:
    """
    Generate readable pydeps dependency graphs for Python packages.

    This command robustly wraps pydeps for large projects by focusing on
    specific subpackages, automatically hiding noisy external dependencies,
    and handling private modules gracefully.
    """
    target_dir = src / package
    if not target_dir.is_dir():
        typer.secho(
            f"Error: Package directory not found at '{target_dir}'",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    only_arg = package if not subpath else f"{package}.{subpath.lstrip('.')}"
    excludes = build_excludes(package, subpath, exclude_private, extra_exclude)

    out.parent.mkdir(parents=True, exist_ok=True)

    cmd: List[str] = [
        sys.executable,
        "-m",
        "pydeps",
        str(target_dir),
        "--noshow",
        "--rankdir",
        rankdir.value,
        "--max-bacon",
        "2",
        "--max-module-depth",
        str(depth),
        "--rmprefix",
        f"{package}.",
        "-o",
        str(out),
    ]

    if use_only:
        cmd.extend(["--only", only_arg])

    if cluster:
        cmd.extend(["--cluster", "--max-cluster-size", "1000", "--min-cluster-size", "2"])

    if excludes:
        cmd.extend(["-x", *excludes])

    if noise_level and noise_level > 0:
        cmd.extend(["--noise-level", str(noise_level)])

    if include_missing:
        cmd.append("--include-missing")

    env = os.environ.copy()
    # Safely construct the PYTHONPATH
    env["PYTHONPATH"] = os.pathsep.join(
        [str(src.resolve())] + ([env["PYTHONPATH"]] if "PYTHONPATH" in env else [])
    )

    typer.secho(f"Running: {' '.join(cmd)}", fg=typer.colors.CYAN)

    proc = subprocess.run(
        cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    if proc.returncode != 0:
        if proc.stdout:
            typer.echo(proc.stdout)
        if proc.stderr:
            typer.secho(proc.stderr, fg=typer.colors.RED, err=True)
        raise typer.Exit(code=proc.returncode)

    typer.secho("Done.", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"SVG: {out.resolve()}")
