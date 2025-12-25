# src/repocards/core/fetcher.py
from __future__ import annotations

import base64
import fnmatch
import os
from typing import Dict, Iterable, List, Literal, Optional, Tuple
from urllib.parse import quote, urlparse

import requests

from ..schemas import FetchedFile, RepoSnapshot

GITHUB_API = "https://api.github.com"

Platform = Literal["github", "gitlab"]

# ------------------------- File selection policy -------------------------

# Keep the include list strongly biased toward human-written, texty content.
INCLUDE_GLOBS = [
    "README*",
    "readme*",
    "docs/**/*.md",
    "doc/**/*.md",
    "documentation/**/*.md",
    ".github/workflows/**/*.yml",
    ".github/workflows/**/*.yaml",
    ".gitlab-ci.yml",
    ".gitlab/**/*.yml",
    ".gitlab/**/*.yaml",  # GitLab CI
    "examples/**/*.md",
    "examples/**/*.py",
    "examples/**/*.sh",
    "demo/**/*.md",
    "demo/**/*.py",
    "demo/**/*.sh",
    "scripts/**/*.py",
    "scripts/**/*.sh",
    "scripts/**/CMakeLists.txt",
    "scripts/**/Makefile",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "requirements*.txt",
    "environment*.yml",
    "Pipfile",
    "Pipfile.lock",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "CMakeLists.txt",
    "**/*.cmake",
    "Makefile",
    "makefile",
    # NEW: docker files
    "Dockerfile",
    "docker/**/Dockerfile*",
    "docker/**/*.yml",
    "docker/**/*.yaml",
    "docker/**/*.sh",
]

# Exclude obvious binaries and bulky folders. Do NOT exclude .github (for workflows).
EXCLUDE_GLOBS = [
    ".git/**",
    "**/.git/**",
    "**/.venv/**",
    "venv/**",
    "env/**",
    "data/**",
    "datasets/**",
    "docs/_build/**",
    "**/.ipynb_checkpoints/**",
    # Common binary / large formats
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.gif",
    "**/*.webp",
    "**/*.bmp",
    "**/*.tif",
    "**/*.tiff",
    "**/*.ico",
    "**/*.pdf",
    "**/*.svgz",
    "**/*.zip",
    "**/*.tar",
    "**/*.tar.*",
    "**/*.7z",
    "**/*.rar",
    "**/*.dmg",
    "**/*.exe",
    "**/*.dll",
    "**/*.so",
    "**/*.dylib",
    "**/*.a",
    "**/*.bin",
    "**/*.wasm",
    "**/*.class",
    "**/*.jar",
    "**/*.pt",
    "**/*.pth",
    "**/*.onnx",
    "**/*.h5",
    "**/*.ckpt",
    "**/*.parquet",
    "**/*.feather",
]

# Extensions we consider text-like if encountered elsewhere in the tree.
TEXTY_EXTS = {
    ".md",
    ".rst",
    ".txt",
    ".toml",
    ".cfg",
    ".ini",
    ".yml",
    ".yaml",
    ".json",
    ".py",
    ".sh",
    ".ps1",
    ".bat",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".cxx",
    ".cmake",
    ".go",
    ".rs",
    ".java",
    ".gradle",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".vue",
    ".mk",  # Make fragments
}

# ------------------------------ Helpers ------------------------------
def _detect_platform(url: str) -> Platform:
    """Detect if URL is GitHub or GitLab."""
    u = urlparse(url)
    netloc = u.netloc.lower()
    if netloc in {"github.com", "www.github.com"}:
        return "github"
    # Strip any port information (e.g., "gitlab.company.com:8443")
    hostname = netloc.split(":", 1)[0]
    # Known GitLab SaaS domains
    if hostname in {"gitlab.com", "www.gitlab.com"}:
        return "gitlab"
    if hostname.endswith(".gitlab.com") or hostname.endswith(".gitlab.io"):
        return "gitlab"
    # Self-managed GitLab instances where "gitlab" is a full DNS label or
    # appears as a prefix in a label (e.g. "gitlab" or "gitlab-xyz" subdomains)
    labels = hostname.split(".")
    if any(label == "gitlab" or label.startswith("gitlab-") for label in labels):
        return "gitlab"
    else:
        raise ValueError(
            f"Unsupported platform: {netloc}. Only GitHub and GitLab URLs are supported."
        )

