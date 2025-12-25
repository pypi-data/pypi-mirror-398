# src/repocards/core/summarizer.py
from __future__ import annotations
from typing import List, Dict, Any
from ..schemas import RepoSnapshot
from .extractors import bucket_commands_by_os
from .detectors import synthesize_quickstart

def _langs_str(repo: RepoSnapshot) -> str:
    languages = repo.languages or {}
    return ", ".join(sorted(languages, key=languages.get, reverse=True)[:3]) if languages else "n/a"

def build_markdown(
    repo: RepoSnapshot,
    repo_url: str,
    generic: Dict[str, List[tuple]],
    extras: Dict[str, Any] | None = None,
) -> str:
    api, urls, notable, overview = (
        generic.get("api", []), generic["urls"], generic["notable"], generic["overview"]
    )
    lines = []
    meta_bits = [f"[Repo]({repo_url})", f"Ref: `{repo.ref}`"]
    if repo.license_spdx: meta_bits.append(f"License: {repo.license_spdx}")
    if repo.topics: meta_bits.append("Topics: " + ", ".join(repo.topics))
    lines += [f"## {repo.owner}/{repo.name}", " • ".join(meta_bits), ""]
    if repo.description: lines += [repo.description.strip(), ""]
    if overview: lines += ["### Overview (README)", overview, ""]

    # Quick facts
    eco_names = ", ".join(extras.get("ecosystems", [])) if extras and extras.get("ecosystems") else "unknown"
    lines += ["### Quick facts",
              f"- **Languages:** {_langs_str(repo)}",
              f"- **Ecosystems detected:** {eco_names}",
              f"- **License:** {repo.license_spdx or 'n/a'}",
              f"- **Topics:** {', '.join(repo.topics) if repo.topics else 'n/a'}",
              ""]

    # Capability facts
    if extras and "capabilities" in extras:
        cap = extras["capabilities"]
        lines += ["### Capability facts"]
        if cap.get("package_names"): lines += [f"- package names: {', '.join(cap['package_names'])}"]
        if cap.get("entrypoints"):   lines += ["- entrypoints:"] + [f"  - `{e}`" for e in cap["entrypoints"][:10]]
        if cap.get("os_support"):    lines += [f"- OS support (inferred): {', '.join(cap['os_support'])}"]
        lines += [f"- provides CLI: {bool(cap.get('provides_cli'))}",
                  f"- provides API: {bool(cap.get('provides_api'))}",
                  f"- dockerfile present: {bool(cap.get('dockerfile_present'))}"]
        if cap.get("model_weight_links"):
            lines += ["- model weights:"] + [f"  - {u}" for u in cap["model_weight_links"][:8]]
        if cap.get("dataset_links"):
            lines += ["- datasets:"] + [f"  - {u}" for u in cap["dataset_links"][:8]]
        lines += [""]

    # Canonical quickstart
    if extras and "capabilities" in extras and extras["capabilities"].get("buckets_by_os"):
        qs = synthesize_quickstart(extras["capabilities"]["buckets_by_os"])
        if any(qs[oskey] for oskey in qs):
            lines += ["### Canonical quickstart (auto-picked)"]
            for oskey in ("linux","macos","windows","generic"):
                steps = qs.get(oskey, [])
                if not steps: continue
                lines += [f"- **{oskey}**"]
                for step in steps:
                    lines += [f"  - `{step['cmd']}`  — _{step['source']}_"]
            lines += [""]

    # Imaging signals (only if score is decent)
    if extras and extras.get("imaging") and extras["imaging"].get("imaging_score", 0) >= 0.35:
        im = extras["imaging"]
        lines += ["### Imaging signals",
                  f"- imaging_score: **{im['imaging_score']:.2f}**"]
        if im.get("tasks"):      lines += [f"- tasks: {', '.join(im['tasks'])}"]
        if im.get("modalities"): lines += [f"- modalities: {', '.join(im['modalities'])}"]
        if im.get("file_types"): lines += [f"- file types: {', '.join(im['file_types'])}"]
        if im.get("python_libs"):lines += [f"- python libs: {', '.join(im['python_libs'])}"]
        lines += [""]

    # Python API snippets (if any)
    if api:
        lines += ["### Quickstart — Python"]
        for code, src in api:
            lines += ["```python", code, "```", f"_— {src}_", ""]
        if lines and lines[-1] == "": lines.pop()

    # Helpful links
    if urls:
        lines += ["", "### Helpful Links"] + [f"- {u}  — _{src}_" for u,src in urls]

    if notable:
        lines += ["", "### Notable files/dirs"] + [f"- `{p}`" for p in notable]

    if repo.truncated:
        lines += ["", "_Note: summary may be incomplete due to fetch limits._"]

    return "\n".join([ln for ln in lines if ln != ""]).rstrip() + "\n"
