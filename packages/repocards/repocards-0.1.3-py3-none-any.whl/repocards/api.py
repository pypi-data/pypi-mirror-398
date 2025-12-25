# src/repocards/api.py
"""
Public API for programmatic access to repocards functionality.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union

from dotenv import load_dotenv

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
from .core.fetcher import _detect_platform, fetch_repo_snapshot_via_api
from .core.summarizer import build_markdown
from .schemas import RepoCard

# Load environment variables from .env file
load_dotenv()


def get_repo_info(
    repo: str,
    mode: Literal[
        "markdown", "json", "pydantic", "markdown_file", "json_file"
    ] = "markdown",
    max_files: int = 160,
    out_dir: Optional[str] = None,
    github_token: Optional[str] = None,
    gitlab_token: Optional[str] = None,
) -> Union[str, RepoCard]:
    """
    Generate a RepoCard for a GitHub or GitLab repository.

    Args:
        repo: GitHub or GitLab URL like https://github.com/owner/repo or https://gitlab.com/owner/project[#ref]
        mode: Output mode:
            - "markdown": returns markdown string
            - "json": returns JSON string
            - "pydantic": returns RepoCard object
            - "markdown_file": writes markdown file and returns the path as string
            - "json_file": writes JSON file and returns the path as string
        max_files: Maximum number of files to fetch from the repository (default: 160)
        out_dir: Directory to write files (required for markdown_file/json_file modes)
        github_token: GitHub personal access token for authentication (optional).
                     Automatically loaded from GITHUB_TOKEN environment variable or .env file.
                     Only pass this directly if you need to override the environment variable.
        gitlab_token: GitLab personal access token for authentication (optional).
                     Automatically loaded from GITLAB_TOKEN environment variable or .env file.
                     Only pass this directly if you need to override the environment variable.

    Returns:
        Depending on mode:
        - str: markdown content, JSON string, or file path
        - RepoCard: pydantic object

    Raises:
        ValueError: If mode is invalid or out_dir is missing for file modes
        requests.exceptions.HTTPError: If GitHub/GitLab API request fails (rate limit, auth, etc.)

    Examples:
        >>> import repocards
        >>> # Get markdown string (token auto-loaded from .env)
        >>> md = repocards.get_repo_info("https://github.com/user/repo")
        >>>
        >>> # Get JSON string
        >>> json_str = repocards.get_repo_info("https://github.com/user/repo", mode="json")
        >>>
        >>> # Get pydantic object
        >>> card = repocards.get_repo_info("https://github.com/user/repo", mode="pydantic")
        >>> print(card.title)
        >>>
        >>> # GitLab repository
        >>> card = repocards.get_repo_info("https://gitlab.com/user/project", mode="pydantic")
        >>>
        >>> # With explicit token (GitHub)
        >>> md = repocards.get_repo_info(
        ...     "https://github.com/user/private-repo",
        ...     github_token="ghp_..."
        ... )
        >>>
        >>> # With explicit token (GitLab)
        >>> md = repocards.get_repo_info(
        ...     "https://gitlab.com/user/private-project",
        ...     gitlab_token="glpat-..."
        ... )
        >>>
        >>> # Write to file
        >>> path = repocards.get_repo_info(
        ...     "https://github.com/user/repo",
        ...     mode="markdown_file",
        ...     out_dir="./output"
        ... )
    """
    # Validate mode
    valid_modes = {"markdown", "json", "pydantic", "markdown_file", "json_file"}
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid mode '{mode}'. Must be one of: {', '.join(sorted(valid_modes))}"
        )

    # Validate out_dir for file modes
    if mode in {"markdown_file", "json_file"} and not out_dir:
        raise ValueError(f"out_dir is required when mode is '{mode}'")

    # --- Fetch curated snapshot
    # Detect platform and use appropriate token
    platform = _detect_platform(repo)
    token = github_token if platform == "github" else gitlab_token

    try:
        snap = fetch_repo_snapshot_via_api(repo, token=token, max_files=max_files)
    except Exception as e:
        # Enhance error message for rate limiting
        error_msg = str(e)
        if "rate limit exceeded" in error_msg.lower():
            if platform == "github":
                raise type(e)(
                    f"{error_msg}\n\n"
                    "GitHub API rate limit exceeded. To fix this:\n"
                    "1. Set GITHUB_TOKEN environment variable: export GITHUB_TOKEN='ghp_...'\n"
                    "2. Or pass github_token parameter: get_repo_info(..., github_token='ghp_...')\n"
                    "3. Get a token at: https://github.com/settings/tokens (needs 'repo' scope)\n"
                    "\n"
                    "Rate limits:\n"
                    "  - Without token: 60 requests/hour\n"
                    "  - With token: 5,000 requests/hour"
                ) from e
            else:  # gitlab
                raise type(e)(
                    f"{error_msg}\n\n"
                    "GitLab API rate limit exceeded. To fix this:\n"
                    "1. Set GITLAB_TOKEN environment variable: export GITLAB_TOKEN='glpat-...'\n"
                    "2. Or pass gitlab_token parameter: get_repo_info(..., gitlab_token='glpat-...')\n"
                    "3. Get a token at: https://gitlab.com/-/profile/personal_access_tokens\n"
                    "   (for self-hosted: https://your-gitlab.com/-/profile/personal_access_tokens)\n"
                ) from e
        raise  # --- Extract evidence
    harvested = harvest_shell_commands(snap.files)
    urls = extract_urls(snap.files)

    generic = {
        "overview": first_readme_para(snap.files),
        "cli": harvested,
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

    # --- Optional imaging analyzer
    imaging = analyze_imaging(snap.files)

    extras: Dict[str, Any] = {
        "ecosystems": ecosystems,
        "capabilities": capabilities,
        "quickstart": quickstart,
        "imaging": imaging,
    }

    # --- Build Markdown
    md = build_markdown(snap, repo, generic, extras=extras)

    # --- Assemble RepoCard
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

    # --- Return based on mode
    if mode == "markdown":
        return card.markdown

    elif mode == "json":
        return json.dumps(card.model_dump(), indent=2)

    elif mode == "pydantic":
        return card

    elif mode == "markdown_file":
        # Create output directory and write markdown file
        out_path = Path(out_dir).expanduser()
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{snap.owner}_{snap.name}.md"
        file_path.write_text(card.markdown, encoding="utf-8")
        return str(file_path)

    elif mode == "json_file":
        # Create output directory and write JSON file
        out_path = Path(out_dir).expanduser()
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{snap.owner}_{snap.name}.json"
        file_path.write_text(json.dumps(card.model_dump(), indent=2), encoding="utf-8")
        return str(file_path)

    # Should never reach here due to validation
    raise ValueError(f"Unexpected mode: {mode}")