def _auth_headers_github(token: Optional[str]) -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def _auth_headers_gitlab(token: Optional[str]) -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if token:
        h["PRIVATE-TOKEN"] = token
    return h

def _parse_repo_url(url: str) -> Tuple[Platform, str, str, str, Optional[str]]:
    """
    Parse GitHub or GitLab repository URL.

    Supports:
    - GitHub: https://github.com/owner/repo[.git][/tree/<ref>|#<ref>]
    - GitLab: https://gitlab.com/group/.../subgroup/project[.git][/-/tree/<ref>|#<ref>]
      Note: GitLab supports deeply nested groups at any depth.

    Returns (platform, api_base, owner, repo, ref|None).
    For GitLab, 'owner' is the first path component and 'repo' is the full project path
    (which may contain slashes for nested groups, e.g., "group/subgroup/project").
    """
    u = urlparse(url)
    platform = _detect_platform(url)

    parts = [p for p in u.path.strip("/").split("/") if p]
    # Validate path components per platform:
    # - GitHub: require at least "owner/repo"
    # - GitLab: allow single-component projects like "https://gitlab.com/project"
    if platform == "github" and len(parts) < 2:
        raise ValueError(f"Invalid repository URL: {url}")
    if platform == "gitlab" and len(parts) < 1:
        raise ValueError(f"Invalid repository URL: {url}")

    ref = None

    if platform == "github":
        api_base = GITHUB_API
        owner, repo = parts[0], parts[1].removesuffix(".git")
        # GitHub uses /tree/<ref>
        if len(parts) >= 4 and parts[2] == "tree":
            ref = "/".join(parts[3:])
    else:  # gitlab
        # GitLab API base: https://gitlab.instance.com/api/v4
        api_base = f"{u.scheme}://{u.netloc}/api/v4"
        # GitLab supports nested groups: group/subgroup/project
        # Find where the project path ends by looking for the /-/ marker
        project_end_idx = len(parts)
        
        # Look for /-/ marker (appears as standalone "-" followed by a GitLab route)
        # GitLab uses /-/ prefix for special routes. Common routes include:
        # tree, blob, commits, tags, branches, merge_requests, issues, wikis,
        # snippets, releases, pipelines, graphs, settings, edit, raw, blame
        gitlab_routes = (
            "tree", "blob", "commits", "tags", "branches",
            "merge_requests", "issues", "wikis", "snippets", "releases",
            "pipelines", "graphs", "settings", "edit", "raw", "blame"
        )
        for i, part in enumerate(parts):
            if part == "-" and i + 1 < len(parts) and parts[i + 1] in gitlab_routes:
                project_end_idx = i
                break
        
        # Extract the full project path (all components before markers)
        project_parts = parts[:project_end_idx]
        
        # Remove .git suffix from the last component if present
        if project_parts and project_parts[-1].endswith(".git"):
            project_parts[-1] = project_parts[-1].removesuffix(".git")
        
        # Ensure we have at least one path component for the GitLab project
        if not project_parts:
            raise ValueError(f"Invalid GitLab repository URL (missing project path): {url}")
        
        # For GitLab: owner is the first component, repo is the full project path
        # This allows proper display while maintaining the full path for API calls
        owner = project_parts[0]
        repo = "/".join(project_parts)
        
        # GitLab uses /-/tree/<ref>
        if len(parts) >= project_end_idx + 2 and parts[project_end_idx] == "-" and parts[project_end_idx + 1] == "tree":
            ref = "/".join(parts[project_end_idx + 2:])

    # #<ref> fragment (works for both)
    if u.fragment:
        ref = u.fragment

    return platform, api_base, owner, repo, ref

def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)

def _looks_texty(path: str) -> bool:
    p = path.lower()
    if p.endswith("cmakelists.txt"):
        return True
    dot = p.rfind(".")
    if dot == -1:
        return False
    return p[dot:] in TEXTY_EXTS

def _rank_candidate(path: str) -> int:
    p = path.lower()
    # highest priority: readme, manifests, workflows
    if p.startswith("readme"):
        return 0
    if p in (
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "requirements.txt",
        "requirements-dev.txt",
        "package.json",
        "cargo.toml",
        "go.mod",
        "cmakelists.txt",
        "makefile",
    ):
        return 0
    if (
        p.startswith(".github/workflows/")
        or p.startswith(".gitlab-ci")
        or p.startswith(".gitlab/")
    ):
        return 0
    # docs next
    if p.startswith(("docs/", "documentation/", "doc/")):
        return 1
    # examples/scripts/build-related
    if "build" in p or p.startswith(("examples/", "scripts/", "meta/", "docker/")):
        return 2
    return 3

