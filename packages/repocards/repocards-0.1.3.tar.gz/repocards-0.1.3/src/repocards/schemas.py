# src/repocards/schemas.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FetchedFile(BaseModel):
    """A single fetched text file from the repository (decoded UTF-8)."""
    path: str
    content: str


class RepoSnapshot(BaseModel):
    """
    A lightweight view of a GitHub repository, suitable for summarization.
    Only a curated subset of files is fetched to stay fast and avoid binaries.
    """
    owner: str
    name: str
    ref: str
    description: Optional[str] = None
    license_spdx: Optional[str] = None
    topics: List[str] = []
    files: List[FetchedFile] = []
    truncated: bool = False
    # Language byte counts from the GitHub Languages API
    languages: Dict[str, int] = {}


class RepoCard(BaseModel):
    """Final assembled card for human + machine consumption."""
    repo_url: str
    ref: str
    title: str
    meta: Dict[str, Any]
    markdown: str
    # Extra machine-usable facts (capabilities, quickstart, enrichments…)
    extras: Dict[str, Any] = {}
