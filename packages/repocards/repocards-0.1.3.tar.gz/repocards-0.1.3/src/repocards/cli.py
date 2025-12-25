# src/repocards/cli.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from dotenv import load_dotenv

from . import __version__
from .analyzers.imaging import analyze_imaging
from .core.detectors import (
    compute_capabilities,
    detect_ecosystems,
    synthesize_quickstart,
)
from .core.extractors import (
    HEAD_INPUTS,
    HEAD_OUTPUTS,
    extract_api_snippets,
    extract_section_text,
    extract_urls,
    first_readme_para,
    harvest_shell_commands,
    notable_paths,
)
from .core.fetcher import fetch_repo_snapshot_via_api
from .core.summarizer import build_markdown
from .schemas import RepoCard

app = typer.Typer(
    add_completion=False,
    help="Generate subject-aware, evidence-based RepoCards from GitHub and GitLab repositories.",
)

load_dotenv()

# ----------------------------- helpers -----------------------------
def _prepare_out(path_str: str) -> Path:
    """Resolve a path and create parent directories if needed."""
    p = Path(path_str).expanduser()
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _resolve_outputs(
    out_dir: Optional[str],
    out_md: Optional[str],
    out_json: Optional[str],
    out_stem: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    """
    Precedence:
      1) If user provided explicit --out-md / --out-json, use those as-is.
      2) Else if --out-dir is provided, write <out_dir>/<stem>.md|.json
      3) Else if only --out-stem is provided, write ./<stem>.md|.json
      4) Else return (None, None) to print Markdown to stdout.
    """
    # 1) explicit paths win
    if out_md or out_json:
        return out_md, out_json

    stem = (out_stem or "card").strip()

    # 2) out-dir given → put both files there
    if out_dir:
        d = Path(out_dir).expanduser()
        d.mkdir(parents=True, exist_ok=True)
        return str(d / f"{stem}.md"), str(d / f"{stem}.json")

    # 3) only stem → write in cwd
    if out_stem:
        cwd = Path.cwd()
        return str(cwd / f"{stem}.md"), str(cwd / f"{stem}.json")

    # 4) default: print to stdout
    return None, None

# ----------------------------- commands -----------------------------
@app.command("summarize")
def summarize(
    repo: str = typer.Argument(
        ...,
        help="GitHub or GitLab URL like https://github.com/owner/repo or https://gitlab.com/owner/project[#ref]",
    ),
    out_dir: Optional[str] = typer.Option(
        None, "--out-dir", help="Directory to write outputs to."
    ),
    out_md: Optional[str] = typer.Option(
        None, "--out-md", help="Write Markdown to this exact path."
    ),
    out_json: Optional[str] = typer.Option(
        None, "--out-json", help="Write JSON to this exact path."
    ),
    out_stem: Optional[str] = typer.Option(
        None,
        "--out-stem",
        help="Base filename (without extension) for outputs (e.g., 'lungs' → lungs.md & lungs.json).",
    ),
    max_files: int = typer.Option(160, help="Max files to fetch from the repo."),
):
    """
    Fetch the repo, harvest commands & facts (docs + CI), detect ecosystems,
    compute capability facts, optional imaging signals, and emit a RepoCard.
    """
    # --- Fetch curated snapshot
    snap = fetch_repo_snapshot_via_api(repo, max_files=max_files)

    # --- Extract evidence
    harvested = harvest_shell_commands(snap.files)
    urls = extract_urls(snap.files)

    generic = {
        "overview": first_readme_para(snap.files),
        "cli": harvested,  # all harvested shell commands (docs + CI)
        "api": extract_api_snippets(snap.files),
        "inputs": extract_section_text(snap.files, HEAD_INPUTS),
        "outputs": extract_section_text(snap.files, HEAD_OUTPUTS),
        "urls": urls,
        "notable": notable_paths(snap.files),
    }

    # --- Capabilities & ecosystems
    capabilities = compute_capabilities(snap.files, harvested, urls, generic["api"])
    ecosystems = detect_ecosystems(snap.files)

    if not ecosystems:
        if any(
            cmd.lower().startswith(("pip ", "pip3 ", "pipx ", "uv "))
            for cmd, _ in harvested
        ):
            ecosystems = ["python"]

    quickstart = synthesize_quickstart(capabilities["buckets_by_os"])

    # --- Optional imaging analyzer (generic, gated)
    imaging = analyze_imaging(snap.files)

    extras: Dict[str, Any] = {
        "ecosystems": ecosystems,
        "capabilities": capabilities,
        "quickstart": quickstart,
        "imaging": imaging,
    }

    # --- Build Markdown
    md = build_markdown(snap, repo, generic, extras=extras)

    # --- Assemble JSON card
    card = RepoCard(
        repo_url=repo,
        ref=snap.ref,
        title=f"{snap.owner}/{snap.name}",
        meta={
            "license": snap.license_spdx,
            "topics": snap.topics,
            "languages": snap.languages,
        },
        markdown=md,
        extras=extras,
    )

    # --- Resolve output destinations
    out_md, out_json = _resolve_outputs(out_dir, out_md, out_json, out_stem)

    # --- Write outputs
    if out_md:
        _prepare_out(out_md).write_text(card.markdown, encoding="utf-8")
        typer.echo(f"Wrote Markdown → {out_md}")
    else:
        # If no path provided, print to stdout
        typer.echo(card.markdown)

    if out_json:
        _prepare_out(out_json).write_text(
            json.dumps(card.model_dump(), indent=2), encoding="utf-8"
        )
        typer.echo(f"Wrote JSON → {out_json}")

@app.command("version")
def version() -> None:
    """Show repocards version."""
    typer.echo(__version__)