# ------------------------------- Fetcher -------------------------------
def fetch_repo_snapshot_via_api(
    repo_url: str,
    token: Optional[str] = None,
    max_files: int = 160,
    max_bytes_per_file: int = 300_000,
) -> RepoSnapshot:
    """
    Fetch a curated subset of files via GitHub or GitLab REST API (no git clone).
    Also fetches repo metadata: description, license, topics, and languages.

    The selection aims to surface human-written docs, manifests, CI workflows,
    and scripts that are most useful for building/running a project.

    Supports both GitHub and GitLab (including self-hosted instances).
    """
    platform, api_base, owner, name, ref = _parse_repo_url(repo_url)

    if platform == "github":
        return _fetch_github_snapshot(
            repo_url, api_base, owner, name, ref, token, max_files, max_bytes_per_file
        )
    else:  # gitlab
        return _fetch_gitlab_snapshot(
            repo_url, api_base, owner, name, ref, token, max_files, max_bytes_per_file
        )

def _fetch_github_snapshot(
    repo_url: str,
    api_base: str,
    owner: str,
    name: str,
    ref: Optional[str],
    token: Optional[str],
    max_files: int,
    max_bytes_per_file: int,
) -> RepoSnapshot:
    """Fetch repository snapshot from GitHub API."""
    session = requests.Session()
    session.headers.update(_auth_headers_github(token or os.getenv("GITHUB_TOKEN")))

    # --- Repo meta
    r = session.get(f"{api_base}/repos/{owner}/{name}")
    r.raise_for_status()
    repo = r.json()
    default_branch = repo.get("default_branch", "main")
    description = repo.get("description")
    license_spdx = (repo.get("license") or {}).get("spdx_id") or None

    # Topics
    topics: List[str] = []
    rt = session.get(f"{api_base}/repos/{owner}/{name}/topics")
    if rt.ok:
        topics = (rt.json().get("names") or [])[:10]

    # Languages
    languages: Dict[str, int] = {}
    rl = session.get(f"{api_base}/repos/{owner}/{name}/languages")
    if rl.ok and isinstance(rl.json(), dict):
        languages = rl.json()

    # Resolve ref
    if not ref:
        ref = default_branch

    # --- List tree (handles branch name or SHA)
    r = session.get(
        f"{api_base}/repos/{owner}/{name}/git/trees/{ref}", params={"recursive": "1"}
    )
    if r.status_code == 422:  # ref may be a branch name; resolve to SHA
        rb = session.get(f"{api_base}/repos/{owner}/{name}/branches/{ref}")
        rb.raise_for_status()
        sha = rb.json()["commit"]["sha"]
        r = session.get(
            f"{api_base}/repos/{owner}/{name}/git/trees/{sha}",
            params={"recursive": "1"},
        )
    r.raise_for_status()
    tree = r.json().get("tree", [])

    # --- Choose candidate paths
    candidate_paths: List[str] = []
    for node in tree:
        if node.get("type") != "blob":
            continue
        path = node["path"]
        # basic filters
        if _matches_any(path, EXCLUDE_GLOBS):
            continue
        if _matches_any(path, INCLUDE_GLOBS) or _looks_texty(path):
            candidate_paths.append(path)

    candidate_paths = sorted(candidate_paths, key=_rank_candidate)

    truncated = False
    if len(candidate_paths) > max_files:
        candidate_paths = candidate_paths[:max_files]
        truncated = True

    # --- Fetch file contents (text only, size-capped)
    files: List[FetchedFile] = []
    for path in candidate_paths:
        rr = session.get(
            f"{api_base}/repos/{owner}/{name}/contents/{path}", params={"ref": ref}
        )
        if rr.status_code == 404:
            continue
        rr.raise_for_status()
        meta = rr.json()
        if isinstance(meta, list):
            continue  # directory
        size = int(meta.get("size") or 0)
        if size > max_bytes_per_file:
            truncated = True
            continue
        enc = meta.get("encoding")
        content_b64 = meta.get("content") or ""
        text = ""
        if enc == "base64":
            try:
                text = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            except Exception:
                # skip undecodable blobs
                continue
        else:
            text = content_b64
        files.append(FetchedFile(path=path, content=text))

    return RepoSnapshot(
        owner=owner,
        name=name,
        ref=ref,
        description=description,
        license_spdx=license_spdx,
        topics=topics,
        files=files,
        truncated=truncated,
        languages=languages,
    )

