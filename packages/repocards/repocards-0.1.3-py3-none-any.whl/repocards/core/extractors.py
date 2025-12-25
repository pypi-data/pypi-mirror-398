# src/repocards/core/extractors.py
from __future__ import annotations
import re
from typing import List, Tuple, Dict
from ..schemas import FetchedFile

# ---------- Shell harvesting (docs + CI) ----------
SHELL_FENCE_RE = re.compile(r"```(?:bash|sh|zsh|shell|console|powershell)\s+(.*?)```", re.S | re.I)
SHELL_LINE_RE  = re.compile(r"(?m)^\s*(?:\$|>)\s*(.+)$")

CMD_TOKEN_RE   = re.compile(
    r"^(?:sudo\s+)?(?:"
    r"pipx?|uv|conda|python3?|pytest|"
    r"npm|yarn|pnpm|bun|node|"
    r"cargo|rustup|"
    r"go|"
    r"cmake|ninja|make|ctest|"
    r"git|brew|apt|dnf|pacman|choco|winget|xcodebuild|msbuild|"
    r"docker|podman|compose"
    r")\b",
    re.I,
)

WORKFLOW_RUN_RE = re.compile(
    r"(?m)^\s*run:\s*(?:\|[ \t]*\n(?P<block>(?:[ \t]{2,}.+\n)+)|(?P<single>.+))"
)

def _rank_source(path: str) -> int:
    # smaller = higher priority
    if path.startswith(("README", "docs/", "Documentation/")): return 0
    if "build" in path.lower(): return 1
    if "/workflows/" in path: return 2
    if path.startswith(("examples/","demo/","scripts/","Meta/")): return 3
    if "EditorConfiguration" in path: return 6
    return 4

def _sorted(pairs: List[Tuple[str,str]]) -> List[Tuple[str,str]]:
    return sorted(pairs, key=lambda t: (_rank_source(t[1]), t[1], t[0]))

def _dedupe_pairs(pairs: List[Tuple[str,str]], limit: int) -> List[Tuple[str,str]]:
    seen, out = set(), []
    for cmd, src in pairs:
        key = cmd.strip()
        if key and key not in seen:
            out.append((key, src)); seen.add(key)
        if len(out) >= limit: break
    return out

def _strip_github_expr(s: str) -> str:
    # remove ${{ ... }} expressions from CI
    return re.sub(r"\$\{\{[^}]+\}\}", "<VAR>", s)

def _split_run_block(block: str) -> List[str]:
    # Join lines ending with backslash; return individual commands
    cmds, cur = [], ""
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.endswith("\\"):
            cur += line[:-1].rstrip() + " "
            continue
        cur += line
        cmds.append(cur.strip())
        cur = ""
    if cur.strip():
        cmds.append(cur.strip())
    return cmds

def harvest_shell_commands(files: List[FetchedFile]) -> List[Tuple[str,str]]:
    pairs: List[Tuple[str,str]] = []
    for f in files:
        txt = f.content
        # fenced blocks in docs
        for m in SHELL_FENCE_RE.finditer(txt):
            for line in _split_run_block(m.group(1)):
                s = _strip_github_expr(line).strip()
                if s and CMD_TOKEN_RE.search(s):
                    pairs.append((s, f.path))
        # $-prefixed lines in docs
        for m in SHELL_LINE_RE.finditer(txt):
            s = _strip_github_expr(m.group(1)).strip()
            if s and CMD_TOKEN_RE.search(s):
                pairs.append((s, f.path))
        # CI workflow run: steps
        if f.path.startswith(".github/workflows/"):
            for m in WORKFLOW_RUN_RE.finditer(txt):
                chunk = m.group("block") or m.group("single") or ""
                for line in _split_run_block(chunk):
                    s = _strip_github_expr(line).strip()
                    if s and CMD_TOKEN_RE.search(s):
                        pairs.append((s, f.path))
    return _dedupe_pairs(_sorted(pairs), 160)

# ---------- Categorize + OS-bucket commands ----------
BUCKETS = [
    ("install", re.compile(r"^(?:sudo\s+)?(?:apt|dnf|pacman|brew|choco|winget|pip|pip3|pipx|uv|conda|npm|yarn|pnpm|bun)\b", re.I)),
    ("setup",   re.compile(r"\b(?:submodule|venv|virtualenv|install --dev|poetry|pre-commit)\b", re.I)),
    ("build",   re.compile(r"^(?:cmake|ninja|make|ctest|go build|cargo\s+(?:build|b)|npm run build|pnpm build|yarn build|xcodebuild|msbuild)\b", re.I)),
    ("run",     re.compile(r"^(?:npm run start|pnpm start|yarn start|python(?:3)?\s|node\s|cargo run|go run|\.\/|ninja -C .+ run)", re.I)),
    ("test",    re.compile(r"(?:pytest|ctest|npm test|yarn test|pnpm test|go test|cargo test)\b", re.I)),
    ("lint",    re.compile(r"(?:flake8|ruff|black|isort|eslint|prettier|clang[- ]?format)\b", re.I)),
]