def _fetch_gitlab_snapshot(
    repo_url: str,
    api_base: str,
    owner: str,
    name: str,
    ref: Optional[str],
    token: Optional[str],
    max_files: int,
    max_bytes_per_file: int,
) -> RepoSnapshot:
    """Fetch repository snapshot from GitLab API."""
    session = requests.Session()
    session.headers.update(_auth_headers_gitlab(token or os.getenv("GITLAB_TOKEN")))

    # GitLab uses URL-encoded project ID. For nested groups, 'name' contains
    # the full project path (e.g., "group/subgroup/project")
    project_id = quote(name, safe="")

    # --- Repo meta
    r = session.get(f"{api_base}/projects/{project_id}")
    r.raise_for_status()
    repo = r.json()
    default_branch = repo.get("default_branch", "main")
    description = repo.get("description")

    # GitLab license info (may be in different format)
    license_info = repo.get("license")
    license_spdx = None
    if license_info:
        if isinstance(license_info, dict):
            license_spdx = license_info.get("key") or license_info.get("name")
        else:
            license_spdx = license_info

    # Topics (tags in GitLab)
    topics_raw = repo.get("topics") or []
    topics: List[str] = topics_raw[:10] if topics_raw else (repo.get("tag_list") or [])[:10]

    # Languages - GitLab provides this directly in project API
    languages: Dict[str, int] = {}
    rl = session.get(f"{api_base}/projects/{project_id}/languages")
    if rl.ok and isinstance(rl.json(), dict):
        # GitLab returns percentages; convert to byte-like counts for consistency
        # Prefer using repository size when available, otherwise fall back to a
        # normalized small integer total to preserve relative proportions.
        lang_percents = rl.json()
        total = sum(lang_percents.values())
        if total > 0:
            repo_stats = repo.get("statistics") or {}
            repo_size = int(repo_stats.get("repository_size") or 0)
            if repo_size > 0:
                # Distribute repository size according to language percentages
                languages = {
                    lang: int(repo_size * (pct / total))
                    for lang, pct in lang_percents.items()
                }
            else:
                # Fallback: scale normalized percentages to a small integer total
                scale_total = 1000
                languages = {
                    lang: int(scale_total * (pct / total))
                    for lang, pct in lang_percents.items()
                }

    # Resolve ref
    if not ref:
        ref = default_branch

    # --- List repository tree
    r = session.get(
        f"{api_base}/projects/{project_id}/repository/tree",
        params={"ref": ref, "recursive": "true", "per_page": 100},
    )
    r.raise_for_status()

    # GitLab may paginate results
    tree = r.json()
    # Handle pagination if needed (simplified - gets first page)
    while "next" in r.links and len(tree) < max_files * 2:
        r = session.get(r.links["next"]["url"])
        r.raise_for_status()
        tree.extend(r.json())

    # --- Choose candidate paths
    candidate_paths: List[str] = []
    for node in tree:
        if node.get("type") != "blob":
            continue
        path = node["path"]
        # basic filters
        if _matches_any(path, EXCLUDE_GLOBS):
            continue
        if _matches_any(path, INCLUDE_GLOBS) or _looks_texty(path):
            candidate_paths.append(path)

    candidate_paths = sorted(candidate_paths, key=_rank_candidate)

    truncated = False
    if len(candidate_paths) > max_files:
        candidate_paths = candidate_paths[:max_files]
        truncated = True

    # --- Fetch file contents (text only, size-capped)
    files: List[FetchedFile] = []
    for path in candidate_paths:
        # GitLab file API
        rr = session.get(
            f"{api_base}/projects/{project_id}/repository/files/{quote(path, safe='')}",
            params={"ref": ref},
        )
        if rr.status_code == 404:
            continue
        rr.raise_for_status()
        meta = rr.json()

        size = int(meta.get("size") or 0)
        if size > max_bytes_per_file:
            truncated = True
            continue

        # GitLab returns content as base64 encoded
        content_b64 = meta.get("content") or ""
        text = ""
        try:
            text = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception:
            # skip undecodable blobs
            continue

        files.append(FetchedFile(path=path, content=text))

    return RepoSnapshot(
        owner=owner,
        name=name,
        ref=ref,
        description=description,
        license_spdx=license_spdx,
        topics=topics,
        files=files,
        truncated=truncated,
        languages=languages,
    )