def bucket_commands(cmds: List[Tuple[str,str]]) -> Dict[str, List[Tuple[str,str]]]:
    out: Dict[str, List[Tuple[str,str]]] = {k: [] for k,_ in BUCKETS}
    for cmd, src in cmds:
        low = cmd.lower()
        placed = False
        for name, pat in BUCKETS:
            if pat.search(low):
                out[name].append((cmd, src)); placed = True; break
        if not placed and (low.startswith("./") or low.startswith("python ")):
            out["run"].append((cmd, src))
    for k in out:
        out[k] = _dedupe_pairs(_sorted(out[k]), 20)
    return out

def classify_os(cmd: str) -> str:
    c = cmd.lower()
    if any(t in c.split()[:2] for t in ("apt","dnf","pacman")): 
        return "linux"
    if c.startswith("brew") or " brew " in c or "cmake_osx" in c or "osx_deployment_target" in c:
        return "macos"
    if any(t in c for t in ("choco","winget","msbuild","powershell","cmd /c","vcvarsall.bat")): 
        return "windows"
    return "generic"

def bucket_commands_by_os(cmds: List[Tuple[str,str]]) -> Dict[str, Dict[str, List[Tuple[str,str]]]]:
    base = bucket_commands(cmds)
    out: Dict[str, Dict[str, List[Tuple[str,str]]]] = {}
    for cat, lst in base.items():
        osmap = {"linux": [], "macos": [], "windows": [], "generic": []}
        for cmd, src in lst:
            osmap[classify_os(cmd)].append((cmd, src))
        for oskey in osmap:
            osmap[oskey] = osmap[oskey][:10]
        out[cat] = osmap
    return out

# ---------- README overview, URLs, notable ----------
URL_RE = re.compile(r"https?://[^\s\]\)>\}\"\']+")
USEFUL_LINK_HINTS = ("docs","doc","guide","wiki","arxiv","paper","issues","releases","cmake","qt","readthedocs","huggingface","zenodo","figshare")

def first_readme_para(files: List[FetchedFile]) -> str | None:
    for f in files:
        if re.search(r"(^|/|\\)readme(\.|$)", f.path, re.I):
            blob = f.content.strip()
            parts = re.split(r"\n\s*\n", blob, maxsplit=1)
            para = re.sub(r"^#+\s*", "", parts[0].strip())
            para = re.sub(r"<[^>]+>", "", para).strip()
            return para[:500] if para else None
    return None

def extract_urls(files: List[FetchedFile]) -> List[Tuple[str, str]]:
    out = []
    for f in files:
        for m in URL_RE.finditer(f.content):
            u = m.group(0).rstrip(").,;:'\"*")
            out.append((u, f.path))
    seen, ded = set(), []
    for u, src in out:
        if u not in seen:
            if any(h in u.lower() for h in USEFUL_LINK_HINTS):
                ded.append((u, src))
            seen.add(u)
    return _sorted(ded)[:14]

def notable_paths(files: List[FetchedFile]) -> List[str]:
    cands = [f.path for f in files if f.path.count("/") <= 2]
    keep = [p for p in cands if p.startswith(("README","docs/","Documentation/","examples/","scripts/","Meta/",".github/workflows/"))]
    seen, out = set(), []
    for p in keep:
        if p not in seen: out.append(p); seen.add(p)
    return out[:16]

# ---------- Small Python API fences ----------
FENCED_PY_RE = re.compile(r"```python(.*?)```", re.S | re.I)

def extract_api_snippets(files: List[FetchedFile]) -> List[Tuple[str, str]]:
    out = []
    for f in files:
        for m in FENCED_PY_RE.finditer(f.content):
            block = m.group(1).strip()
            if not block: continue
            lines = block.splitlines()
            if len(lines) > 40:
                block = "\n".join(lines[:40]) + "\n# …"
            out.append((block, f.path))
            if len(out) >= 2:
                return out
    return out

# ---------- Inputs / Outputs sections ----------
HEAD_INPUTS  = re.compile(r"(?im)^#{1,6}\s*inputs?\b")
HEAD_OUTPUTS = re.compile(r"(?im)^#{1,6}\s*outputs?\b")

def extract_section_text(files: List[FetchedFile], head_re: re.Pattern, max_lines: int = 12) -> List[Tuple[str, str]]:
    out: List[Tuple[str,str]] = []
    for f in files:
        txt = f.content
        for m in head_re.finditer(txt):
            start = m.end()
            rest = txt[start:]
            stop = re.search(r"(?m)^\s*#{1,6}\s+\S", rest)
            chunk = rest[: stop.start() if stop else len(rest)]
            lines = [ln.rstrip() for ln in chunk.strip().splitlines() if ln.strip()]
            if lines:
                out.append(("\n".join(lines[:max_lines]).strip(), f.path))
    seen, ded = set(), []
    for block, src in out:
        key = (block, src)
        if key not in seen:
            ded.append((block, src)); seen.add(key)
    return ded[:2]
